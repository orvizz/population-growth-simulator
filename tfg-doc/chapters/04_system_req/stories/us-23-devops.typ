#import "../../../template.typ": user-story

#user-story(
  role:     [developer],
  want:     [an automated CI pipeline to run the full test suite and security scans on every commit and pull request],
  benefit:  [I can detect regressions immediately and prevent code with known vulnerabilities or failing tests from being merged into the main branch],
  priority: "Must",
  points:   [5],
  criteria: (
    [Unit tests (no database required) run first on every push; a failure blocks the pipeline immediately.],
    [Integration tests run against a live PostgreSQL service container after migrations are applied.],
    [Static security analysis (Bandit) and dependency vulnerability scanning (pip-audit) execute as part of the same pipeline run.],
    [A high-severity security finding or any failing test blocks the pull-request merge.],
  ),
)
