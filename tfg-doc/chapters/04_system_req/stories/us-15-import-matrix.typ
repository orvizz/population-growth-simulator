#import "../../../template.typ": user-story

#user-story(
  role:     [registered user],
  want:     [import one or more population matrices from a JSON or ZIP file],
  benefit:  [I can restore previously exported matrices or bulk-load a collection of matrices prepared offline without re-entering data manually],
  priority: "Should",
  points:   [5],
  criteria: (
    [A single JSON file imports exactly one matrix.],
    [A ZIP archive can contain multiple JSON files and imports them all in a single operation.],
    [After the import, a summary report shows how many matrices were successfully imported and lists any failures with a reason.],
  ),
)
