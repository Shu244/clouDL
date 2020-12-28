import traceback
import requests
import copy
import time
import json
import os

from clouDL_utils.hyperparameters import Hyperparameters
from clouDL_utils import gcp_interactions as gcp
from clouDL_utils.progress import Progress
from clouDL_utils import strings


class Manager:
    '''
    Triggers saving the current state of the model, hyperparameters, and performance
    '''

    def __init__(self, temp_path, bucket_name, rank, torch):
        self.rank = rank
        self.bucket_name = bucket_name
        self.temp_path = temp_path
        self.torch = torch

        if not os.path.isdir(temp_path):
            os.mkdir(temp_path)

        self.quick_send = gcp.QuickSend(bucket_name)

        progress_path = os.path.join(strings.vm_progress, str(rank), strings.vm_progress_report)
        hyparams_path = os.path.join(strings.vm_progress, str(rank), strings.vm_hyparams_report)

        self.progress = Progress(progress_path=progress_path, bucket_name=bucket_name)
        self.hyparams = Hyperparameters(hyparams_path=hyparams_path, bucket_name=bucket_name)

        self.load_params = self.hyparams.force_cur_values()
        self.load_best_params = False
        self.count = 0

        # For tracking the model
        self.model = None
        self.best_params = None

        if self.load_params:
            params_path = os.path.join(strings.vm_progress, str(rank), strings.params_file)
            gcp.download_file(self.bucket_name, params_path, self.temp_path)

            try:
                params_path = os.path.join(strings.vm_progress, str(rank), strings.best_params_file)
                gcp.download_file(self.bucket_name, params_path, self.temp_path)
                self.load_best_params = True
            except Exception as err:
                print('No best params in cloud')

    def track_model(self, model):
        '''
        Auto load progress into model, track best params, and save checkpoints

        :param model: Model to track
        '''

        self.model = model

        if self.load_params:
            path = os.path.join(self.temp_path, strings.params_file)
            self.model.load_state_dict(self.torch.load(path))
        if self.load_best_params:
            path = os.path.join(self.temp_path, strings.best_params_file)
            self.best_params = self.torch.load(path)

    def start_epoch(self):
        return self.progress.start_epoch()

    def set_compare_goal(self, compare, goal):
        self.progress.set_compare_goal(compare, goal)

    def get_hyparams(self):
        return self.hyparams.get_hyparams()

    def get_progress(self):
        return self.progress.get_progress()

    def add_progress(self, key, value):
        improved = self.progress.add(key, value)
        if improved and self.model is not None:
            self.best_params = copy.deepcopy(self.model.state_dict())

    def finished(self, param_dict=None):
        '''
        :param param_dict: This can be the current params or the best params for the model.
        '''
        if param_dict is None:
            if self.best_params is not None:
                param_dict = self.best_params
            elif self.model is not None:
                param_dict = self.model.state_dict()
            else:
                raise ValueError

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

    def save_progress(self, param_dict=None, best_param_dict=None):
        if param_dict is None and self.model is not None:
            param_dict = self.model.state_dict()
        if best_param_dict is None and self.best_params is not None:
            best_param_dict = self.best_params

        if param_dict is None:
            raise ValueError

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
        self.torch.save(param_dict, local_path)
        gcp.upload_file(self.bucket_name, local_path, cloud_folder)

    def get_cur_max_iter(self):
        cur_iter = self.hyparams.get_raw_hyparams()[self.hyparams.cur_iter]
        max_iter = self.hyparams.get_raw_hyparams()["max_iter"]
        return cur_iter, max_iter

    @staticmethod
    def get_meta_data():
        root_url = 'http://metadata/computeMetadata/v1/instance/attributes/'
        rank_url = os.path.join(root_url, 'rank')
        bucket_url = os.path.join(root_url, 'bucket')

        rank_request = requests.get(rank_url, headers={'Metadata-Flavor': 'Google'})
        bucket_request = requests.get(bucket_url, headers={'Metadata-Flavor': 'Google'})
        rank = int(rank_request.text)
        bucket_name = bucket_request.text

        return rank, bucket_name

    @staticmethod
    def create_manager(torch, tmppath='./tmp', rank=None, bucket_name=None):
        if rank is None or bucket_name is None:
            try:
                meta_rank, meta_bucket_name = Manager.get_meta_data()
                rank = meta_rank
                bucket_name = meta_bucket_name
            except Exception as err:
                print('Could not get meta data')
                raise ValueError
        return Manager(tmppath, bucket_name, rank, torch)

    def hyparam_search(self, run):
        start, end = self.get_cur_max_iter()
        quick_send = self.quick_send
        rank = self.rank
        temp_path = self.temp_path

        while start < end:
            try:
                param_pth = os.path.join(temp_path, strings.params_file) if self.load_params else None
                best_param_pth = os.path.join(temp_path, strings.best_params_file) if self.load_best_params else None
                run(self, param_pth, best_param_pth)
                print("Trying new hyperparameters")
            except Exception as err:
                timestr = time.strftime("%m%d%Y-%H%M%S")
                readable_timestr = time.strftime("%m/%d/%Y-%H:%M:%S")
                filename = timestr + ("-vm%d" % rank) + "-iter" + str(start) + ".json"
                msg = {
                    "traceback": traceback.format_exc(),
                    "error": str(err),
                    "hyperparameters": self.get_hyparams(),
                    "progress": self.get_progress(),
                    "time": readable_timestr
                }
                msg = json.dumps(msg)
                print("Writing the following msg to shared errors folder in Google cloud")
                print(msg)
                quick_send.send(filename, msg, strings.shared_errors)

                self.reset()
                self.reset_cloud_progress()
            start += 1


class TestManager:
    '''
    This class is used to test your training model without having to interact with the cloud by using
    the actual Manager class.
    This is safe to run tests and dry runs on.
    '''

    def __init__(self, hyparams):
        self.hyparams = hyparams

    def get_hyparams(self):
        return self.hyparams

    def track_model(self, model):
        print('Tracking model')

    def start_epoch(self):
        return 0

    def set_compare_goal(self, compare, goal):
        print('Setting compare and goal')

    def add_progress(self, key, value):
        print('Adding progress')

    def finished(self, param_dict=None):
        print('Finishing')

    def save_progress(self, param_dict=None, best_param_dict=None):
        print('Saving progress')

    def hyparam_search(self, run):
        run(self)

    @staticmethod
    def create_manager(hyparams):
        return TestManager(hyparams)
