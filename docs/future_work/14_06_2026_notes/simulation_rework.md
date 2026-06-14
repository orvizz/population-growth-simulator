# Stochastic simulation rework

Deterministic simulations are good at they are, but we need to rework stochastic simulations.


# Actual situation

Stochastic simulations are performed with N matrices of the same size. 
Each simulation has T iterations (like time steps). We have a vector v of one dimension compatible with the matrix. In each iteration (each time step), we choose randomly one matrix and use it to multiply the vector.


# Reworked version

Now, we add a new component for the simulation itself, the number of times that we're going to repeat it. Instead of doing 1 run choosing matrix randomly each step, now we're going to execute X runs, and we're going to choose the matrix beforethe run, and use that matrix for the entire run. The result of the simulation will be the same graph as now, but the values are the mean of the result of all the simulations for that specific step. We then should also show the variance and the minimum and maximum value for that time step.

This rework applies as well for the quasi-extinction part, that is already implemented like that but we need to change the part where we pick one matrix at each step and configure it to commit to a matrix for an entire run.
