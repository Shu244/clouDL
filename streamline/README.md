## Using Manager.py

Remember to the following when using Manger:
1) Set the compare and goal keys for Manager using <code>Manager.set_compare_goal(compare, goal)</code>
2) Start the epochs on the value returned by <code>Manager.start_epochs()</code> method
3) Make sure to call <code>Manager.finished(param_dict)</code> once the model is done training
4) Use <code>Manager.save_progress(param_dict)</code> sparsely since it is expensive 
5) Use <code>Manager.add_progress(key, value)</code> freely
6) Load the parameters into the model when it is provided

Progress should be saved at the end of an epoch instead of the beginning
and epochs should start at 0. This is not mandatory but saves unnecessary saving and maintains true epoch value when reloading state.

The starting epoch is calculated by counting the number of elements added to a key using <code>Manager.add_progress(key, value)</code>.
In order to keep track of epochs, the method must be used; otherwise, the starting epoch will be 0 by default when reloading from a state (this will not
throw an error).
