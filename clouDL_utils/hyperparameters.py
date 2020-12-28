import random
import copy
import json

from clouDL_utils import gcp_interactions as gcp
from clouDL_utils import strings

class Hyperparameters:
    def __init__(self, hyparams_path=None, hyparams=None, bucket_name=None):
        if not hyparams_path and not hyparams:
            raise ValueError

        if hyparams_path:
            # Letting errors pass through if file cannot be read since the file is mandatory
            if bucket_name:
                self.raw_hyparams = gcp.stream_download_json(bucket_name, hyparams_path)
            else:
                self.raw_hyparams = json.load(open(hyparams_path))
        if hyparams:
            self.raw_hyparams = hyparams

        self.cur_val = "current_values"
        self.cur_iter = "current_iter"

    def force_cur_values(self):
        '''
        Forces "current_values" key in raw_hyparams to have a value.
        :return: True if it already has a value. False otherwise.
        '''
        if self.cur_val in self.raw_hyparams and self.raw_hyparams[self.cur_val] != None:
            # "current_values" key has values
            return True
        else:
            # generate new current values
            self.generate()
            return False

    def reset(self):
        # Generate new current values
        self.generate()
        # Maintains track of number of sets of hyparameters tried
        self.raw_hyparams[self.cur_iter] = self.raw_hyparams[self.cur_iter] + 1

    def generate(self):
        '''
        Generates new hyperparameters according to specifications in raw_hyparam["hyperparameters"]
        '''

        hyparam_copy = copy.deepcopy(self.raw_hyparams["hyperparameters"])
        cur_iter = self.raw_hyparams[self.cur_iter]
        for key, value in hyparam_copy.items():
            if isinstance(value, list):
                # Defaults to uniform random
                new_val = Hyperparameters.uniform_random(value[0], value[1])
                hyparam_copy[key] = new_val
            elif isinstance(value, dict):
                data = value["data"]
                method = value["method"]

                if method == "list":
                    new_val = Hyperparameters.list(cur_iter, data)
                elif method == "step":
                    new_val = Hyperparameters.step(cur_iter, *data)
                elif method == "multiple":
                    new_val = Hyperparameters.multiple(cur_iter, *data)
                else:
                    new_val = Hyperparameters.uniform_random(*data)

                hyparam_copy[key] = new_val

        self.raw_hyparams[self.cur_val] = hyparam_copy

    def uniform_random(start, end):
        return random.uniform(start, end)

    def multiple(cur_iter, start, factor):
        return start*(factor**cur_iter)

    def list(cur_iter, lis):
        return lis[cur_iter % len(lis)]

    def step(cur_iter, start, step):
        return start + step*cur_iter

    def get_hyparams(self):
        return self.raw_hyparams[self.cur_val]

    def get_raw_hyparams(self):
        '''
        The raw hyperparameter dictionary contains the current hyperparemter values as
        well as the information specifying the portion of the hyperparameter grid being searched.

        :return: Raw hyperparameter dictionary
        '''

        return self.raw_hyparams

    def save_hyparams(self, quick_send, cloud_folder):
        quick_send.send(strings.vm_hyparams_report, json.dumps(self.raw_hyparams), cloud_folder)

    def interesting_sec(self):
        '''
        Gets part of the hyperparameter that are not constants
        :return: Dict of meaningful hyparameters
        '''

        hyparam_sec = self.raw_hyparams["hyperparameters"]
        interesting = {}
        for key, value in hyparam_sec.items():
            if isinstance(value, list) or isinstance(value, dict):
                interesting[key] = value
        return interesting

    def interesting_vals(self):
        interesting_cur_vals = {}
        cur_vals = self.get_hyparams()
        interesting_sec = self.interesting_sec()
        for key in interesting_sec:
            interesting_cur_vals[key] = cur_vals[key]
        return interesting_cur_vals
