import traceback
import argparse
import torch
import copy
import time
import json
import os

from utils.Hyperparameters import Hyperparameters
from utils import gcp_interactions as gcp
from utils.Progress import Progress
from ai.MNIST_test import run
from utils import strings


'''
Best model and VM progress will save the same items:
-hyparameters, parameters, progress report

results will save one file containing:
-hyperparameters and progress report
'''

class Manager:
    '''
    Triggers saving the current state of the model, hyperparameters, and performance
    '''

    def __init__(self, temp_path, bucket_name, rank):
        self.rank = rank
        self.bucket_name = bucket_name
        self.temp_path = temp_path
        self.quick_send = gcp.QuickSend(bucket_name)

        progress_path = os.path.join(strings.vm_progress, str(rank), strings.vm_progress_report)
        hyparams_path = os.path.join(strings.vm_progress, str(rank), strings.vm_hyparams_report)

        self.progress = Progress(progress_path=progress_path, bucket_name=bucket_name)
        self.hyparams = Hyperparameters(hyparams_path=hyparams_path, bucket_name=bucket_name)

        self.load_params = self.hyparams.force_cur_values()
        self.load_best_params = False
        self.count = 0

        if self.load_params:
            params_path = os.path.join(strings.vm_progress, str(rank), strings.params_file)
            gcp.download_file(self.bucket_name, params_path, self.temp_path)

            try:
                params_path = os.path.join(strings.vm_progress, str(rank), strings.best_params_file)
                gcp.download_file(self.bucket_name, params_path, self.temp_path)
                self.load_best_params = True
            except Exception as err:
                print('No best params in cloud')

    def start_epoch(self):
        return self.progress.start_epoch()

    def set_compare_goal(self, compare, goal):
        self.progress.set_compare_goal(compare, goal)

    def get_hyparams(self):
        return self.hyparams.get_hyparams()

    def get_progress(self):
        return self.progress.get_progress()

    def add_progress(self, key, value):
        self.progress.add(key, value)

    def finished(self, param_dict):
        '''
        :param param_dict: This can be the current params or the best params for the model.
        '''

        self.save_results()
        self.save_best(param_dict)
        self.reset()
        self.reset_cloud_progress()

    def reset_cloud_progress(self):
        '''
        Resets the cloud folder keeping track of progress by deleting the params and removing current hyperparameter
        values
        '''
        cloud_folder_path = os.path.join(strings.vm_progress, str(self.rank))
        gcp.delete_all_prefixes(self.bucket_name, cloud_folder_path)

        hyparams_copy = copy.deepcopy(self.hyparams.raw_hyparams)
        hyparams_copy.pop("current_values", None)

        self.quick_send.send(strings.vm_hyparams_report, json.dumps(hyparams_copy), cloud_folder_path)

    def reset(self):
        self.progress.reset()
        self.hyparams.reset()

    def save_progress(self, param_dict, best_param_dict=None):
        folder_path = strings.vm_progress + ("/%d" % self.rank)
        self.progress.save_progress(self.quick_send, folder_path)
        self.hyparams.save_hyparams(self.quick_send, folder_path)
        self.save_params(param_dict, folder_path)
        if best_param_dict:
            self.save_params(best_param_dict, folder_path, strings.best_params_file)

    def save_results(self):
        progress_report = self.progress.get_progress()
        hyparams_report = self.hyparams.get_raw_hyparams()

        timestr = time.strftime("%m%d%Y-%H%M%S")
        readable_timestr = time.strftime("%m/%d/%Y-%H:%M:%S")

        filename = timestr + ("-vm%d" % self.rank) + ('-%d' % self.count) + ".json"
        result = {
            "progress": progress_report,
            "hyperparameters": hyparams_report,
            "time": readable_timestr
        }
        msg = json.dumps(result)

        self.quick_send.send(filename, msg, strings.results + ("/%d" % self.rank))
        self.count += 1

    def save_best(self, param_dict):
        if self.isBest(self.progress):
            folder_path = strings.best_model + ("/%d" % self.rank)
            self.progress.save_progress(self.quick_send, folder_path)
            self.hyparams.save_hyparams(self.quick_send, folder_path)
            self.save_params(param_dict, folder_path)
            return True
        return False

    def isBest(self, cur_report):
        progress_path = os.path.join(strings.best_model, str(self.rank), strings.vm_progress_report)

        try:
            best_progress_json = gcp.stream_download_json(self.bucket_name, progress_path)
            best_progress = Progress(progress=best_progress_json)
        except Exception as err:
            return True

        return best_progress.worse(cur_report.get_best())

    def save_params(self, param_dict, cloud_folder, filename=strings.params_file):
        '''
        Saving the parameters for a model to a folder determined by whether or not the training is done.

        :param param_dict: Generated by model.state_dict()
        '''
        local_path = os.path.join(self.temp_path, filename)
        torch.save(param_dict, local_path)
        gcp.upload_file(self.bucket_name, local_path, cloud_folder)

    def get_cur_max_iter(self):
        cur_iter = self.hyparams.get_raw_hyparams()[self.hyparams.cur_iter]
        max_iter = self.hyparams.get_raw_hyparams()["max_iter"]
        return cur_iter, max_iter


def hyparam_search(manager):
    start, end = manager.get_cur_max_iter()
    quick_send = manager.quick_send
    rank = manager.rank
    temp_path = manager.temp_path

    while start < end:
        try:
            param_pth = os.path.join(temp_path, strings.params_file) if manager.load_params else None
            best_param_pth = os.path.join(temp_path, strings.best_params_file) if manager.load_best_params else None
            run(manager, param_pth, best_param_pth)
            print("Trying new hyperparameters")
        except Exception as err:
            timestr = time.strftime("%m%d%Y-%H%M%S")
            readable_timestr = time.strftime("%m/%d/%Y-%H:%M:%S")
            filename = timestr + ("-vm%d" % rank) + "-iter" + str(start) + ".json"
            msg = {
                "traceback": traceback.format_exc(),
                "error": str(err),
                "hyperparameters": manager.get_hyparams(),
                "progress": manager.get_progress(),
                "time": readable_timestr
            }
            msg = json.dumps(msg)
            print("Writing the following msg to shared errors folder in Google cloud")
            print(msg)
            quick_send.send(filename, msg, strings.shared_errors)

            manager.reset()
            manager.reset_cloud_progress()
        start += 1


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Training model over a portion of the hyperparameters")

    parser.add_argument('rank', help='The id for this virtual machine', type=int)
    parser.add_argument('bucket_name', help='The name of the bucket')
    parser.add_argument("-m", '--tmppth', default="./tmp", help='The folder to store temporary files before moving to gcloud')

    args = parser.parse_args()

    manager = Manager(args.tmppth, args.bucket_name, args.rank)
    hyparam_search(manager)
