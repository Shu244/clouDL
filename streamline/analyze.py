import matplotlib.pyplot as plt
import gcp_interactions as gcp
import argparse
import strings
import json
import os


def hr():
    print("---" * 20)


def plot_vals(x, y, title, ylabel, xlabel="Number of Epochs"):
    plt.plot(x, y)
    plt.ylabel(ylabel)
    plt.xlabel(xlabel)
    plt.title(title)
    plt.show()


class Downloader:
    def __init__(self, bucket_name, temp_path):
        self.bucket_name = bucket_name
        self.temp_path = temp_path

    def download(self, folder_name, ignore_filename=None):
        gcp.download_folder(self.bucket_name, folder_name, self.cplt_tmppth(folder_name), None)

    def cplt_tmppth(self, folder):
        return os.path.join(self.temp_path, folder)


class Hyperparameters:
    def __init__(self, hyparams_path):
        self.hyparams = json.load(open(hyparams_path))
        self.meaningful = self.meaningful_sec()

    def meaningful_sec(self):
        hyparam_sec = self.hyparams["hyperparameters"]
        meaningful = {}
        for key, value in hyparam_sec.items():
            if isinstance(value, list):
                meaningful[key] = value
        return meaningful

    def cur_vals(self):
        return self.hyparams["current_values"]

    def cur_meaningful_vals(self):
        cur_meaningful = {}
        cur_vals = self.hyparams["current_values"]
        for key in self.meaningful:
            cur_meaningful[key] = cur_vals[key]
        return cur_meaningful


class Progress:
    def __init__(self, progress_pth):
        self.progress = json.load(open(progress_pth))
        self.compare = self.progress["compare"]
        self.goal = self.progress["goal"]
        self.compare_vals = self.progress[self.compare]
        self.best = max(self.compare_vals) if self.goal == "max" else min(self.compare_vals)

    def get_best(self):
        return self.best

    def worse(self, val):
        if self.goal == 'max':
            if val > self.best:
                return True
            else:
                return False
        if self.goal == 'min':
            if val < self.best:
                return True
            else:
                return False

    def get_compare_goal(self):
        return self.compare, self.goal


class Errors:
    def __init__(self, downloader):
        self.downloader = downloader
        self.path = downloader.cplt_tmppth(strings.shared_errors)
        if not os.path.isdir(self.path):
            self.download()

    def download(self):
        os.mkdir(self.path)
        self.downloader.download(strings.shared_errors)

    def count(self):
        return len(os.listdir(self.path))

    def view_num(self):
        print('Number of errors %d' % self.count())

    def view_errors(self, limit=None):
        count = self.count()
        if not limit or limit > count:
            limit = self.count

        err_files = os.listdir(self.path)
        for i in range(0, limit):
            hr()
            print("Error %d" % i)
            err_str = open(os.path.join(self.path, err_files[i]), "r").read()
            print(err_str)


class Best_Model:

    def __init__(self, downloader):
        self.downloader = downloader
        self.path = downloader.cplt_tmppth(strings.best_model)
        if not os.path.isdir(self.path):
            self.download()

    def download(self):
        os.mkdir(self.path)
        # Ignores param.pt file
        self.downloader.download(strings.best_model, strings.params_file)

    def get_best(self):
        folder_names = os.listdir(self.path)

        if len(folder_names) == 0:
            return None

        best_progress = Progress(os.path.join(self.path, folder_names[0], strings.vm_progress_report))
        best_hyparams = Hyperparameters(os.path.join(self.path, folder_names[0], strings.vm_hyparams_report))

        for index, folder_name in enumerate(folder_names):
            if index == 0:
                continue

            progress = Progress(os.path.join(self.path, folder_name, strings.vm_progress_report))

            if best_progress.worse(progress.best):
                best_progress = progress
                best_hyparams = Hyperparameters(os.path.join(self.path, folder_name, strings.vm_progress_report))

        return best_progress, best_hyparams

    def view_best(self):
        result = self.get_best()

        if not result:
            print("No best model")
            return

        best_progress, best_hyparams = result
        print("Best %s is %s" % (best_progress.compare, str(best_progress.best)))
        print("Hyperparameter section:")
        print(best_hyparams.meaningful)
        print("Hyperparameters used:")
        print(best_hyparams.cur_meaningful_vals())
        plot_vals(best_progress["epochs"], best_progress.compare_vals, "Best Progress", best_progress.compare)


class Results:
    def __init__(self, downloader):
        self.downloader = downloader
        self.path = downloader.cplt_tmppth(strings.results)
        if not os.path.isdir(self.path):
            self.download()

    def download(self):
        os.mkdir(self.path)
        self.downloader.download(strings.results)

    def get_all_results(self):


    def view_results(self):
        return


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Analyzing the data after training")

    parser.add_argument('bucket_name', help='The name of the bucket')
    parser.add_argument("-m", '--tmppth', default="./tmp",
                        help='The folder to store temporary files downloaded from the cloud')
    parser.add_argument("-e", '--errs', type=int,
                        help='View the shared errors. Provide an int to limit to the num of errors shown')
    parser.add_argument("-b", '--best', help='View the best model. This assumes epochs is in the progress reports')
    parser.add_argument("-r", '--results', help='View the results. This assumes epochs is in the progress reports')


    args = parser.parse_args()
    downloader = Downloader(args.bucket_name, args.tmppth)

    if args.errs:
        errors = Errors(downloader)
        errors.view_num()
        errors.view_errors(args.errs)

    if args.best:
        best = Best_Model(downloader)
        best.view_best()

    if args.best:
        results = Results(downloader)
        results.view_results()



# Count number of results
# Plot all of them by VM (all graphs should have the same x and y min and max)

# separate downloading and analyzing since we can analyze multiple times and download once