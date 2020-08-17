from __future__ import print_function, division

import torch
import torch.nn as nn
import torch.optim as optim
from torch.optim import lr_scheduler
import numpy as np
import torchvision
from torchvision import models, transforms
from torch.utils.data import Dataset
import matplotlib.pyplot as plt
import time
import copy
import os



############################################################
# Configurations
############################################################

LR = 0.01
MOMENTUM = 0.9
L2 = 0.00001
SCHEDULER_STEP = 110
MULTIPLICATIVE_FACTOR = 0.2
PATIENCE = 15
NUM_EPOCHES = 200
EPOCH_TO_SAVE = 5
BATCH_SIZE = 512
model_str = 'Model 2'
plt_data_file_name = 'plt_data.npy'
folder = '/home/shuhao/Downloads/data/cifar_base'


############################################################
# Dataset
############################################################


# Normalizing should only be used if I am not using pretrained parameters
# unless the pretrained parameters expect normalized inputs
transform_train = transforms.Compose([
    # Only apply these augmentations some times
    transforms.RandomApply(
        [
            transforms.ColorJitter(brightness=0.5, contrast=0.5)
            # Test this transformation. Does not seem to help
            # transforms.RandomAffine(degrees=0, translate=[.1, .1])
        ],
        p=0.5
    ),
    # This transformation proven to cause unreliable accuracy around 40% mark.
    # transforms.RandomPerspective(p=0.35, distortion_scale=0.5, interpolation=3),
    transforms.RandomCrop(32, padding=4),
    transforms.RandomHorizontalFlip(),
    transforms.RandomRotation(15),
    transforms.ToTensor(),
    transforms.RandomErasing(p=0.5, scale=(0.02, 0.20))
])

# For speed reason, FiveCrop is not performed on development set.
transform_dev = transforms.Compose([
    transforms.ToTensor()
])


train_dataset = torchvision.datasets.CIFAR10(root='./data', train=True,
                                        download=True, transform=transform_train)
train_dataloader = torch.utils.data.DataLoader(train_dataset, batch_size=BATCH_SIZE,
                                          shuffle=True, num_workers=4)

dev_dataset = torchvision.datasets.CIFAR10(root='./data', train=False,
                                       download=True, transform=transform_dev)
dev_dataloader = torch.utils.data.DataLoader(dev_dataset, batch_size=BATCH_SIZE,
                                         shuffle=False, num_workers=4)

dataset_sizes = [len(train_dataset), len(dev_dataset)]
device = torch.device("cuda:0" if torch.cuda.is_available() else "cpu")

if not os.path.exists(folder):
    os.mkdir(folder)


############################################################
# Sanity check for datalaoder
############################################################


# Shows example of data
def imshow(inp, title=None):
    """Imshow for Tensor."""
    # imshow treats image as HxWxC but tensors use CxHxW
    inp = inp.numpy().transpose((1, 2, 0))
    # values below 0 becomes 0 and values greater than 1 becomes 1.
    inp = np.clip(inp, 0, 1)
    plt.imshow(inp)
    if title is not None:
        plt.title(title)
    plt.show()


# Get a batch of training data
inputs, classes = next(iter(train_dataloader))
inputs = inputs[:4]

# Make a grid from batch
out = torchvision.utils.make_grid(inputs)

imshow(out, title='Examples of training image')


############################################################
# Training functions stopping
############################################################


