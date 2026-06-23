#import "../../../template.typ": user-story

#user-story(
  role:     [registered user],
  want:     [log out of my current session],
  benefit:  [I can protect my account when using a shared or public device],
  priority: "Must",
  points:   [2],
  criteria: (
    [Clicking "Log out" immediately invalidates the session token and clears it from the browser.],
    [After logout, attempting to access any authenticated endpoint redirects to the login prompt.],
  ),
)
