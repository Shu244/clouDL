import gcp_interactions as gcp
import argparse
import strings
import random
import copy
import torch
import time
import json
import os


'''
Best model and VM progress will save the same items:
-hyparameters, parameters, progress report

results will save one file containing:
-hyperparameters and progress report
'''


'''
Triggers saving the current state of the model, hyperparameters, and performance
'''
class Manager:
    def __init__(self, tmp_path, bucket_name, rank):
        self.download_progress_folder(bucket_name, tmp_path, rank)

        self.quick_send = gcp.QuickSend(tmp_path, bucket_name)
        self.rank = rank
        self.tracker = Tracker(self.quick_send)
        self.hyparams = Hyperparameters(self.quick_send)

    def download_progress_folder(self, bucket_name, tmp_folder, rank):
        folder_path = strings.vm_progress + ("/%d/" % rank)
        gcp.download_folder(bucket_name, folder_path, tmp_folder)

'''
Used to track the performance of a model while training:
-Loads and saves model progress
'''
class Tracker:
    def __init__(self, quick_send, rank):
        self.quick_send = quick_send
        self.progress_report_local_pth = os.path.join(
            quick_send.temp_path,
            rank,
            strings.vm_progress_report)
        self.report = json.load(open(self.progress_report_local_pth)) \
            if os.path.isfile(self.progress_report_local_pth) \
            else {}
        self.rank = rank

    def add(self, key, value):
        if key not in self.report:
            self.report[key] = []
        self.report[key].append(value)

    def save(self, quick_send, folder):
        quick_send.write(strings.vm_progress_report, json.dumps(self.report), folder)



'''
Manages the hyperparameters:
-Loads hyperparameters and saves them
'''
class Hyperparameters:

    def __init__(self, quick_send, rank):
        file_path = os.path.join(quick_send.temp_path, rank, strings.vm_progress_file)
        self.raw_hyparams = json.load(open(file_path))


        self.cur_val = "current_values"
        self.temp_folder = temp_path
        self.rank = rank

        if self.cur_val in raw_hyparams and raw_hyparams[self.cur_val] != None:
            # load in values
            self.cur_hyparams = self.raw_hyparams[self.cur_val]
            self.load_params = True
        else:
            # generate new values
            # self.load_params = False set in the generate method
            # self.cur_hyparams is also set
            self.generate()

        self.raw_hyparams[self.cur_val] = None

    def get_hyparams_folder(bucket_name, rank, tmp_folder_pth):
        folder_path = strings.vm_progress + ("/%d/" % rank)
        gcp.download_folder(bucket_name, folder_path, tmp_folder_pth)

    def get_hyparams(temp_path, rank):
        file_path = os.path.join(temp_path, rank, strings.vm_progress_file)
        return Hyperparameters(json.load(open(file_path)), temp_path, rank)

    def generate(self):
        '''
        Generates new hyperparameters according to specifications in hyparam_obj
        '''

        self.load_params = False
        hyparam_copy = copy.deepcopy(self.raw_hyparams["hyperparameters"])
        for key, value in hyparam_copy.items():
            if isinstance(value, list):
                new_val = random.uniform(value[0], value[1])
                hyparam_copy[key] = new_val
        self.cur_hyparams = hyparam_copy

    def get_hyparams(self):
        return self.cur_hyparams

    def save_best_params(self, best_params):
        '''
        best_params is generated using model.state_dict()

        :param best_params:
        :return:
        '''

        override = False
        # Checking if the current best params outperforms the previous best_state
        try:
            gcp.download_file(download param report here)
            report_path = os.path.join(self.temp_folder, strings.best_param_progress_file)
            report = json.load(open(report_path))

        except FileNotFoundError as err:
            # Could not download previous best param report.
            # Assuming best params has not existed yet
        self.save_params_locally(best_params, strings.best_params_file)
        gcp.upload_file(bucket_name, os.path.join(self.temp_folder, strings.best_params_file), results_folder)

    def save_state(self, model):

        self.raw_hyparams[self.cur_val] = self.cur_hyparams
        self.save_params_locally(best_params, strings.best_params_file)
        gcp.upload_file(bucket_name, os.path.join(self.temp_folder, strings.best_params_file), results_folder)

        folder = strings.vm_progress + ('/%d' % rank)
        quick_send.send(strings.vm_progress_file, json.dumps(self.raw_hyparams), folder)
        gcp.upload_file(bucketname, param_path, folder)

    def save_params_locally(self, params, filename):
        path = os.path.join(self.temp_folder, filename)
        torch.save(params, path)

    def save_param_paths(self):
        return self.temp_folder, strings.params_file



def hyparam_search(hyparams, temp_path, quick_send, rank):
    start = hyparams.raw_hyparams["current_iter"]
    end = hyparams.raw_hyparams["max_iter"]

    while start < end:
        try:
            param_pth = os.path.join(temp_path, strings.params_file) if hyparams.load_params else None
            train(hyparams.get_hyparams(), param_pth)
            hyparams.generate()
            # TODO save the results in the results cloud folder
            # Save the top n best params in the folder
        except Exception as err:
            timestr = time.strftime("%m%d%Y-%H%M%S")
            readable_timestr = time.strftime("%m/%d/%Y-%H:%M:%S")
            filename = timestr + ("-vm%d" % rank) + "-iter" + str(start) + ".json"
            msg = {
                "error": str(err),
                "hyperparameters": hyparams.get_hyparams(),
                "time": readable_timestr
            }
            msg = json.dumps(msg)
            quick_send.send(filename, msg, strings.shared_errors)
            print("Writing the following msg to shared errors folder in Google cloud")
            print(msg)
        start += 1


def train(a, b):
    print("training")
    print(a)
    print(b)
    if not b:
        raise Exception("Something terrible happened")


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Training model over a portion of the hyperparameters")

    parser.add_argument('rank', help='The id for this virtual machine', type=int)
    parser.add_argument('bucket_name', help='The name of the bucket')
    parser.add_argument("-m", '--tmppth', default="./tmp", help='The folder to store temporary files before moving to gcloud')

    args = parser.parse_args()

    quick_send = gcp.QuickSend(args.tmppth, args.bucket_name)
    get_hyparams_folder(args.bucket_name, args.rank, args.tmppth)
    hyparams = get_hyparams(args.tmppth, args.rank)
    hyparam_search(hyparams, args.tmppth, quick_send, args.rank)