class EarlyStopping(object):
    def __init__(self, mode='min', min_delta=0, patience=10, percentage=False):
        '''
        Args:
            mode: min or max
            min_delta: new metric has to be within min_delta to be consider better than current best_metric
            patience: patience before stopping.
            percentage: if min_delta is a percentage, then true; false otherwise.
        '''
        self.mode = mode
        self.min_delta = min_delta
        self.patience = patience
        self.best = None # No best yet.
        self.num_bad_epochs = 0 # No bad epoches yet
        self.is_better = None
        self._init_is_better(mode, min_delta, percentage)

        # Never stop if patience is 0 and always save the new metric.
        if patience == 0:
            self.is_better = lambda a, b: True
            self.stop = lambda a: False

    # metric represents the values you are measuring for early stopping.
    # returns true to stop
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

    # Custom method to determine what is better.
    def _init_is_better(self, mode, min_delta, percentage):
        if mode not in {'min', 'max'}:
            raise ValueError('mode ' + mode + ' is unknown!')
        if not percentage:
            if mode == 'min':
                self.is_better = lambda a, best: a < best - min_delta
            if mode == 'max':
                self.is_better = lambda a, best: a > best + min_delta
        else:
            if mode == 'min':
                self.is_better = lambda a, best: a < best - (
                            best * min_delta / 100)
            if mode == 'max':
                self.is_better = lambda a, best: a > best + (
                            best * min_delta / 100)


best_model_parameters = {}  # Uses global scope


