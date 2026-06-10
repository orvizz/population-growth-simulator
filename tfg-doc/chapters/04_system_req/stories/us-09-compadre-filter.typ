#import "../../../template.typ": user-story

#user-story(
  role:     [researcher],
  want:     [filter the matrix catalog by taxonomic and ecological metadata such as kingdom, country, and species name],
  benefit:  [efficiently narrow down the matrices relevant to a comparative demographic analysis without manual inspection],
  priority: "Must",
  points:   [5],
  criteria: (
    [Filtering by kingdom (e.g., Plantae, Animalia) shows only matrices from that taxonomic group.],
    [Filtering by country shows only matrices collected in that geographic region.],
    [Multiple filters applied at the same time narrow the results as AND conditions.],
  ),
)
