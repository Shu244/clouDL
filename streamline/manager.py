import gcp_interactions as gcp
import argparse
import strings
import random
import copy
import time
import json
import os


class Hyperparameters:

    def __init__(self, raw_hyparams):
        self.raw_hyparams = raw_hyparams
        self.cur_val = "current_values"

        if self.cur_val in raw_hyparams and raw_hyparams[self.cur_val] != None:
            # load in values
            self.cur_hyparams = self.raw_hyparams[self.cur_val]
            self.load_params = True
        else:
            # generate new values
            # self.load_params = False set in the generate method
            self.cur_hyparams = self.generate()

        self.raw_hyparams[self.cur_val] = None

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


def get_hyparams_folder(bucket_name, rank, tmp_folder_pth):
    folder_path = strings.vm_progress + ("/%s/" % rank)
    gcp.download_folder(bucket_name, folder_path, tmp_folder_pth)


def get_hyparams(tmp_folder_pth, rank):
    file_path = os.path.join(tmp_folder_pth, rank, strings.vm_progress_file)
    return Hyperparameters(json.load(open(file_path)))


def hyparam_search(hyparams, temp_path, quick_send, rank):
    start = hyparams.raw_hyparams["current_iter"]
    end = hyparams.raw_hyparams["max_iter"]

    while start < end:
        try:
            param_pth = os.path.join(temp_path, strings.params_file) if hyparams.load_params else None
            train(hyparams.get_hyparams(), param_pth)
            hyparams.generate()
        except Exception as err:
            timestr = time.strftime("%m%d%Y-%H%M%S")
            readable_timestr = time.strftime("%m/%d/%Y-%H:%M:%S")
            filename = timestr + "-vm" + rank + "-iter" + str(start) + ".json"
            msg = {
                "error": str(err),
                "hyperparameters": hyparams.get_hyparams(),
                "time": readable_timestr
            }
            msg = json.dumps(msg)
            quick_send.send(filename, msg, strings.shared_errors)
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

    parser.add_argument('rank', help='The id for this virtual machine')
    parser.add_argument('bucket_name', help='The name of the bucket')
    parser.add_argument("-m", '--tmppth', default="./tmp", help='The folder to store temporary files before moving to gcloud')

    args = parser.parse_args()

    quick_send = gcp.QuickSend(args.tmppth, args.bucket_name)
    get_hyparams_folder(args.bucket_name, args.rank, args.tmppth)
    hyparams = get_hyparams(args.tmppth, args.rank)
    hyparam_search(hyparams, args.tmppth, quick_send, args.rank)
