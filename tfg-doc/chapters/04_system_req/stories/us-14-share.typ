#import "../../../template.typ": user-story

#user-story(
  role:     [registered user],
  want:     [share my custom matrix with specific other registered users by entering their username],
  benefit:  [collaborate on demographic modelling with colleagues without making the matrix fully public],
  priority: "Could",
  points:   [5],
  criteria: (
    [The owner can add a user to the share list by entering their exact username.],
    [Shared users can view and use (but not edit or delete) the matrix.],
    [The owner can revoke access for any shared user at any time.],
  ),
)
