#import "../../../template.typ": user-story

#user-story(
  role:     [registered user],
  want:     [browse my list of saved simulation runs and reload any of them],
  benefit:  [compare different scenarios or revisit a past analysis without redoing the computation],
  priority: "Must",
  points:   [5],
  criteria: (
    [The simulations list shows run name, creation date, type (deterministic or stochastic), and the names of the matrices used.],
    [Opening a saved run restores the population dynamics plot and ecological analytics exactly as they were at the time of saving.],
    [I can permanently delete a run I no longer need from the list.],
  ),
)
