#!/bin/bash

# Downloads packages needed for this package
# Original built for Linux (Ubuntu) device
# Prerequisites: Anaconda
conda install pytorch torchvision cudatoolkit=10.2 -c pytorch
conda install matplotlib