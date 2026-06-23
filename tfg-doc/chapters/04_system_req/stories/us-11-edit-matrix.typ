#import "../../../template.typ": user-story

#user-story(
  role:     [registered user],
  want:     [edit the cell values and metadata (species, common name, kingdom, country, stage names) of a custom matrix I own],
  benefit:  [I can correct mistakes or update the demographic model as new field data becomes available],
  priority: "Must",
  points:   [5],
  criteria: (
    [Only the owner of a custom matrix may edit it; other users receive a permission error.],
    [Editing a matrix does not retroactively alter any saved simulation runs that referenced it, because matrix values are captured in an immutable snapshot at run time.],
    [Changes are persisted immediately and apply to all future simulations using that matrix.],
  ),
)
