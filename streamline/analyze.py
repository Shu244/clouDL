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

    def download(self, folder_name):
        gcp.download_folder(self.bucket_name, folder_name, self.complete_tmppth(folder_name))

    def complete_tmppth(self, folder):
        return os.path.join(self.temp_path, folder)


class Errors:
    def __init__(self, downloader):
        self.downloader = downloader
        self.path = downloader.complete_tmppth(strings.shared_errors)
        os.mkdir(self.path)

    def download(self):
        self.downloader.download(strings.shared_errors)

    def count(self):
        return len(os.listdir(self.path))

    def view_num(self):
        print('Number of errors %d' % self.count())

    def view(self, limit=None):
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
        self.path = downloader.complete_tmppth(strings.best_model)
        os.mkdir(self.path)

    def view_best(self):
        folder_names = os.listdir(self.path)
        best = None
        best_folder = None
        compare = None
        goal = None

        all_hyparams_secs = []

        for index, folder_name in enumerate(folder_names):
            progress_path = os.path.join(self.path, folder_name, strings.vm_progress_report)
            hyparams_path = os.path.join(self.path, folder_name, strings.vm_hyparams_report)
            progress_report = json.load(open(progress_path))
            hyparam_report = json.load(open(hyparams_path))

            all_hyparams_secs.append(hyparam_report["hyperparameters"])

            if index == 0:
                compare = progress_report["compare"]
                goal = progress_report["goal"]
            val = progress_report[compare]
            if goal == "max":
                if not best or val > best:
                    best = val
                    best_folder = folder_name
            else:
                if not best or val < best:
                    best = val
                    best_folder = folder_name
        best_hyparams = json.load(open(os.path.join(self.path, best_folder, strings.vm_hyparams_report)))

        hr()
        print("Compare: %s, Goal: %s" % (compare, goal))
        print("Best value: %s" % str(best))
        print("Best hyperparameters: ")
        print(json.dumps(best_hyparams))

        hr()
        print("Hyperparameter grid searched by each VM:")
        # TODO



if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Analyzing the data after training")

    parser.add_argument('bucket_name', help='The name of the bucket')
    parser.add_argument("-m", '--tmppth', default="./tmp",
                        help='The folder to store temporary files downloaded from the cloud')
    parser.add_argument("-e", '--errs', type=int,
                        help='View the shared errors. Provide an int to limit to the num of errors shown')
    parser.add_argument("-b", '--best', help='View the best model')

    args = parser.parse_args()
    downloader = Downloader(args.bucket_name, args.tmppth)

    if args.errs:
        errors = Errors(downloader)
        errors.download()
        errors.view_num()
        errors.view(args.errs)

    if args.best:
        best = Best_Model(downloader)
        best.view_best()


# Count number of results
# Plot all of them by VM (all graphs should have the same x and y min and max)

# View hyperparameters portion for each VM

# separate downloading and analyzing since we can analyze multiple times and download once