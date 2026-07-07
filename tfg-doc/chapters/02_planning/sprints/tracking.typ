// chapters/02_planning/sprints/tracking.typ
#import "../../../template.typ": sp

This section tracks what actually happened against the plan laid out in @tab:sprints.
Three baselines are used to judge progress:

- *Initial baseline*: The WBS estimate at project start: 203 pts spread across 44 tasks
  in 6 sprints (@tab:sprints), of which 122 pts trace directly to the 24 user stories in
  @sec:stories and the remainder covers setup, architecture, DevOps, and documentation
  work.
- *Mid-project baseline*: Checkpoint at the end of #sp(2) (Mar 28, 2026): 100 of the
  203 planned points were complete (~49%), broadly on track with the cumulative ideal
  line in @fig:burndown, with #sp(3) already showing the widest actual/ideal gap due to
  its much longer (~5.5-week) period.
- *Final baseline*: End of #sp(5) (Jun 9, 2026): all 203 points were completed; every
  sprint's actual line in @fig:burndown reaches zero by its period end.

#let _ttable(cap, rows) = figure(
  table(
    columns: (auto, auto, auto, auto),
    stroke: 0.5pt + luma(200),
    align: (center + horizon, center + horizon, center + horizon, center + horizon),
    inset: (x: 8pt, y: 6pt),
    fill: (_, y) => if y == 0 { luma(232) } else if calc.odd(y) { luma(250) } else { white },
    table.header([*Task*], [*Start*], [*End*], [*Status*]),
    ..rows
  ),
  caption: cap,
)

==== Sprint 0

#_ttable([Sprint 0 actual tracking], (
  link(label("task:s0-01"))[S0-01], [Feb 11, 2026], [Feb 15, 2026], [Done],
  link(label("task:s0-02"))[S0-02], [Feb 14, 2026], [Feb 18, 2026], [Done],
  link(label("task:s0-03"))[S0-03], [Feb 17, 2026], [Feb 21, 2026], [Done],
  link(label("task:s0-04"))[S0-04], [Feb 20, 2026], [Feb 24, 2026], [Done],
  link(label("task:s0-05"))[S0-05], [Feb 23, 2026], [Feb 27, 2026], [Done],
  link(label("task:s0-06"))[S0-06], [Feb 26, 2026], [Feb 28, 2026], [Done],
)) <tab:tracking-s0>

#figure(
  image("../../../resources/diagrams/burndown-s0.svg", width: 70%),
  caption: [Sprint 0 burndown: ideal vs. actual],
) <fig:burndown-s0>

==== Sprint 1

#_ttable([Sprint 1 actual tracking], (
  link(label("task:s1-01"))[S1-01], [Mar 1, 2026], [Mar 4, 2026], [Done],
  link(label("task:s1-02"))[S1-02], [Mar 3, 2026], [Mar 6, 2026], [Done],
  link(label("task:s1-03"))[S1-03], [Mar 5, 2026], [Mar 8, 2026], [Done],
  link(label("task:s1-04"))[S1-04], [Mar 7, 2026], [Mar 10, 2026], [Done],
  link(label("task:s1-05"))[S1-05], [Mar 9, 2026], [Mar 12, 2026], [Done],
  link(label("task:s1-06"))[S1-06], [Mar 11, 2026], [Mar 14, 2026], [Done],
  link(label("task:s1-07"))[S1-07], [Mar 13, 2026], [Mar 14, 2026], [Done],
)) <tab:tracking-s1>

#figure(
  image("../../../resources/diagrams/burndown-s1.svg", width: 70%),
  caption: [Sprint 1 burndown: ideal vs. actual],
) <fig:burndown-s1>

==== Sprint 2

#_ttable([Sprint 2 actual tracking], (
  link(label("task:s2-01"))[S2-01], [Mar 15, 2026], [Mar 18, 2026], [Done],
  link(label("task:s2-02"))[S2-02], [Mar 17, 2026], [Mar 20, 2026], [Done],
  link(label("task:s2-03"))[S2-03], [Mar 19, 2026], [Mar 22, 2026], [Done],
  link(label("task:s2-04"))[S2-04], [Mar 21, 2026], [Mar 24, 2026], [Done],
  link(label("task:s2-05"))[S2-05], [Mar 23, 2026], [Mar 26, 2026], [Done],
  link(label("task:s2-06"))[S2-06], [Mar 25, 2026], [Mar 28, 2026], [Done],
  link(label("task:s2-07"))[S2-07], [Mar 27, 2026], [Mar 28, 2026], [Done],
)) <tab:tracking-s2>

