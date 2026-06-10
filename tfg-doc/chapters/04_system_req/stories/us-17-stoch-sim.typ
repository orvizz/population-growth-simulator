#import "../../../template.typ": user-story

#user-story(
  role:     [registered user],
  want:     [run a stochastic simulation by selecting two or more population matrices of the same dimension],
  benefit:  [model population dynamics under environmental variability, where the environment switches randomly between states at each time step],
  priority: "Must",
  points:   [8],
  criteria: (
    [I can select two or more matrices of the same dimension; the system validates that all dimensions match.],
    [At each time step, one matrix is selected uniformly at random: $bold(v)(t+1) = bold(A)_i dot.op bold(v)(t)$.],
    [I can provide a random seed to make the simulation reproducible.],
    [The stochastic population trajectory is plotted with one line per stage.],
  ),
)
