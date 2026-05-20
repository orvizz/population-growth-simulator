// chapters/04_system_req/stories/us-01-example.typ
#import "/template.typ": user-story

#user-story(
  role:     [registered user],
  want:     [log in with my email and password],
  benefit:  [access my personalized content],
  priority: "Must",
  points:   [5],
  criteria: (
    [The system accepts valid email and password combinations.],
    [Invalid credentials show a generic error without revealing which field failed.],
    [A successful login redirects the user to their dashboard.],
  ),
)
