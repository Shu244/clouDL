import pathlib
import os

from clouDL_utils import gcp_interactions as gcp


class Downloader:
    def __init__(self, bucket_name, temp_path):
        self.bucket_name = bucket_name
        self.temp_path = temp_path

    def download(self, folder_name, ignore_filename=None):
        dest = self.cplt_tmppth(folder_name)
        if not os.path.isdir(dest):
            pathlib.Path(dest).mkdir(parents=True, exist_ok=True)
            gcp.download_folder(self.bucket_name, folder_name, dest, ignore_filename)
            return None
        else:
            return 'The folder %s already exists and will be used (DATA MAY BE OUTDATED!)' % dest

    def cplt_tmppth(self, folder):
        return os.path.join(self.temp_path, folder)
