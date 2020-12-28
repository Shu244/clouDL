import json
import os

from clouDL_utils import gcp_interactions as gcp
from clouDL_utils.progress import Progress
from clouDL.analyze import Best_Model
from clouDL_utils import strings


class Archive:
    def __init__(self, bucket_name, top_n):
        self.bucket_name = bucket_name
        self.top_n = top_n

    def clear_for_new_hyparams(self):
        gcp.delete_all_prefixes(self.bucket_name, strings.vm_progress)
        gcp.delete_all_prefixes(self.bucket_name, strings.best_model)
        gcp.delete_all_prefixes(self.bucket_name, strings.results)
        gcp.delete_all_prefixes(self.bucket_name, strings.shared_errors)

    def archive_results(self):
        folder_names = gcp.get_folder_names(self.bucket_name, strings.results)
        for folder_name in folder_names:
            src = os.path.join(strings.results, folder_name)
            dest = os.path.join(strings.archive, strings.results)
            gcp.move_cloud_folder(self.bucket_name, src, dest)

    def archive_best_model(self, top_n):
        if top_n == 0:
            return None

        # There is a best progress for each VM, this gets them all in a list
        best_progress_list = Best_Model.best_progress_list(self.bucket_name)

        if not best_progress_list:
            return None

        progress_list, folder_names = best_progress_list

        best_index = Best_Model.best_progress_index(progress_list)
        best_progress = progress_list[best_index]
        best_folder_name = folder_names[best_index]
        best_vm_src = os.path.join(strings.best_model, best_folder_name)

        best_archive_path = os.path.join(strings.archive, strings.best_model)
        best_archived_folders = gcp.get_folder_names(self.bucket_name, best_archive_path)
        archive_len = len(best_archived_folders)

        # There are folders
        int_folder_names = [int(folder_name) for folder_name in best_archived_folders]
        # Has at most top_n elements
        int_folder_names = int_folder_names[:top_n]
        int_folder_names.sort()
        best_archived_folders = [str(int_folder_name) for int_folder_name in int_folder_names]
        inserted = False

        for idx, best_archived_folder in enumerate(best_archived_folders):
            # Iterates from best to worse
            archive_progress_pth = os.path.join(strings.archive, strings.best_model,
                                                best_archived_folder, strings.vm_progress_report)
            progress_json = gcp.stream_download_json(self.bucket_name, archive_progress_pth)
            archive_progress = Progress(progress=progress_json)
            if archive_progress.worse(best_progress.get_best()):
                # Need to insert new best into the archive

                # Iterates from second to last best archive to best archive that was just beat
                end = idx
                start = top_n - 1 if archive_len >= top_n else archive_len
                for i in range(start, end, -1):
                    src = os.path.join(best_archive_path, str(i))
                    dest = os.path.join(strings.archive, strings.best_model, str(i + 1))
                    gcp.move_cloud_folder(self.bucket_name, src, dest)

                # Inserting new best into archive
                dest = os.path.join(best_archive_path, str(idx + 1))
                gcp.move_cloud_folder(self.bucket_name, best_vm_src, dest)
                inserted = True
                break

        if not inserted and archive_len != top_n:
            # Did not beat any in the archive and there is room to insert in the end
            dest = os.path.join(best_archive_path, str(archive_len + 1))
            gcp.move_cloud_folder(self.bucket_name, best_vm_src, dest)
            inserted = True

        # True if the progress has been inserted in the best archive. False otherwise
        return inserted

    def update_meta_data(self):
        best_archive_path = os.path.join(strings.archive, strings.best_model)
        meta_path = os.path.join(best_archive_path, strings.meta)
        new_meta = False

        try:
            meta_json = gcp.stream_download_json(self.bucket_name, meta_path)
            meta_progress = Progress(progress=meta_json)
        except Exception as err:
            meta_progress = Progress()
            new_meta = True

        best_archived_folders = gcp.get_folder_names(self.bucket_name, best_archive_path)
        for idx, folder in enumerate(best_archived_folders):
            path = os.path.join(best_archive_path, folder, strings.vm_progress_report)
            best_progress_json = gcp.stream_download_json(self.bucket_name, path)
            best_progress = Progress(progress=best_progress_json)

            if idx == 0 and new_meta:
                meta_progress.set_compare_goal(*best_progress.get_compare_goal())

            meta_progress.add(folder, best_progress.get_best())

        gcp.stream_upload_str(self.bucket_name, json.dumps(meta_progress.get_progress()), meta_path)

    def archive(self):
        self.archive_results()
        result = self.archive_best_model(self.top_n)
        if result is not None:
            self.update_meta_data()
        self.clear_for_new_hyparams()
