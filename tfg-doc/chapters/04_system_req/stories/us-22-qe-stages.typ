#import "../../../template.typ": user-story

#user-story(
  role:     [registered user],
  want:     [configure per-stage exclusions and minimum thresholds before running a quasi-extinction analysis],
  benefit:  [I can focus the extinction criterion on ecologically relevant life stages (e.g., reproductive adults only) and ignore juvenile stages that naturally fluctuate near zero],
  priority: "Should",
  points:   [5],
  criteria: (
    [I can assign a minimum abundance threshold to each life-history stage independently.],
    [I can exclude specific stages from the extinction check entirely.],
    [The configuration is validated before job submission: at least one stage must be included in the check.],
  ),
)
