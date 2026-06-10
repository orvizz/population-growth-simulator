#import "../../../template.typ": user-story

#user-story(
  role:     [visitor],
  want:     [browse a paginated catalog of population matrices],
  benefit:  [discover available matrices for my research without needing an account],
  priority: "Must",
  points:   [3],
  criteria: (
    [The catalog is visible without authentication.],
    [Each entry shows the species name, source (COMPADRE or custom), and matrix dimension.],
    [The list is paginated so that the page loads in under two seconds even with thousands of entries.],
  ),
)
