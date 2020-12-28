class EarlyStopping(object):
    def __init__(self, mode='min', patience=10):
        self.patience = patience
        self.best = None  # No best yet.
        self.num_bad_epochs = 0  # No bad epoches yet
        self.is_better = EarlyStopping._init_is_better(mode)

    def stop(self, metrics):
        # When starting, best is set to be the first metric
        if self.best is None:
            self.best = metrics
            return False

        if self.is_better(metrics, self.best):
            self.num_bad_epochs = 0
            self.best = metrics
        else:
            self.num_bad_epochs += 1

        if self.num_bad_epochs >= self.patience:
            return True

        return False

    @staticmethod
    def _init_is_better(mode):
        if mode not in {'min', 'max'}:
            raise ValueError('mode ' + mode + ' is unknown!')
        if mode == 'min':
            return lambda a, best: a < best
        if mode == 'max':
            return lambda a, best: a > best