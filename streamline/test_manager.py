class Manager:
    '''
    This class is used to test your training model without having to interact with the cloud by using
    the actual Manager class.
    This is safe to run tests and dry runs on.
    '''

    def __init__(self, hyparams):
        self.hyparams = hyparams

    def add_progress(self, key, value):
        print("Test add progress")

    def save_progress(self, params_dict):
        print("Test save progress")

    def finished(self, params_dict):
        print("Test finished")

    def get_hyparams(self):
        return self.hyparams