#import "../../../template.typ": user-story

#user-story(
  role:     [registered user],
  want:     [export a population matrix to a JSON or CSV file],
  benefit:  [use the matrix data in external tools or archive it for my own records],
  priority: "Should",
  points:   [3],
  criteria: (
    [JSON export includes the full matrix data (A, U, F), stage names, and all metadata fields.],
    [CSV export produces a tidy grid of the A-matrix values with stage names as row and column headers.],
    [The exported file downloads automatically in the browser without requiring a separate step.],
  ),
)
