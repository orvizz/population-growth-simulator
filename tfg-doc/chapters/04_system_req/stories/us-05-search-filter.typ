#import "../../../template.typ": user-story

#user-story(
  role:     [visitor],
  want:     [search and filter the matrix catalog by species name, taxonomic kingdom, and country of origin],
  benefit:  [quickly find matrices relevant to my study species without manually scrolling through thousands of entries],
  priority: "Must",
  points:   [5],
  criteria: (
    [Text search matches against species name and common name (case-insensitive, partial match).],
    [Kingdom and country dropdowns act as AND conditions when both are selected.],
    [Applying a filter updates the results immediately without a full page reload.],
    [A clear "no results" message appears when the query returns an empty set.],
  ),
)
