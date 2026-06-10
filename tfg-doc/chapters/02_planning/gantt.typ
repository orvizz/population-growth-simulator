// chapters/02_planning/gantt.typ

// ── Colour palette ──────────────────────────────────────────────────────────
#let _gh  = rgb("#1F4E79")              // header background
#let _gm  = rgb("#9DC3E6")              // project management (always on)
#let _ga  = rgb("#BDD7EE")              // generic development track
#let _gt  = rgb("#C6E0B4")              // testing & devops
#let _gd  = rgb("#F8CBAD")              // documentation

// ── Cell helpers ─────────────────────────────────────────────────────────────
#let _on(c)  = table.cell(fill: c)[]
#let _off    = []

// ── Gantt figure ─────────────────────────────────────────────────────────────
#figure(
  {
    set text(size: 7.5pt)
    table(
      columns: (2.4fr, 1fr, 1fr, 1fr, 1fr, 1fr),
      stroke: 0.5pt + luma(160),
      align: center + horizon,
      inset: (x: 5pt, y: 5pt),

      // ── Header row ──────────────────────────────────────────────────────
      table.cell(fill: _gh, align: left + horizon)[
        #text(fill: white, weight: "bold")[Workstream]
      ],
      table.cell(fill: _gh)[
        #text(fill: white, weight: "bold")[Feb \ #text(size: 6.5pt)[(Sprint 0)]]
      ],
      table.cell(fill: _gh)[
        #text(fill: white, weight: "bold")[Mar \ #text(size: 6.5pt)[(Sprints 1–2)]]
      ],
      table.cell(fill: _gh)[
        #text(fill: white, weight: "bold")[Apr \ #text(size: 6.5pt)[(Sprint 3)]]
      ],
      table.cell(fill: _gh)[
        #text(fill: white, weight: "bold")[May \ #text(size: 6.5pt)[(Sprints 3–4)]]
      ],
      table.cell(fill: _gh)[
        #text(fill: white, weight: "bold")[Jun \ #text(size: 6.5pt)[(Sprint 5)]]
      ],

      // ── Project Management (all months) ─────────────────────────────────
      table.cell(align: left + horizon)[Project Management],
      _on(_gm), _on(_gm), _on(_gm), _on(_gm), _on(_gm),

      // ── Prototype & Design (Feb) ─────────────────────────────────────────
      table.cell(align: left + horizon)[Prototype & Design],
      _on(_ga), _off, _off, _off, _off,

      // ── Core Architecture (Mar) ──────────────────────────────────────────
      table.cell(align: left + horizon)[Core Architecture],
      _off, _on(_ga), _off, _off, _off,

      // ── Authentication (Mar) ─────────────────────────────────────────────
      table.cell(align: left + horizon)[Authentication],
      _off, _on(_ga), _off, _off, _off,

      // ── Matrix Browsing (Mar–Apr) ────────────────────────────────────────
      table.cell(align: left + horizon)[Matrix Browsing],
      _off, _on(_ga), _on(_ga), _off, _off,

      // ── Custom Matrices (Apr) ────────────────────────────────────────────
      table.cell(align: left + horizon)[Custom Matrices],
      _off, _off, _on(_ga), _off, _off,

      // ── Simulations (Apr–May) ────────────────────────────────────────────
      table.cell(align: left + horizon)[Simulations],
      _off, _off, _on(_ga), _on(_ga), _off,

      // ── Analytics & Quasi-Extinction (May–Jun) ───────────────────────────
      table.cell(align: left + horizon)[Analytics & Quasi-Extinction],
      _off, _off, _off, _on(_ga), _on(_ga),

      // ── Testing & DevOps (Mar–Jun) ───────────────────────────────────────
      table.cell(align: left + horizon)[Testing & DevOps],
      _off, _on(_gt), _on(_gt), _on(_gt), _on(_gt),

      // ── Documentation (May–Jun) ──────────────────────────────────────────
      table.cell(align: left + horizon)[Documentation],
      _off, _off, _off, _on(_gd), _on(_gd),
    )
  },
  caption: [Project Gantt chart — February to June 2026],
) <fig:gantt>
