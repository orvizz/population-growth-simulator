#import "../../../template.typ": user-story

#user-story(
  role:     [registered user],
  want:     [delete a custom matrix that I no longer need],
  benefit:  [I can keep my personal matrix library organised and free of outdated models],
  priority: "Must",
  points:   [3],
  criteria: (
    [Only the owner can delete a custom matrix.],
    [Deletion is permanent and requires an explicit confirmation step to prevent accidental loss.],
    [Deleting a matrix does not delete simulation runs that referenced it, because snapshots preserve the matrix values independently.],
  ),
)
