# Overview
The files here allow users an intuitive way to manage deploying your model to GCP.

## configs.json
This file allows you to easily configure the hardware for the VMs. 

## hyperparameter.json
This file allows you to easily control which hyperparameter section each VM will search.

## user_startup.sh
This is the script that will run in the VMs.

## quick_start.sh
This wraps all the functionality of the package in one location, but should be customized for personal use. 

## access_token
This file should contain the personal access token for your private repo. This allows the VMs to clone your private repo.
This is not required if your repo is public.

## data.tar.zip
This is an archived and compressed file of your training,validation, and test data. This file is not automatically 
created for you, but once it has been created, you can pass it as a command line argument to clouDL. 

## File Structure in VM

The current working directory contains a `data` folder. The 
`data` folder contains your uncompressed and extracted data and your access_token if provided. 
