import os

from . import gcp_interactions as gcp
from . import strings


'''
Need to clear: VM-progress, best_model, results, and shared errors

Need to archive: top N models (keep track of best score in meta data), results 

archive:
-best_models
--meta
--1
---params.pt
---progress.json
---hyperparameters.json
--2
--3
-results
--many results

should also be able to plot best_models meta data
'''

class Archive:
    def __init__(self, downloader):
        self.downloader = downloader
        self.bucket_name = downloader.bucket_name
        self.temp_path = downloader.temp_path

    def clear_for_new_hyparams(self):
        gcp.delete_all_prefixes(self.bucket_name, strings.vm_progress)
        gcp.delete_all_prefixes(self.bucket_name, strings.best_model)
        gcp.delete_all_prefixes(self.bucket_name, strings.results)
        gcp.delete_all_prefixes(self.bucket_name, strings.shared_errors)

    def archive_results(self, results_path):
        folders = os.listdir(results_path)
        if len(folders) == 0:
            return

        for folder in folders:
            folder_path = os.path.join(results_path, folder)
            files = os.listdir(folder_path)
            for file in files:
                gcp_path = os.path.join(strings.archive, strings.results)
                gcp.upload_file(self.bucket_name, os.path.join(folder_path, file), gcp_path)

    def archive_best_model(self, best_model_path):
        folders = os.listdir(best_model_path)
        if len(folders) == 0:
            return

        # Get top Models from archive
        # Get best model from best_models
        # Check where best_model fits
        # Break or upload best_model
        # Update meta_data (should only contain the absolute best model)

        return

    def archive(self):
        temp_path = self.downloader.temp_path
        bucket_name = self.downloader.bucket_name

        archive_path = os.path.join(temp_path, strings.archive)
        best_model_path = os.path.join(temp_path, strings.best_model)
        results_path = os.path.join(temp_path, strings.results)
        if os.path.isdir(archive_path):
            raise ValueError("Please manually clear archive folder at %s" % archive_path)
        if os.path.isdir(best_model_path):
            raise ValueError("Please manually clear best model folder at %s" % best_model_path)
        if os.path.isdir(results_path):
            raise ValueError("Please manually clear results folder at %s" % results_path)

        self.downloader.download(strings.archive, ignore_filename=strings.params_file)
        self.downloader.download(strings.best_model, ignore_filename=strings.params_file)
        self.downloader.download(strings.results)

        self.archive_results(results_path)
        self.archive_best_model(best_model_path)
        self.clear_for_new_hyparams()
