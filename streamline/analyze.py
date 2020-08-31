import matplotlib.pyplot as plt
import argparse
import json
import os
import re

from utils.Hyperparameters import Hyperparameters
from utils.Progress import Progress
from utils.Downloader import Downloader
from utils import strings


def hr():
    print("---" * 20)


def plot_vals(x, y, title, ylabel, xlabel="Number of Epochs"):
    plt.plot(x, y)
    plt.ylabel(ylabel)
    plt.xlabel(xlabel)
    plt.title(title)
    plt.show()


class Errors:
    def __init__(self, downloader):
        self.downloader = downloader
        self.path = downloader.cplt_tmppth(strings.shared_errors)
        self.downloader.download(strings.shared_errors)

    def get_count(self):
        return len(os.listdir(self.path))

    def view(self, limit=None):
        count = self.get_count()

        hr()
        print('Number of errors: %d' % count)

        if not limit or limit > count:
            limit = count

        err_files = os.listdir(self.path)
        for i in range(0, limit):
            hr()
            print("Error %d:" % i)
            err_str = open(os.path.join(self.path, err_files[i]), "r").read()
            print(err_str)


class Best_Model:

    def __init__(self, downloader):
        self.downloader = downloader
        self.path = downloader.cplt_tmppth(strings.best_model)
        # Ignores param.pt file when downloading folder
        self.downloader.download(strings.best_model, strings.params_file)

    def get_best(self):
        folder_names = os.listdir(self.path)

        if len(folder_names) == 0:
            return None

        best_progress = Progress(progress_path=os.path.join(self.path, folder_names[0], strings.vm_progress_report))
        best_hyparams = Hyperparameters(hyparams_path=os.path.join(self.path, folder_names[0], strings.vm_hyparams_report))

        for index, folder_name in enumerate(folder_names):
            if index == 0:
                continue

            progress = Progress(progress_path=os.path.join(self.path, folder_name, strings.vm_progress_report))

            if best_progress.worse(progress.get_best()):
                best_progress = progress
                best_hyparams = Hyperparameters(hyparams_path=os.path.join(self.path, folder_name, strings.vm_progress_report))

        return best_progress, best_hyparams

    def view(self, x_label):
        result = self.get_best()

        if not result:
            print("No best model")
            return

        best_progress, best_hyparams = result
        compare, _ = best_progress.get_compare_goal()
        compare_vals = best_progress.get_compare_vals()

        hr()
        print("Best %s is %s" % (compare, str(best_progress.get_best())))
        print("Hyperparameter section:")
        print(json.dumps(best_hyparams.interesting_sec()))
        print("Hyperparameters used:")
        print(best_hyparams.interesting_vals())
        plot_vals(best_progress.progress[x_label], compare_vals, "Best Progress %s vs. %s" % (compare, x_label), compare, x_label)


class Results:
    def __init__(self, downloader):
        self.downloader = downloader
        self.path = downloader.cplt_tmppth(strings.results)
        self.downloader.download(strings.results)

    def get_vm_progress(self, folder_name):
        folder_pth = os.path.join(self.path, folder_name)
        filenames = os.listdir(folder_pth)
        progress_list = []
        for filename in filenames:
            clpt_pth = os.path.join(folder_pth, filename)
            result_json = json.load(open(clpt_pth))
            progress_json = result_json["progress"]
            progress_list.append((Progress(progress=progress_json), filename))
        return progress_list

    def get_all_progress(self):
        folder_names = os.listdir(self.path)

        if len(folder_names) == 0:
            return None

        '''
        Shape of all_progress:
        [
            [(Progress, filename), ..., (Progress, filename)],
            .
            .
            .
            [(Progress, filename), ..., (Progress, filename)]
        ]
        '''
        all_progress = [self.get_vm_progress(folder_name) for folder_name in folder_names]
        dictionary = dict(zip(folder_names, all_progress))
        return dictionary

    def subplot(self, main_title, x_label, yrange, progress_list):
        '''
        Creates subplots for the results from one VM

        :param main_title: Title of the entire subplot
        :param x_label: x label for each subplot
        :param progress_tuple: A list of tuples (one for each result from a VM) that contains
                               a Progress object and the associated filename
        '''


        num = len(progress_list)
        cols = 3
        # ceiling division
        rows = (num + cols - 1 ) // cols

        fig, axs = plt.subplots(nrows=rows, ncols=cols, sharex=True, sharey=True)
        fig.suptitle(main_title)

        for index, (progress, filename) in enumerate(progress_list):
            x = progress.progress[x_label]
            y = progress.get_compare_vals()

            row = index // cols
            col = index - row * cols

            if rows == 1:
                subplot = axs[col]
            else:
                subplot = axs[row, col]
            subplot.plot(x, y)
            id = re.search("(vm[0-9]+)-([0-9]+)", filename).group(2)
            subplot.set_title('id: %s' % id)
            subplot.set_ylim(yrange)

        # Credit to https://stackoverflow.com/a/53172335
        # Uses a common x and y label for all subplots
        fig.add_subplot(111, frameon=False)
        plt.tick_params(labelcolor='none', top=False, bottom=False, left=False, right=False)
        plt.xlabel(x_label)
        plt.ylabel(progress_list[0][0].get_compare_goal()[0], labelpad=25)

        # Labelpad and this are to improve spacing
        fig.tight_layout()

    def view(self, x_label, yrange):
        progress_dictionary = self.get_all_progress()

        if not progress_dictionary:
            print("No results available")
            return

        for folder_name, progress_list in progress_dictionary.items():
            main_title = 'For VM %s' % folder_name
            self.subplot(main_title, x_label, yrange, progress_list)
        plt.show()


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Analyzing the data after training")

    parser.add_argument('bucket_name', help='The name of the bucket')
    parser.add_argument("-m", '--tmppth', default="./tmp",
                        help='The folder to store temporary files downloaded from the cloud')
    parser.add_argument("-e", '--errs', type=int,
                        help='View the shared errors. Provide an int to limit to the num of errors shown')
    parser.add_argument("-b", '--best', help='View the best model. You can provide the x value to plot by')
    parser.add_argument("-r", '--results', help='View the results. You can provide the x value to plot by')
    parser.add_argument("-y", '--yrange', nargs=2, type=int, default=[0, 100], help='Provide x range for plotting')


    args = parser.parse_args()
    downloader = Downloader(args.bucket_name, args.tmppth)

    if args.errs:
        errors = Errors(downloader)
        errors.view(args.errs)

    if args.best:
        best = Best_Model(downloader)
        best.view(args.best)

    if args.results:
        yrange = args.yrange
        results = Results(downloader)
        results.view(args.results, yrange)
