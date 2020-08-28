## Using Manager.py

Remember to the following when using Manger:
1) Set the compare and goal keys for Manager using <code>Manager.set_compare_goal(compare, goal)</code>
2) Start the epochs on the value returned by <code>Manager.start_epochs()</code> method
3) Make sure to call <code>Manager.finished(param_dict)</code> once the model is done training
4) Use <code>Manager.save_progress(param_dict)</code> sparsely since it is expensive 
5) Use <code>Manager.add_progress(key, value)</code> freely
6) Load the parameters into the model when it is provided

Progress should be saved at the end of an epoch instead of the beginning. This is not mandatory but prevents unnecessary saving.

The key "epochs" should be used and managed via <code>Manager.add_progress(key, value)</code>. This will help
restarts start on the proper epoch. If not used, an approximate start epoch will be calculated, which relies on existing progress
and epochs starting at 0.
