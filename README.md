## Overview

This package allows you to easily train your model on a cluster of GPU equipped VMs in GCP. 
This package also allows you to visualize the automatically generated reports. 

## Setting up

This package was developed using a Ubuntu 20.04 machine.

First download the Google Cloud SDK following the steps [here](https://cloud.google.com/compute/docs/tutorials/python-guide).
Next, activate your desired virtual conda environment. Download the zip for this repo and extract it to the desired folder.
Then run <code>bash setup.sh</code>.


Some typical next steps (all associated files are in the <code>user_files</code> folder):
1) Create a new <code>access_token</code> file to clone private repos from a VM
2) Update <code>startup.sh</code> to at least clone your new repo
3) Update <code>hyperparameters.json</code> to search the desired hyperparameter space
4) Create a <code>data.tar.zip</code> if you have training data to move to the cloud
5) Update <code>quick_start.sh</code> if you want to change the number of workers, project_id for GCP, or top N to archive.

Make sure to incorporate <code>manager.py</code> in your code!

## Using Manager.py

Remember to do the following when using Manger:
1) Set the compare and goal keys for Manager using <code>Manager.set_compare_goal(compare, goal)</code>. This will allow Manager to compute the "best" params
2) Start the epochs on the value returned by <code>Manager.start_epochs()</code> method
3) Make sure to call <code>Manager.finished(param_dict)</code> once the model is done training
4) Use <code>Manager.save_progress(param_dict, best_param_dict)</code> sparsely since it is expensive 
5) <code>Manager.save_progress(param_dict, best_param_dict)</code> can be used to track the current params and the optional best params
6) Use <code>Manager.add_progress(key, value)</code> freely
7) Use <code>Manager.track_model(model)</code> to automatically track the best params and obtain params when saving progress

Progress should be saved at the end of an epoch instead of the beginning. This is not mandatory but prevents unnecessary saving.

The key "epochs" should be used and managed via <code>Manager.add_progress(key, value)</code>. This will help
restarts start on the proper epoch. If not used, an approximate start epoch will be calculated, which relies on existing progress
and epochs starting at 0.

## Manager.py Example
Import the manager module:
<pre>
if testing:
    from GCP_AI.manager import TestManager
    manager = TestManager.create_manager(hyparams_dict)
else:
    from GCP_AI.manager import Manager
    manager = Manager.create_manager()
</pre>

Pass your run function to manager:

<pre>
manager.hyparam_search(run_func)
</pre>

The run function will receive an instance of the manager object, paths for the current model params and
paths for the best model params.

Your run function should make use of the manager. An example of using manager:

<pre>
hyparams = manager.get_hyparams()

BATCH_SIZE = hyparams["BATCH_SIZE"]
EPOCHS = hyparams["EPOCHS"]
GAMMA = hyparams["GAMMA"]
LR = hyparams["LR"]
SAVE_INTERVAL = hyparams["SAVE_INTERVAL"]

...

start_epoch = manager.start_epoch()
manager.track_model(model)
for epoch in range(start_epoch, EPOCHS):
    manager.add_progress("epochs", epoch)
    train(model, device, train_loader, optimizer, epoch, manager)
    test(model, device, test_loader, manager)
    scheduler.step()

    if epoch > 0 and epoch % SAVE_INTERVAL == 0:
        manager.save_progress()

manager.finished()
</pre>

For a complete example, visit [here](https://github.com/Shu244/test_gcp_ai).

## New Start for GCP

Execute <code>bash quick_start.sh new bucket_name</code> to do the following:
1) Move your archived and compressed training data, access token (for VMs to access private repos), and hyperparameter configs to cloud storage
2) Spin up a cluster of VMs, each with hardware specified by the configs.json. 
3) Run the training on VMs which manages four things: progress, results, best models, and errors.
4) Once finish, the VMs will shut down automatically

## Finished GCP Job

Execute <code>bash quick_start.sh analyze bucket_name</code> to do the following:
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

Then execute <code>bash quick_start.sh resume bucket_name</code> to update hyperparameter json and spin up a new cluster.

## Manual Tests:
Execute <code>bash quick_start.sh manual bucket_name</code> to move everything to cloud storage but not spin up a cluster.
This is helpful to run manual tests. 
