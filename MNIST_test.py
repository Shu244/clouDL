from __future__ import print_function
import torch
import torch.nn as nn
import torch.nn.functional as F
import torch.optim as optim
from torchvision import datasets, transforms
from torch.optim.lr_scheduler import StepLR


class Net(nn.Module):
    def __init__(self):
        super(Net, self).__init__()
        self.conv1 = nn.Conv2d(1, 32, 3, 1)
        self.conv2 = nn.Conv2d(32, 64, 3, 1)
        self.dropout1 = nn.Dropout2d(0.25)
        self.dropout2 = nn.Dropout2d(0.5)
        self.fc1 = nn.Linear(9216, 128)
        self.fc2 = nn.Linear(128, 10)

    def forward(self, x):
        x = self.conv1(x)
        x = F.relu(x)
        x = self.conv2(x)
        x = F.relu(x)
        x = F.max_pool2d(x, 2)
        x = self.dropout1(x)
        x = torch.flatten(x, 1)
        x = self.fc1(x)
        x = F.relu(x)
        x = self.dropout2(x)
        x = self.fc2(x)
        output = F.log_softmax(x, dim=1)
        return output


def train(model, device, train_loader, optimizer, epoch, manager):
    model.train()
    total_loss = 0
    for batch_idx, (data, target) in enumerate(train_loader):
        data, target = data.to(device), target.to(device)
        optimizer.zero_grad()
        output = model(data)
        loss = F.nll_loss(output, target)
        total_loss += loss
        loss.backward()
        optimizer.step()

    avg_loss = (total_loss/len(train_loader)).item()
    print("Epoch %d, loss %.4f" % (epoch, avg_loss))
    manager.add_progress("train_loss", avg_loss)


def test(model, device, test_loader, manager):
    model.eval()
    test_loss = 0
    correct = 0
    with torch.no_grad():
        for data, target in test_loader:
            data, target = data.to(device), target.to(device)
            output = model(data)
            test_loss += F.nll_loss(output, target, reduction='sum').item()  # sum up batch loss
            pred = output.argmax(dim=1, keepdim=True)  # get the index of the max log-probability
            correct += pred.eq(target.view_as(pred)).sum().item()

    test_loss /= len(test_loader.dataset)
    print('\nTest set: Average loss: {:.4f}, Accuracy: {}/{} ({:.0f}%)\n'.format(
        test_loss, correct, len(test_loader.dataset),
        100. * correct / len(test_loader.dataset)))

    manager.add_progress("val_loss", test_loss)
    manager.add_progress("val_accuracy", 100. * correct / len(test_loader.dataset))


def run(manager, param_pth=None, best_param_pth=None):
    hyparams = manager.get_hyparams()

    BATCH_SIZE = hyparams["BATCH_SIZE"]
    EPOCHS = hyparams["EPOCHS"]
    GAMMA = hyparams["GAMMA"]
    LR = hyparams["LR"]
    SAVE_INTERVAL = hyparams["SAVE_INTERVAL"]

    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

    transform=transforms.Compose([
        transforms.ToTensor(),
        transforms.Normalize((0.1307,), (0.3081,))
        ])

    dataset1 = datasets.MNIST('../data', train=True, download=True,
                       transform=transform)
    dataset2 = datasets.MNIST('../data', train=False, download=True,
                       transform=transform)

    train_loader = torch.utils.data.DataLoader(dataset1, batch_size=BATCH_SIZE, shuffle=False, num_workers=4)
    test_loader = torch.utils.data.DataLoader(dataset2, batch_size=BATCH_SIZE, shuffle=False, num_workers=4)

    model = Net().to(device)

    optimizer = optim.Adadelta(model.parameters(), lr=LR)

    scheduler = StepLR(optimizer, step_size=1, gamma=GAMMA)
    start_epoch = manager.start_epoch()
    manager.track_model(model)
    for epoch in range(start_epoch, EPOCHS):
        manager.add_progress("epochs", epoch)
        train(model, device, train_loader, optimizer, epoch, manager)
        test(model, device, test_loader, manager)
        scheduler.step()
        print("Finished one epoch")

        if epoch > 0 and epoch % SAVE_INTERVAL == 0:
            # save progress
            manager.save_progress()

    manager.finished()


if __name__ == '__main__':
    testing = False

    if testing:
        from streamline.manager import TestManager
        manager = TestManager.create_manager({
            "BATCH_SIZE": 64,
            "EPOCHS": 5,
            "GAMMA": 0.7,
            "LR": 1,
            "SAVE_INTERVAL": 2
        })
    else:
        from streamline.manager import Manager
        manager = Manager.create_manager(rank=0, bucket_name='stoked-brand-285120-package')

    manager.hyparam_search(run)