#figure(
  image("../../../resources/diagrams/burndown-s2.svg", width: 70%),
  caption: [Sprint 2 burndown: ideal vs. actual],
) <fig:burndown-s2>

==== Sprint 3

#_ttable([Sprint 3 actual tracking], (
  link(label("task:s3-01"))[S3-01], [Mar 29, 2026], [Apr 6, 2026], [Done],
  link(label("task:s3-02"))[S3-02], [Apr 3, 2026], [Apr 12, 2026], [Done],
  link(label("task:s3-03"))[S3-03], [Apr 9, 2026], [Apr 18, 2026], [Done],
  link(label("task:s3-04"))[S3-04], [Apr 15, 2026], [Apr 24, 2026], [Done],
  link(label("task:s3-05"))[S3-05], [Apr 21, 2026], [Apr 30, 2026], [Done],
  link(label("task:s3-06"))[S3-06], [Apr 27, 2026], [May 6, 2026], [Done],
  link(label("task:s3-07"))[S3-07], [May 3, 2026], [May 8, 2026], [Done],
)) <tab:tracking-s3>

#figure(
  image("../../../resources/diagrams/burndown-s3.svg", width: 70%),
  caption: [Sprint 3 burndown: ideal vs. actual],
) <fig:burndown-s3>

==== Sprint 4

#_ttable([Sprint 4 actual tracking], (
  link(label("task:s4-01"))[S4-01], [May 9, 2026], [May 12, 2026], [Done],
  link(label("task:s4-02"))[S4-02], [May 11, 2026], [May 14, 2026], [Done],
  link(label("task:s4-03"))[S4-03], [May 13, 2026], [May 16, 2026], [Done],
  link(label("task:s4-04"))[S4-04], [May 15, 2026], [May 19, 2026], [Done],
  link(label("task:s4-05"))[S4-05], [May 18, 2026], [May 21, 2026], [Done],
  link(label("task:s4-06"))[S4-06], [May 20, 2026], [May 23, 2026], [Done],
  link(label("task:s4-07"))[S4-07], [May 22, 2026], [May 25, 2026], [Done],
  link(label("task:s4-08"))[S4-08], [May 24, 2026], [May 26, 2026], [Done],
)) <tab:tracking-s4>

#figure(
  image("../../../resources/diagrams/burndown-s4.svg", width: 70%),
  caption: [Sprint 4 burndown: ideal vs. actual],
) <fig:burndown-s4>

==== Sprint 5

#_ttable([Sprint 5 actual tracking], (
  link(label("task:s5-01"))[S5-01], [May 27, 2026], [May 29, 2026], [Done],
  link(label("task:s5-02"))[S5-02], [May 28, 2026], [May 30, 2026], [Done],
  link(label("task:s5-03"))[S5-03], [May 30, 2026], [Jun 1, 2026], [Done],
  link(label("task:s5-04"))[S5-04], [May 31, 2026], [Jun 3, 2026], [Done],
  link(label("task:s5-05"))[S5-05], [Jun 2, 2026], [Jun 4, 2026], [Done],
  link(label("task:s5-06"))[S5-06], [Jun 3, 2026], [Jun 6, 2026], [Done],
  link(label("task:s5-07"))[S5-07], [Jun 5, 2026], [Jun 7, 2026], [Done],
  link(label("task:s5-08"))[S5-08], [Jun 6, 2026], [Jun 9, 2026], [Done],
  link(label("task:s5-09"))[S5-09], [Jun 8, 2026], [Jun 9, 2026], [Done],
)) <tab:tracking-s5>

#figure(
  image("../../../resources/diagrams/burndown-s5.svg", width: 70%),
  caption: [Sprint 5 burndown: ideal vs. actual],
) <fig:burndown-s5>

==== Burndown

The chart below combines all six sprints into a single project timeline. Each sprint's
date range is shaded with a distinct light background colour, matching the order in
which the sprints appear in @tab:sprints.

#figure(
  image("../../../resources/diagrams/burndown-global.svg", width: 100%),
  caption: [Project burndown (Sprint 0 to Sprint 5): ideal vs. actual remaining points, shaded by sprint],
) <fig:burndown>
