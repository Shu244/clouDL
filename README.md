## Overview

This package allows you to easily train your model on a cluster of GPU equipped VMs in GCP. 
This package also allows you to visualize the automatically generated reports. 

## Setting up

This package was developed using a Ubuntu 20.04 machine.

First download the Google Cloud SDK following the steps [here](https://cloud.google.com/compute/docs/tutorials/python-guide)
so you can access the Google Cloud Platform tools from the command line and rest API.
Next, install this package using <code>pip install clouDL</code>.

Lastly, to configure your VM cluster, run <code>clouDL_create -r PATH</code>. This will create a folder containing the
necessary configuration files in PATH. 

Some typical next steps (all associated files are in the newly created folder):
1) Create a new <code>access_token</code> file to clone private repos from a VM
2) Update <code>user_startup.sh</code> to specify the bash script you want to execute once a VM is ready
3) Update <code>hyperparameters.json</code> to search the desired hyperparameter space
4) Create a <code>data.tar.zip</code> if you have training, validation, and testing data to move to the cloud
5) Update <code>quick_start.sh</code> if you want to change the number of workers, project_id for GCP, or top N to archive. quick_start.sh
   sets some default values to get you up and running easily, but more control can be accessed by using `clouDL` entrypoint directly. 
   Use <code>clouDL -h</code> for more. 


Make sure to incorporate <code>Manager</code> in your code when training. 

## Using Manager

Manager is essentially the interface you will interact to enable training/hyperparamter tuning on a cluster of VMs. 

Remember to do the following when using Manger:

1) Set the compare and goal keys for Manager using <code>Manager.set_compare_goal(compare, goal)</code>. This will allow Manager to compute the "best" params
2) Start the epochs on the value returned by <code>Manager.start_epochs()</code> method
3) Make sure to call <code>Manager.finished(param_dict)</code> once the model is done training
4) Use <code>Manager.save_progress(param_dict, best_param_dict)</code> sparsely since it is expensive 
5) <code>Manager.save_progress()</code> can be used to track the current params and the best params
6) Use <code>Manager.add_progress(key, value)</code> freely
7) Use <code>Manager.track_model(model)</code> to automatically track the best params and load params when training is 
   interrupted

Progress should be saved at the end of an epoch instead of the beginning. This is not mandatory but prevents unnecessary saving.

The key "epochs" should be used and managed via <code>Manager.add_progress(key, value)</code>. 
If not used, an approximate start epoch will be calculated when resuming training, which relies on existing progress
and epochs starting at 0.

## Manager.py Example

For a complete example, visit [here](https://github.com/Shu244/test_clouDL).

## New Start

From `clouDL_create`, a `quick_start.sh` file is provided with three four modes. The `new` mode
does the following:
1) Move your archived and compressed training data, access token (for VMs to access private repos), and hyperparameter configs to cloud storage
2) Spin up a cluster of VMs, each with hardware specified by the configs.json. 
3) Run the training on VMs which manages four things: progress, results, best models, and errors.
4) Once finish, the VMs will shut down automatically

## Finished Job

The `analyze` mode does the following:
1) View any errors
2) Plot the results grouped by hyperparameter sections
3) Plot the progress for the best model in this iteration
4) Archive results and maintain an overall top N models
5) Plot archive data to view top N best models
6) Plot meta data to track trend of your hyperparameter search

## Resume Hyperparameter Search

Edit your hyperparameter.json file to assign each VM a new portion of the hyperparameter grid. The available search options for a 
given hyperparameter are: 
1) Uniform random search
2) Step search
3) Multipe/exponential search
4) Predetermined List

Then use the `resume` mode from `quick_start.sh` to update hyperparameter json and spin up a new cluster.

## Manual Tests
Execute <code>bash quick_start.sh manual project_id bucket_name</code> to move everything to cloud storage but not spin up a cluster.
This is helpful to run manual tests on the cloud. 

## Extras
An early stopping module is also provided to reduce boiler plate training code. The module can be accessed using

<code>from cloudDL.earlystop import EarlyStopping</code>