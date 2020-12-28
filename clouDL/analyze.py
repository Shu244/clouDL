import matplotlib.pyplot as plt
import argparse
import json
import os
import re

from clouDL_utils.hyperparameters import Hyperparameters
from clouDL_utils import gcp_interactions as gcp
from clouDL_utils.downloader import Downloader
from clouDL_utils.progress import Progress
from clouDL_utils import strings

from functools import cmp_to_key


def hr():
    print("---" * 20)


def plot_vals(x, y, title, ylabel, xlabel="Number of Epochs"):
    plt.plot(x, y, marker='o')
    plt.ylabel(ylabel)
    plt.xlabel(xlabel)
    plt.title(title)
    plt.show()


def cmp(a, b):
    '''
    Custom sorting method
    Both a and b are a list of tuples that contains a Progress object and a string
    '''

    a_str = a[1]
    b_str = b[1]

    a_digit = int("".join(filter(str.isdigit, a_str)))
    b_digit = int("".join(filter(str.isdigit, b_str)))

    return (a_digit > b_digit) - (a_digit < b_digit)


class Errors:
    def __init__(self, downloader):
        self.downloader = downloader
        self.path = downloader.cplt_tmppth(strings.shared_errors)
        self.msg = self.downloader.download(strings.shared_errors)

    def get_count(self):
        return len(os.listdir(self.path))

    def view(self, limit=None):
        count = self.get_count()

        hr()

        if self.msg:
            print(self.msg)

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
        self.download_msg = self.downloader.download(strings.best_model, strings.params_file)

    @staticmethod
    def best_progress_index(progress_list):
        '''
        Returns the index of the best progress. Only the first occurrence is returned.

        :param progress_list: Progress object list
        :return: Index of best progress
        '''

        if not progress_list:
            return None
        bests = [progress.get_best() for progress in progress_list]
        return bests.index(max(bests))

    @staticmethod
    def best_progress_list(bucket_name):
        folder_names = gcp.get_folder_names(bucket_name, strings.best_model)
        folder_names = list(folder_names)

        if not folder_names:
            return None

        progress_list = []
        for folder_name in folder_names:
            progress_path = os.path.join(strings.best_model, folder_name, strings.vm_progress_report)
            progress_json = gcp.stream_download_json(bucket_name, progress_path)
            progress = Progress(progress=progress_json)
            progress_list.append(progress)

        return progress_list, folder_names

    @staticmethod
    def get_best(path):
        folder_names = os.listdir(path)

        if len(folder_names) == 0:
            return None

        best_progress = Progress(progress_path=os.path.join(path, folder_names[0], strings.vm_progress_report))
        best_hyparams = Hyperparameters(hyparams_path=os.path.join(path, folder_names[0], strings.vm_hyparams_report))
        best_folder = folder_names[0]

        for index, folder_name in enumerate(folder_names):
            if index == 0:
                continue

            progress_path = os.path.join(path, folder_name, strings.vm_progress_report)

            if not os.path.isfile(progress_path):
                continue

            progress = Progress(progress_path=progress_path)

            if best_progress.worse(progress.get_best()):
                best_progress = progress
                best_hyparams = Hyperparameters(hyparams_path=os.path.join(path, folder_name, strings.vm_hyparams_report))
                best_folder = folder_name

        return best_progress, best_hyparams, best_folder

    @staticmethod
    def static_view(path, x_label, title):
        result = Best_Model.get_best(path)

        if not result:
            print("No best model")
            return

        best_progress, best_hyparams, best_folder = result
        compare, _ = best_progress.get_compare_goal()
        compare_vals = best_progress.get_compare_vals()

        print("Folder %s" % best_folder)
        print("Best %s is %s" % (compare, str(best_progress.get_best())))
        print("Hyperparameter section:")
        print(json.dumps(best_hyparams.interesting_sec()))
        print("Hyperparameters used:")
        print(best_hyparams.interesting_vals())
        complete_title = title + (": %s vs. %s" % (compare, x_label))
        plot_vals(best_progress.progress[x_label], compare_vals, complete_title, compare, x_label)

    def view(self, x_label):
        hr()

        if self.download_msg:
            print(self.download_msg)

        print('Best model from VM data:')
        Best_Model.static_view(self.path, x_label, "Current Iteration Best Progress")


