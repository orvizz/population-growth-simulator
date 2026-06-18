// chapters/02_planning/traceability.typ

@tab:traceability maps every user story from @sec:stories to the sprint(s) and task(s) in
@tab:sprints that implemented it. The mapping is not one-to-one: a story is often
delivered incrementally across more than one task, or even across more than one sprint
(e.g. a backend endpoint in one sprint, its frontend in a later one), and several sprint
tasks (setup, architecture, DevOps, documentation) support no single story and are
therefore absent from this table even though they appear in @tab:sprints.

#figure(
  table(
    columns: (auto, auto, auto),
    stroke: 0.5pt + luma(200),
    align: (center + horizon, center + horizon, left + horizon),
    inset: (x: 8pt, y: 6pt),
    fill: (_, y) => if y == 0 { luma(232) } else if calc.odd(y) { luma(250) } else { white },
    table.header([*US ID*], [*Sprint(s)*], [*Task(s)*]),

    link(label("us:01"))[US-01], [Sprint 1], link(label("task:s1-04"))[S1-04],
    link(label("us:02"))[US-02], [Sprint 1], link(label("task:s1-04"))[S1-04],
    link(label("us:03"))[US-03], [Sprint 1], link(label("task:s1-04"))[S1-04],
    link(label("us:04"))[US-04], [Sprints 1, 5], (link(label("task:s1-03"))[S1-03], link(label("task:s5-05"))[S5-05]).join(", "),
    link(label("us:05"))[US-05], [Sprints 1, 5], (link(label("task:s1-03"))[S1-03], link(label("task:s5-05"))[S5-05]).join(", "),
    link(label("us:06"))[US-06], [Sprints 1, 2, 3], (link(label("task:s1-03"))[S1-03], link(label("task:s2-03"))[S2-03], link(label("task:s3-02"))[S3-02]).join(", "),
    link(label("us:07"))[US-07], [Sprints 4, 5], (link(label("task:s4-08"))[S4-08], link(label("task:s5-06"))[S5-06]).join(", "),
    link(label("us:08"))[US-08], [Sprints 0, 1], (link(label("task:s0-06"))[S0-06], link(label("task:s1-05"))[S1-05]).join(", "),
    link(label("us:09"))[US-09], [Sprints 1, 5], (link(label("task:s1-03"))[S1-03], link(label("task:s5-05"))[S5-05]).join(", "),
    link(label("us:10"))[US-10], [Sprints 0, 1, 2], (link(label("task:s0-04"))[S0-04], link(label("task:s1-03"))[S1-03], link(label("task:s2-03"))[S2-03]).join(", "),
    link(label("us:11"))[US-11], [Sprint 2], (link(label("task:s2-03"))[S2-03], link(label("task:s2-04"))[S2-04]).join(", "),
    link(label("us:12"))[US-12], [Sprint 2], (link(label("task:s2-03"))[S2-03], link(label("task:s2-04"))[S2-04]).join(", "),
    link(label("us:13"))[US-13], [Sprint 2], link(label("task:s2-04"))[S2-04],
    link(label("us:14"))[US-14], [Sprint 2], link(label("task:s2-04"))[S2-04],
    link(label("us:15"))[US-15], [Sprints 4, 5], (link(label("task:s4-08"))[S4-08], link(label("task:s5-06"))[S5-06]).join(", "),
    link(label("us:16"))[US-16], [Sprints 0, 2], (link(label("task:s0-05"))[S0-05], link(label("task:s2-01"))[S2-01], link(label("task:s2-03"))[S2-03]).join(", "),
    link(label("us:17"))[US-17], [Sprint 5], link(label("task:s5-01"))[S5-01],
    link(label("us:18"))[US-18], [Sprint 2], (link(label("task:s2-01"))[S2-01], link(label("task:s2-03"))[S2-03]).join(", "),
    link(label("us:19"))[US-19], [Sprint 2], (link(label("task:s2-01"))[S2-01], link(label("task:s2-03"))[S2-03]).join(", "),
    link(label("us:20"))[US-20], [Sprints 4, 5], (link(label("task:s4-02"))[S4-02], link(label("task:s4-03"))[S4-03], link(label("task:s5-02"))[S5-02]).join(", "),
    link(label("us:21"))[US-21], [Sprint 4], (link(label("task:s4-06"))[S4-06], link(label("task:s4-07"))[S4-07]).join(", "),
    link(label("us:22"))[US-22], [Sprint 5], link(label("task:s5-03"))[S5-03],
    link(label("us:23"))[US-23], [Sprints 2, 3], (link(label("task:s2-05"))[S2-05], link(label("task:s2-06"))[S2-06], link(label("task:s3-06"))[S3-06]).join(", "),
    link(label("us:24"))[US-24], [Sprint 5], link(label("task:s5-04"))[S5-04],
  ),
  caption: [User Story Traceability Matrix],
) <tab:traceability>
