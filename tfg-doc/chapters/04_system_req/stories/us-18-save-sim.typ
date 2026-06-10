#import "../../../template.typ": user-story

#user-story(
  role:     [registered user],
  want:     [save a completed simulation run to my account with a descriptive name],
  benefit:  [retrieve and compare past results at any time without re-running the computation],
  priority: "Must",
  points:   [5],
  criteria: (
    [I can name the simulation before or after running it.],
    [The saved run stores an immutable snapshot of the matrix values used, so future edits to the source matrix do not affect the stored result.],
    [The saved run appears in my simulations list immediately after saving.],
  ),
)
