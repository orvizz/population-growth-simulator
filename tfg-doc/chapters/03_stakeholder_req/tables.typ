// chapters/03_stakeholder_req/tables.typ
// All tables for Chapter 3. Included from solution_alternatives.typ.

#let solution-comparison-table = [
  #figure(
    table(
      columns: (1fr, auto, auto, auto, auto),
      inset: 8pt,
      align: (left, center, center, center, center),
      table.header(
        [*Criterion*],
        [*Script*],
        [*.exe*],
        [*Local app*],
        [*Web app*],
      ),
      [No installation required],           [#sym.times],     [#sym.checkmark], [#sym.times],     [#sym.checkmark],
      [Works on all platforms],             [#sym.tilde],     [#sym.times],     [#sym.tilde],     [#sym.checkmark],
      [Graphical interface],                [#sym.times],     [#sym.checkmark], [#sym.checkmark], [#sym.checkmark],
      [Live COMPADRE database],             [#sym.times],     [#sym.times],     [#sym.times],     [#sym.checkmark],
      [Persistent user storage],            [#sym.times],     [#sym.times],     [#sym.times],     [#sym.checkmark],
      [Multi-user collaboration],           [#sym.times],     [#sym.times],     [#sym.times],     [#sym.checkmark],
      [Centralised updates],                [#sym.times],     [#sym.times],     [#sym.times],     [#sym.checkmark],
      [Works without Python on client],     [#sym.times],     [#sym.checkmark], [#sym.times],     [#sym.checkmark],
      [99.5% availability guarantee],       [#sym.times],     [#sym.times],     [#sym.times],     [#sym.checkmark],
      [Security pipeline (SAST/CVE scan)],  [#sym.times],     [#sym.times],     [#sym.times],     [#sym.checkmark],
    ),
    caption: [Comparison of solution alternatives across key project criteria
              (#sym.checkmark = fully satisfied, #sym.tilde = partially satisfied,
              #sym.times = not satisfied).],
  ) <tab:solution-comparison>
]
