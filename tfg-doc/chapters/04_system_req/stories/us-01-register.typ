#import "../../../template.typ": user-story

#user-story(
  role:     [visitor],
  want:     [register a new account with a username, email address, and password],
  benefit:  [I can access features reserved for registered users, such as saving simulations and managing custom matrices],
  priority: "Must",
  points:   [5],
  criteria: (
    [The system accepts a unique username, a unique and valid-format email address, and a password of at least 8 characters with numbers and letters.],
    [Attempting to register with an already-used email or username returns a descriptive error message.],
    [After successful registration, the user can immediately log in with the new credentials.],
  ),
)
