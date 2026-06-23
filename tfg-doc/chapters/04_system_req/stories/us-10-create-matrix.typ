#import "../../../template.typ": user-story

#user-story(
  role:     [registered user],
  want:     [create my own population matrix by specifying stage names and entering the cell values],
  benefit:  [I can model populations not covered by COMPADRE or test hypothetical demographic scenarios],
  priority: "Must",
  points:   [8],
  criteria: (
    [I can choose the matrix dimension n (n ≥ 2) and enter each cell of the A (projection) matrix.],
    [I can optionally provide the U (survival) and F (fertility) sub-matrices.],
    [I can name each life-history stage and add optional metadata (species, country, etc.).],
    [The matrix is saved to my account and immediately available for simulation.],
  ),
)
