#import "../../../template.typ": user-story

#user-story(
  role:     [registered user],
  want:     [run a deterministic simulation by selecting a single population matrix and specifying an initial population vector],
  benefit:  [project population dynamics over time under a constant-environment assumption and observe the long-run trajectory],
  priority: "Must",
  points:   [8],
  criteria: (
    [I can select any matrix I have access to (COMPADRE or custom) as the simulation input.],
    [I enter the initial population vector (one non-negative value per stage) and the number of time steps (1–1000).],
    [The system computes the trajectory using the recurrence $bold(v)(t+1) = bold(A) dot.op bold(v)(t)$.],
    [A line plot showing population size per stage over time is displayed upon completion.],
  ),
)
