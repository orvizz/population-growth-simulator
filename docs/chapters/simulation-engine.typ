= Simulation Engine <simulation-engine>

== Mathematical Background

The simulator is built on the theory of *stage-structured population models*,
also known as matrix population models @caswell2001. In this framework a
population is partitioned into discrete _stages_ (e.g. seedling, juvenile,
adult) and its state at any time $t$ is represented as a column vector
$bold(v)(t) in RR^n$, where $n$ is the number of stages and each entry
$v_i(t)$ is the abundance of individuals in stage $i$.

The dynamics are governed by a *population projection matrix*
$bold(A) in RR^(n times n)$, where entry $a_(i j)$ encodes the expected
contribution of an individual in stage $j$ to stage $i$ over one time step
(one year in most COMPADRE matrices). The projection rule is:

$ bold(v)(t+1) = bold(A) bold(v)(t) $

Iterating this rule for $T$ steps produces the *trajectory*:

$ { bold(v)(0),, bold(v)(1),, dots.h,, bold(v)(T) } $

This trajectory is what the system stores as `result_history`.

== Deterministic Simulation

A deterministic simulation uses a single fixed matrix $bold(A)$ for every time
step. Given an initial vector $bold(v)(0)$ and a number of steps $T$, the
algorithm is:

```python
A = np.array(matrix_a, dtype=float)  # None cells → 0.0
v = np.array(initial_vector, dtype=float)
history = [v.tolist()]
for _ in range(n_steps):
    v = A @ v
    history.append(v.tolist())
```

The resulting `history` list has length $T + 1$ (one entry per time point,
including $t = 0$).

The matrix $bold(A)$ may contain `null` cells, which arise in COMPADRE data
when certain vital rates were not measured. These are converted to `0.0`
before the computation, treating unmeasured transitions as absent.

== Stochastic Simulation

A stochastic simulation models *environmental stochasticity* by providing a
set of $k >= 2$ matrices ${ bold(A)_1, bold(A)_2, dots.h, bold(A)_k }$,
each representing the population dynamics under a different environmental
scenario (e.g. a good year vs. a bad year). At each time step one matrix is
selected uniformly at random and applied:

$ bold(v)(t+1) = bold(A)_(i_t) bold(v)(t), quad i_t tilde.op "Uniform"({1, dots.h, k}) $

The algorithm is:

```python
rng = np.random.default_rng(random_seed)
arrays = [np.array(m, dtype=float) for m in matrices]
v = np.array(initial_vector, dtype=float)
history = [v.tolist()]
for _ in range(n_steps):
    A = arrays[rng.integers(len(arrays))]
    v = A @ v
    history.append(v.tolist())
```

Using `numpy.random.default_rng` (the modern NumPy Generator API) instead of
the legacy `numpy.random` module provides statistically independent, reproducible
streams. When `random_seed` is provided, the same seed always produces the same
trajectory, enabling exact reproduction of past runs. When `random_seed` is
`None`, a random seed is drawn from the OS entropy source.

All matrices in a stochastic run must share the same dimension $n$; this is
validated by the service layer before the algorithm runs.

== Validation

The service layer performs the following checks before invoking either algorithm.

+ *Matrix existence* — every referenced matrix id must exist in the database.
  Missing matrices return `404 Not Found`.
+ *Matrix data presence* — `matrix_a` must not be null. A matrix with no
  projection data cannot be simulated. Returns `400 Bad Request`.
+ *Dimension consistency (stochastic only)* — all matrices in `matrix_ids`
  must have the same $n$. Mismatched dimensions return `400 Bad Request` with a
  message listing the conflicting dimensions.
+ *Vector dimension match* — `len(initial_vector)` must equal $n$. A mismatch
  returns `400 Bad Request` with the expected and actual sizes.

== Ephemeral vs. Stored Runs

`SimulationService` exposes two entry points for running a simulation.

`run_ephemeral` computes the trajectory and returns it directly without writing
anything to the database. It is called by `POST /v1/simulations/run`.

`run` computes the trajectory and then calls `SimulationRepository.create` to
persist the full result. It is called by `POST /v1/simulations`.

The algorithm is identical in both cases — only the persistence step differs.

== Key Properties

*Determinism.* Given the same matrix, initial vector, number of steps (and seed
for stochastic runs), the algorithm always produces the same trajectory. This
is guaranteed by NumPy's BLAS routines for the deterministic path and by
`default_rng` for the stochastic path.

*Performance.* Each projection step is a single BLAS Level-2 matrix-vector
product. For the matrix sizes present in the COMPADRE dataset (typically
$n <= 20$) this is computed in microseconds. Even with $T = 1000$ steps the
computation is negligible compared to network and I/O latency.

*None handling.* `_to_array` converts every `None` cell to `0.0` before
constructing the NumPy array. This makes the engine robust to incomplete
COMPADRE entries without requiring callers to pre-process the matrix data.
