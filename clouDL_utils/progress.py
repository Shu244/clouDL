import json

from clouDL_utils import gcp_interactions as gcp
from clouDL_utils import strings


class Progress:
    def __init__(self, progress_path=None, progress=None, bucket_name=None):
        if progress_path:
            if bucket_name:
                try:
                    self.progress = gcp.stream_download_json(bucket_name, progress_path)
                except Exception as err:
                    self.reset()
            else:
                self.progress = json.load(open(progress_path))
        if progress:
            self.progress = progress
        if not progress and not progress_path:
            self.reset()

    def get_compare_goal(self):
        return self.progress["compare"], self.progress["goal"]

    def get_compare_vals(self):
        compare, _ = self.get_compare_goal()
        return self.progress[compare]

    def get_best(self):
        _, goal = self.get_compare_goal()
        compare_vals = self.get_compare_vals()
        return max(compare_vals) if goal == "max" else min(compare_vals)

    def add(self, key, value):
        '''
        Adds the key and value to the progress

        :param key: Key
        :param value: Value
        :return: True if the key and value are the new best. False otherwise
        '''

        if key not in self.progress:
            self.progress[key] = []
        self.progress[key].append(value)

        compare, _ = self.get_compare_goal()
        if compare == key:
            compare_vals = self.get_compare_vals()
            best = self.get_best()
            index = compare_vals.index(best)
            if index == len(compare_vals) - 1:
                # The new key and value is the current best
                return True

        return False


    def save_progress(self, quick_send, folder):
        quick_send.send(strings.vm_progress_report, json.dumps(self.progress), folder)

    def get_progress(self):
        return self.progress

    def reset(self):
        self.progress = {
            "goal": "max",
            "compare": "val_accuracy"
        }

    def set_compare_goal(self, compare, goal):
        self.progress["compare"] = compare
        self.progress["goal"] = goal

    def approximate_start_epoch(self):
        dict_keys = list(self.progress.keys())
        dict_keys.remove("compare")
        dict_keys.remove("goal")
        if len(dict_keys) == 0:
            return 0
        return len(self.progress[dict_keys[0]])

    def start_epoch(self):
        epochs = "epochs"
        if epochs in self.progress:
            # +1 since we have already completed the last epoch in the list
            return self.progress[epochs][-1] + 1
        else:
            return self.approximate_start_epoch()

    def worse(self, val):
        best = self.get_best()
        _, goal = self.get_compare_goal()
        if goal == 'max':
            if val > best:
                return True
            else:
                return False
        if goal == 'min':
            if val < best:
                return True
            else:
                return False
