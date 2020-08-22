#!/bin/bash

# Note that GOOGLE SDK for the CMD must also be downloaded
# Downloads packages needed for this package
# Original build is for Linux (Ubuntu) machine
# Prerequisites: Anaconda
conda install pytorch torchvision cudatoolkit=10.2 -c pytorch
conda install matplotlib
conda install -c conda-forge google-api-python-client
conda install -c conda-forge google-cloud-storage
