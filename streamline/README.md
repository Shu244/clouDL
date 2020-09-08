# Overview
Below are following options to run this repo.

## New Start
Execute <code>bash quick_start.sh new bucket_name</code> to do the following:
1) Move your archived and compressed training data, access token (for VMs to access private repos), and hyperparameter configs to cloud storage
2) Spin up a cluster of VMs, each with hardware specified by the configs.json. 
3) Run the training on VMs which manages four things: progress, results, best models, and errors.
4) Once finish, the VMs will shut down automatically

## Job Finished
Execute <code>bash quick_start.sh analyze bucket_name</code> to do the following:
1) View any errors
2) Plot the results grouped by hyperparameter sections
3) Plot the progress for the best model in this iteration
4) Archive results and maintain an overall top N models
5) Plot archive data to view top N best models
6) Plot meta data to track trend of your hyperparameter search

## Resume Job
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


# Using Manager.py

Remember to the following when using Manger:
1) Set the compare and goal keys for Manager using <code>Manager.set_compare_goal(compare, goal)</code>
2) Start the epochs on the value returned by <code>Manager.start_epochs()</code> method
3) Make sure to call <code>Manager.finished(param_dict)</code> once the model is done training
4) Use <code>Manager.save_progress(param_dict, best_param_dict)</code> sparsely since it is expensive 
5) <code>Manager.save_progress(param_dict, best_param_dict)</code> can be used to track the current params and the optional best params
6) Use <code>Manager.add_progress(key, value)</code> freely
7) Load the parameters into the model when it is provided

Progress should be saved at the end of an epoch instead of the beginning. This is not mandatory but prevents unnecessary saving.

The key "epochs" should be used and managed via <code>Manager.add_progress(key, value)</code>. This will help
restarts start on the proper epoch. If not used, an approximate start epoch will be calculated, which relies on existing progress
and epochs starting at 0.
