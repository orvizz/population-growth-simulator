# Average Matrix 

We'll have to ways of calculating average matrixes in two different context. 

## Avergae Maatrix for stochastic simulations

Computing an average matrix for an stochastic simulation will provide a lot of value to our application. We first need to define how the simulations are performed, and what concept of average matrix are we talking about. 

How stochastic simulations are performed?

First, we start with a set $A$ of $N$ matrixes where $N >= 2$. All the matrixes in that specific set must have the same dimensions, so all matrixes have dimensions $m * m$. This vector can be defined as:

$$
\{A_{1}, A_{2}, ... , A_{n}\} \subset R^{m * m}
$$

Then, we pick up matrixes at random to multiply a vector $V$. We do this process $T$ times. 
This means, that each matrix will have a **frequency**, or how many times has that concrete matrix been selected. Then, we'll have a vector $F$ of size $N$ in which each $F_{n}$ represents how many times the matrix $A_{n}$ has been selected.

Therefore, we can ensure that $\sum_{k=1}^{N}F_{k} = T$. And finally, with this information, que can define the final average matrix as:

$$
\overline{A}_t = \frac{1}{T}\sum_{k=1}^{N}F_{k}*A_{k}
$$


This average matrix must be shown in the "Simulation" screen, when a simulation is performed.

## Average Matrix for quasi-extinction simulations

Quasi-extinction simulations consist on running several normal simulations (deterministic or stochastic) and find in what percentage of situations a population ends up extinct or not. In this case, we'll prefer a deterministic matrix instead of an stochastic one. This amtrix will be simply computed as (starting for the same foundation as previously):

$$
\overline{A} = \frac{1}{N}\sum_{k=1}^{N}A_{k}
$$

This amtrix will be sown in at the top-right corner of the quasi-extinction visualization.