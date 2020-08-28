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
        dest = self.cplt_tmppth(folder_name)
        if not os.path.isdir(dest):
            os.mkdir(dest)
            gcp.download_folder(self.bucket_name, folder_name, dest, ignore_filename)

    def cplt_tmppth(self, folder):
        return os.path.join(self.temp_path, folder)


class Hyperparameters:
    def __init__(self, hyparams_path=None, hyparams=None):
        if not hyparams_path and not hyparams:
            raise ValueError

        if hyparams_path:
            self.hyparams = json.load(open(hyparams_path))
        if hyparams:
            self.hyparams = hyparams

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
    def __init__(self, progress_path=None, progress=None):
        if not progress_path and not progress:
            raise ValueError

        if progress_path:
            self.progress = json.load(open(progress_path))
        if progress:
            self.progress = progress

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
        self.downloader.download(strings.shared_errors)

    def count(self):
        return len(os.listdir(self.path))

    def view(self, limit=None):
        count = self.count()

        print('Number of errors %d' % self.count())

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

            if best_progress.worse(progress.best):
                best_progress = progress
                best_hyparams = Hyperparameters(hyparams_path=os.path.join(self.path, folder_name, strings.vm_progress_report))

        return best_progress, best_hyparams

    def view(self, x_label):
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
        plot_vals(best_progress.progress[x_label], best_progress.compare_vals,
                  "Best Progress %s vs. %s" % (best_progress.compare, x_label), best_progress.compare, x_label)


class Results:
    def __init__(self, downloader):
        self.downloader = downloader
        self.path = downloader.cplt_tmppth(strings.results)
        self.downloader.download(strings.results)

    def get_progress(self, folder_pth):
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

        all_progress = [self.get_progress(folder_name) for folder_name in folder_names]
        dictionary = dict(zip(folder_names, all_progress))
        return dictionary

    def subplot(self, main_title, x_label, xrange, yrange, progress_list):
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

        fig, axs = plt.subplots(rows, cols)
        fig.suptitle(main_title)

        index = 0
        for row in range(0, rows):
            for col in range(0, cols):
                progress, filename = progress_list[index]
                index += 1

                x = progress.progress[x_label]
                y = progress.compare_vals

                subplot = axs[row, col]
                subplot.plot(x, y)
                subplot.set_title('%s: %s vs %s' % (filename, x_label, progress.compare))
                subplot.set_ylim(yrange)
                subplot.set_xlim(xrange)

        for ax in axs.flat:
            ax.set(xlabel=x_label, ylabel=progress_list[0][0].compare)

        # Hide x labels and tick labels for top plots and y ticks for right plots.
        for ax in axs.flat:
            ax.label_outer()

    def view(self, x_label, xrange, yrange):
        progress_dictionary = self.get_all_progress()

        if not progress_dictionary:
            print("No results available")
            return

        for folder_name, progress_list in progress_dictionary.items():
            main_title = 'For VM %s' % folder_name
            self.subplot(main_title, x_label, xrange, yrange, progress_list)
        plt.show()


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Analyzing the data after training")

    parser.add_argument('bucket_name', help='The name of the bucket')
    parser.add_argument("-m", '--tmppth', default="./tmp",
                        help='The folder to store temporary files downloaded from the cloud')
    parser.add_argument("-e", '--errs', type=int,
                        help='View the shared errors. Provide an int to limit to the num of errors shown')
    parser.add_argument("-b", '--best', default="epochs", help='View the best model. You can provide the x value to plot by')
    parser.add_argument("-r", '--results', default="epochs", help='View the results. You can provide the x value to plot by')
    parser.add_argument("-x", '--xrange', nargs=2, type=int, default=[0, None], help='Provide x range for plotting')
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
        xrange = args.xrange
        yrange = args.yrange

        if not xrange[1]:
            print("Please provide a x range")
            exit()

        results = Results(downloader)
        results.view(args.results, xrange, yrange)
