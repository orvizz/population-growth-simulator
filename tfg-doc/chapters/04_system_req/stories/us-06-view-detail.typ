#import "../../../template.typ": user-story

#user-story(
  role:     [visitor],
  want:     [view the full details of a population matrix],
  benefit:  [I can inspect the matrix entries and metadata before deciding to use it in a simulation],
  priority: "Must",
  points:   [3],
  criteria: (
    [The detail view shows the projection matrix A, survival matrix U, and fertility matrix F as readable grids.],
    [Stage names are displayed as row and column labels on each matrix grid.],
    [Ecological metadata (species, kingdom, country, study duration) is shown alongside the matrices.],
    [A cyclic graph is shown as a graphical representation of the matrix]
  ),
)
