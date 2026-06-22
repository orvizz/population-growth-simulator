#import "../../../template.typ": user-story

#user-story(
  role:     [user],
  want:     [select my preferred display language from the application header],
  benefit:  [I can use the interface in my native language and have that preference preserved across sessions],
  priority: "Should",
  points:   [3],
  criteria: (
    [A language selector is visible in the application header on every tab, regardless of authentication state.],
    [Selecting a language updates all labels, buttons, and messages immediately without a page reload.],
    [The selected language is persisted in the browser so it is restored on the next visit.],
    [Supported languages: English, Spanish (Español), Asturian (Asturianu), Galician (Galego), Basque (Euskara), and Catalan (Català).],
  ),
)
