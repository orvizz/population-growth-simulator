#import "../../../template.typ": user-story

#user-story(
  role:     [registered user],
  want:     [run a stochastic simulation by selecting two or more population matrices of the same dimension],
  benefit:  [model population dynamics under environmental variability, where each of N independent runs commits to one randomly-chosen environment (matrix) for its full duration, enabling ensemble-based population forecasting],
  priority: "Must",
  points:   [8],
  criteria: (
    [I can select two or more matrices of the same dimension; the system validates that all dimensions match.],
    [The system executes $N$ independent runs (10–1 000, default 100); each run commits to one randomly-chosen matrix and applies $bold(v)(t+1) = bold(A)_i dot.op bold(v)(t)$ for all $T$ steps with the same $bold(A)_i$ throughout.],
    [I can provide a random seed to make the simulation reproducible.],
    [The result shows the mean population trajectory per stage with a shaded min/max band representing ensemble spread; I can also set the number of runs (10–1 000, default 100).],
  ),
)
