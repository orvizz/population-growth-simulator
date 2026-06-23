#import "../../../template.typ": user-story

#user-story(
  role:     [registered user],
  want:     [view the ecological analytics computed from my simulation alongside the population trajectory],
  benefit:  [I can understand the long-run behaviour of the population (growth rate, stage composition, sensitivity to vital rates) beyond raw trajectory data],
  priority: "Must",
  points:   [5],
  criteria: (
    [For deterministic simulations: the dominant eigenvalue $lambda_1$, stable stage distribution, reproductive values, sensitivity matrix, and elasticity matrix are displayed.],
    [For stochastic simulations: the stochastic long-run growth rate $lambda_s$, the mean projection matrix, and its elasticities are displayed.],
    [Analytics are shown in the same view as the simulation plot without requiring a separate navigation step.],
  ),
)
