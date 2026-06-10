#import "../../../template.typ": user-story

#user-story(
  role:     [registered user],
  want:     [log in with my email address and password],
  benefit:  [access my simulations, custom matrices, and other personalised content],
  priority: "Must",
  points:   [5],
  criteria: (
    [The system accepts a valid email and password combination and issues a session token.],
    [Invalid credentials return a generic error that does not reveal which field is wrong.],
    [A successful login establishes a session that persists across page reloads.],
  ),
)
