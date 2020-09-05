class Manager:
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