class Results:
    def __init__(self, downloader):
        self.downloader = downloader
        self.path = downloader.cplt_tmppth(strings.results)
        self.download_msg = self.downloader.download(strings.results)

    def get_vm_progress(self, folder_name):
        folder_pth = os.path.join(self.path, folder_name)
        filenames = os.listdir(folder_pth)
        progress_list = []
        for filename in filenames:
            clpt_pth = os.path.join(folder_pth, filename)
            result_json = json.load(open(clpt_pth))
            progress_json = result_json["progress"]
            iter_id = re.search("(vm[0-9]+)-([0-9]+)", filename).group(2)
            id_str = "id: %s" % iter_id
            progress_list.append((Progress(progress=progress_json), id_str))
        progress_list.sort(key=cmp_to_key(cmp))
        return progress_list

    def get_all_progress(self):
        folder_names = os.listdir(self.path)

        if len(folder_names) == 0:
            return None

        '''
        Shape of all_progress:
        [
            [(Progress, id_str), ..., (Progress, id_str)],
            .
            .
            .
            [(Progress, id_str), ..., (Progress, id_str)]
        ]
        '''
        all_progress = [self.get_vm_progress(folder_name) for folder_name in folder_names]
        dictionary = dict(zip(folder_names, all_progress))
        return dictionary

    @staticmethod
    def subplot(main_title, x_label, yrange, progress_list):
        '''
        Creates subplots for the results from one VM

        :param main_title: Title of the entire subplot
        :param x_label: x label for each subplot
        :param progress_tuple: A list of tuples (one tuple for each result from a VM) that contains
                               a Progress object and the subplot title
        '''


        num = len(progress_list)
        cols = 3

        if num < cols:
            cols = num

        # ceiling division
        rows = (num + cols - 1 ) // cols

        fig, axs = plt.subplots(nrows=rows, ncols=cols, sharex=True, sharey=True)
        fig.suptitle(main_title)

        for index, (progress, subplot_title) in enumerate(progress_list):
            x = progress.progress[x_label]
            y = progress.get_compare_vals()

            row = index // cols
            col = index - row * cols

            if rows == 1 and cols == 1:
                subplot = axs
            elif rows == 1:
                subplot = axs[col]
            else:
                subplot = axs[row, col]

            subplot.plot(x, y, marker='o')
            subplot.set_title(subplot_title)
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

        hr()

        if self.download_msg:
            print(self.download_msg)

        print('Plotting results')

        if not progress_dictionary:
            print("No results available")
            return

        for folder_name, progress_list in progress_dictionary.items():
            main_title = 'For VM %s' % folder_name
            Results.subplot(main_title, x_label, yrange, progress_list)
        plt.show()


class Best_Archived_Models:

    def __init__(self, downloader):
        self.bucket_name = downloader.bucket_name
        self.downloader = downloader
        self.archive_path = os.path.join(strings.archive, strings.best_model)
        self.path = downloader.cplt_tmppth(self.archive_path)
        self.download_msg = self.downloader.download(self.archive_path, strings.params_file)

    def get_meta(self):
        meta_path = os.path.join(strings.archive, strings.best_model, strings.meta)
        meta_json = gcp.stream_download_json(self.bucket_name, meta_path)
        progress = Progress(progress=meta_json)
        return progress

    def best_progress_list(self):
        folders_and_files = os.listdir(self.path)

        if len(folders_and_files) == 0:
            return None

        progress_list = []
        for folder_or_file in folders_and_files:
            path = os.path.join(self.path, folder_or_file)
            if os.path.isdir(path):
                # The folder_or_file represents a folder
                # The folder name represents the rank of the model
                subplot_title = 'rank: %s' % folder_or_file

                progress_path = os.path.join(path, strings.vm_progress_report)
                progress = Progress(progress_path=progress_path)

                progress_list.append((progress, subplot_title))
        progress_list.sort(key=cmp_to_key(cmp))
        return progress_list

    def view(self, x_label, yrange):
        hr()

        if self.download_msg:
            print(self.download_msg)

        print('Best model from archive:')
        Best_Model.static_view(self.path, x_label, "Best Archived/Overall Progress")

        progress_list = self.best_progress_list()

        if progress_list:
            # Plotting meta data
            try:
                meta = self.get_meta()
                compare, _ = meta.get_compare_goal()
                rank_1 = meta.get_progress()['1']
                x = list(range(0, len(rank_1)))
                plot_vals(x, rank_1, "Best Model vs. Hyperparameter Tuning Iterations",
                     compare, "Iterations of Hyperparameter Tuning")
            except Exception as err:
                print('No meta data available')

            # Plotting subplots
            main_title = "Best Models From Archive"
            Results.subplot(main_title, x_label, yrange, progress_list)
            plt.show()
        else:
            print('No archived best model, cannot create subplots and will not plot metadata')


def main():
    parser = argparse.ArgumentParser(description="Analyzing the data after training")

    parser.add_argument('bucket_name', help='The name of the bucket')
    parser.add_argument("-m", '--tmppth', default="./tmp",
                        help='The folder to store temporary files downloaded from the cloud')
    parser.add_argument("-e", '--errs', type=int,
                        help='View the shared errors. Provide an int to limit to the num of errors shown')
    parser.add_argument("-b", '--best', help='View the best model. Provide the x value to plot by')
    parser.add_argument("-a", '--archive', nargs=2, help='View the best archived models. Provide the x value to plot by and top n to archive')
    parser.add_argument("-r", '--results', help='View the results. Provide the x value to plot by')
    parser.add_argument("-y", '--yrange', nargs=2, type=int, default=[0, 100], help='Provide y range for plotting')


    args = parser.parse_args()
    downloader = Downloader(args.bucket_name, args.tmppth)

    if args.errs:
        errors = Errors(downloader)
        errors.view(args.errs)

    if args.results:
        results = Results(downloader)
        results.view(args.results, args.yrange)

    if args.best:
        best = Best_Model(downloader)
        best.view(args.best)

    if args.archive:
        hr()
        archive_approval = input(
            "Archiving will move all the VM data and make them inaccessible by some features. Continue? [yes | no]")
        if archive_approval.lower() in ["yes", "y"]:
            # Importing here to avoid cyclic imports
            from clouDL_utils.archive import Archive

            x_label = args.archive[0]
            top_n = int(args.archive[1])

            print('Archiving')
            archive = Archive(args.bucket_name, top_n)
            archive.archive()

            best_archive = Best_Archived_Models(downloader)
            best_archive.view(x_label, args.yrange)
        else:
            print("Cannot analyze archive until VM data is archived")


if __name__ == '__main__':
    main()
