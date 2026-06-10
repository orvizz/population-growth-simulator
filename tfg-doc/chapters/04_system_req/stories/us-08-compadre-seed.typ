#import "../../../template.typ": user-story

#user-story(
  role:     [developer],
  want:     [the COMPADRE plant matrix database to be seeded into the application automatically when the server starts for the first time],
  benefit:  [users have immediate access to thousands of real-world population matrices without any manual data entry],
  priority: "Must",
  points:   [8],
  criteria: (
    [On first container startup the seed script runs automatically and populates the database with COMPADRE matrices.],
    [Subsequent startups detect that seeding was already performed and skip the process.],
    [Seeded matrices are read-only: they are marked with #raw("source_type = \"compadre\"") and cannot be edited or deleted by any user.],
  ),
)