def train_model(model, criterion, optimizer, early_stopping=None, scheduler=None, num_epochs=25, epoch_to_save=5):
    '''
    Args:
        model: model to train
        criterion: calculates loss
        optimizer: optimizer that takes step in gradient descent
        scheduler: schedule to adjust learning rate
        num_epoches:  epoches to train for
    '''

    # Used to track the time it takes to train a model.
    since = time.time()

    # Store the best parameters while training.
    best_model_parameters = copy.deepcopy(model.state_dict())
    best_acc = 0.0

    plt_training_loss = []
    plt_dev_loss = []
    plt_dev_acc = []
    plt_epochs = []

    for epoch in range(num_epochs):
        if epoch % epoch_to_save == 0:
            save_model(model)

        print('Epoch {}/{}'.format(epoch, num_epochs - 1))
        print('-' * 10)

        # ----------------------------------Training Phase of Epoch-----------------------------------------------
        model.train()
        epoch_loss = 0.0
        epoch_correct = 0

        countI = 0
        # Iterate over mini batches of training data.
        for inputs, labels in train_dataloader:
            print('batch: ', countI)
            countI += 1
            # if GPU device exists, must load data to GPU.
            inputs = inputs.to(device)
            labels = labels.to(device)

            # zero the parameter gradients
            optimizer.zero_grad()

            # forward
            outputs = model(inputs)
            # returns tensors (value, index) for the maximum value in each row.
            _, preds = torch.max(outputs, 1)
            # returns one loss value, which is averaged over the mini-batch.
            loss = criterion(outputs, labels)

            # Update parameters
            loss.backward()
            optimizer.step()

            # loss.item is the loss averaged over the mini-batch
            epoch_loss += loss.item() * inputs.size(0)
            epoch_correct += torch.sum(preds == labels.data)


        # Print average loss for training
        epoch_avg_loss = epoch_loss / dataset_sizes[0]
        # Print accuracy for training
        epoch_acc = epoch_correct.double() / dataset_sizes[0]
        print('Training Loss: {:.4f} Acc: {:.4f}'.format(epoch_avg_loss, epoch_acc))


        scheduler.step()
        plt_training_loss.append(epoch_avg_loss)
        # ----------------------------------Evaluating Phase of Epoch-----------------------------------------------

        model.eval()  # Set model to evaluate mode
        epoch_loss = 0.0
        epoch_correct = 0

        # Iterate over dev data.
        for inputs, labels in dev_dataloader:
            inputs = inputs.to(device)
            labels = labels.to(device)

            with torch.set_grad_enabled(False):
                outputs = model(inputs)
                _, preds = torch.max(outputs, 1)
                loss = criterion(outputs, labels)

            epoch_loss += loss.item() * inputs.size(0)
            epoch_correct += torch.sum(preds == labels.data)

        epoch_avg_loss = epoch_loss / dataset_sizes[1]
        epoch_acc = epoch_correct.item() / dataset_sizes[1]  # item gets value from tensor containing one value regardless of device
        print('Evaluation Loss: {:.4f} Acc: {:.4f}'.format(epoch_avg_loss, epoch_acc))

        plt_dev_loss.append(epoch_avg_loss)
        plt_dev_acc.append(epoch_acc)
        plt_epochs.append(epoch)

        # deep copy the best model
        if epoch_acc > best_acc:
            best_acc = epoch_acc
            best_model_parameters = copy.deepcopy(model.state_dict())

        if early_stopping.stop(epoch_acc):
            print('-' * 10)
            print('Early stopping used.')
            break

        # ---------------------------------- End Evaluating Phase of Epoch-----------------------------------------------

    time_elapsed = time.time() - since
    print('Training complete in {:.0f}m {:.0f}s'.format(time_elapsed // 60, time_elapsed % 60))
    print('Best val Acc: {:4f}'.format(best_acc))

    model.load_state_dict(best_model_parameters)
    save_model(model)
    return model, plt_training_loss, plt_dev_loss, plt_dev_acc, plt_epochs


# ----------------------------Trying VGG16---------------------------------
def create_model():
    model = models.vgg16(pretrained=True)
    model.classifier[6] = nn.Linear(in_features=4096, out_features=100, bias=True)
    return model


def save_model(model, filename="parameters.pt"):
    # path = os.path.join(folder, filename)
    # torch.save(model.state_dict(), path)
    print('Not saving when testing')


def load_parameters(model=None, filename="parameters.pt"):
    print('Loading existing parameters.')
    path = os.path.join(folder, filename)
    if model:
        # Device defaults of GPU
        model.load_state_dict(torch.load(path, map_location=device))
    else:
        model = create_model()
        model.to(device)
        # Device defaults of GPU
        model.load_state_dict(torch.load(path, map_location=device))
    return model


def plot_vals(x, y, title, ylabel, xlabel="Number of Epochs"):
    plt.plot(x, y)
    plt.ylabel(ylabel)
    plt.xlabel(xlabel)
    plt.title(title)
    plt.show()


def plot_from_file(path=plt_data_file_name, modelStr=model_str):
    arr = load_arr(path)
    epoches = arr[3]
    plot_vals(epoches, arr[0], "Training Loss Over Epochs For " + modelStr, "Cross Entropy Loss")
    plot_vals(epoches, arr[1], "Development Loss Over Epochs For " + modelStr, "Cross Entropy Loss")
    plot_vals(epoches, arr[2], "Development Accuracy Over Epochs For " + modelStr, "Accuracy (%)")


def save_arr(arr, name):
    path = os.path.join(folder, name)
    np.save(path, arr)


def load_arr(name):
    path = os.path.join(folder, name)
    return np.load(path, allow_pickle=True)


model = create_model()


# if GPU is available, must also transfer model to GPU
model = model.to(device)
criterion = nn.CrossEntropyLoss()
optimizer = optim.SGD(model.parameters(), lr=LR, momentum=MOMENTUM, weight_decay=L2)
# more schedulers in addition to StepLR can be found at https://pytorch.org/docs/stable/optim.html#how-to-adjust-learning-rate
exp_lr_scheduler = lr_scheduler.StepLR(optimizer, step_size=SCHEDULER_STEP, gamma=MULTIPLICATIVE_FACTOR)


# Training
try:
    path_of_params = os.path.join(folder, "parameters.pt")
    if os.path.exists(path_of_params):
        model = load_parameters(model)

    early_stopping = EarlyStopping(mode='max', min_delta=0, patience=PATIENCE, percentage=False)
    (model, t_loss, d_loss, d_acc, epoch) = train_model(model=model, criterion=criterion, optimizer=optimizer,
                                                        early_stopping=early_stopping, scheduler=exp_lr_scheduler,
                                                        num_epochs=NUM_EPOCHES,
                                                        epoch_to_save=EPOCH_TO_SAVE)

    plt_data = np.array([t_loss, d_loss, d_acc, epoch])
    save_arr(plt_data, plt_data_file_name)
except:
    print('Exception occurred and will now save best model.')
    model.load_state_dict(best_model_parameters)
    save_model(model)

plot_from_file()
