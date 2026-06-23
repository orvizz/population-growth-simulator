#import "../../../template.typ": user-story

#user-story(
  role:     [registered user],
  want:     [set the visibility of my custom matrix to private, shared, or public],
  benefit:  [I can control who can see and use my matrix, keeping experimental work private or making finished models available to the community],
  priority: "Should",
  points:   [5],
  criteria: (
    [*Private*: only the owner can see and use the matrix.],
    [*Shared*: only users the owner has explicitly added to the share list can access it.],
    [*Public*: any visitor can view and use the matrix, regardless of authentication.],
    [The owner can change the visibility setting at any time without affecting existing simulation snapshots.],
  ),
)
