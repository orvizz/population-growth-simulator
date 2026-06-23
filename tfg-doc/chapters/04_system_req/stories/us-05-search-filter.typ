#import "../../../template.typ": user-story

#user-story(
  role:     [visitor],
  want:     [search and filter the matrix catalog by species name, taxonomic kingdom, and country of origin],
  benefit:  [I'm able to quickly find matrices relevant to my study species without manually scrolling through thousands of entries],
  priority: "Must",
  points:   [5],
  criteria: (
    [Text search matches against species name and common name (case-insensitive, partial match).],
    [All filters act as an AND filter.],
    [A clear "no results" message appears when the query returns an empty set.],
  ),
)
