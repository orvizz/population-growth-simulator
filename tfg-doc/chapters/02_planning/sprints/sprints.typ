=== Sprint Backlogs

This section details the task backlog for each sprint. Tasks are categorised by
workstream and prioritised as *High*, *Med*, or *Low* relative to the sprint goal.

// ── Styling helpers ───────────────────────────────────────────────────────────

#let _styles = (
  "Setup":         (rgb("#E0F2FE"), rgb("#0369A1")),
  "Architecture":  (rgb("#DBEAFE"), rgb("#1E40AF")),
  "Feature":       (rgb("#DCFCE7"), rgb("#166534")),
  "Testing":       (rgb("#CCFBF1"), rgb("#0F766E")),
  "DevOps":        (rgb("#FEF3C7"), rgb("#92400E")),
  "Documentation": (rgb("#EDE9FE"), rgb("#5B21B6")),
  "Research":      (rgb("#FFF7ED"), rgb("#C2410C")),
)

#let _cat(label) = {
  let pair = _styles.at(label, default: (rgb("#F3F4F6"), rgb("#374151")))
  box(
    fill: pair.at(0), stroke: 0.5pt + pair.at(1), radius: 3pt,
    inset: (x: 4pt, y: 2pt),
    text(size: 7pt, fill: pair.at(1), weight: "bold")[#label]
  )
}

#let _prio(p) = {
  let c = if p == "High" { rgb("#DC2626") }
          else if p == "Med" { rgb("#D97706") }
          else { rgb("#16A34A") }
  text(size: 8pt, fill: c, weight: "bold")[#p]
}

#let _goal(body) = block(
  width: 100%, fill: luma(246),
  stroke: (left: 3pt + rgb("#2563EB")),
  inset: (left: 10pt, y: 8pt, right: 8pt), radius: 2pt,
)[*Sprint goal:* #body]

#let _btable(cap, rows) = figure(
  table(
    columns: (2.0cm, 1fr, 2.9cm, 1.4cm),
    stroke: 0.5pt + luma(200),
    align: (center + horizon, left + horizon, center + horizon, center + horizon),
    inset: (x: 8pt, y: 6pt),
    fill: (_, y) => if y == 0 { luma(232) } else if calc.odd(y) { luma(250) } else { white },
    table.header([*ID*], [*Task*], [*Category*], [*Priority*]),
    ..rows
  ),
  caption: cap,
)

// ── Legend ────────────────────────────────────────────────────────────────────

#block(
  stroke: 0.5pt + luma(200), radius: 3pt, inset: 10pt, width: 100%,
)[
  *Category legend:*
  #h(6pt)
  #_cat("Setup") #h(4pt)
  #_cat("Architecture") #h(4pt)
  #_cat("Feature") #h(4pt)
  #_cat("Testing") #h(4pt)
  #_cat("DevOps") #h(4pt)
  #_cat("Documentation") #h(4pt)
  #_cat("Research")
]

// ── Sprint 0 ─────────────────────────────────────────────────────────────────

==== Sprint 0 Backlog (Feb 11–28, 2026)

#_goal[Project inception: repository setup, Typst documentation template, initial Shiny prototype, and COMPADRE data exploration.]

#_btable([Sprint 0 backlog], (
  [S0-01], [Set up project repository and version control], _cat("Setup"), _prio("High"),
  [S0-02], [Draft project scope, objectives, and initial requirements], _cat("Setup"), _prio("High"),
  [S0-03], [Create Typst documentation template with styles and structure], _cat("Documentation"), _prio("High"),
  [S0-04], [Build initial Shiny prototype with matrix input UI], _cat("Feature"), _prio("High"),
  [S0-05], [Implement basic population simulation (matrix × vector loop)], _cat("Feature"), _prio("High"),
  [S0-06], [Research COMPADRE dataset structure and data access], _cat("Research"), _prio("Med"),
))

// ── Sprint 1 ─────────────────────────────────────────────────────────────────

==== Sprint 1 Backlog (Mar 1–14, 2026)

#_goal[Core architecture: FastAPI backend, PostgreSQL database, JWT authentication, COMPADRE seeder, initial test suite.]

#_btable([Sprint 1 backlog], (
  [S1-01], [Set up PostgreSQL schema with SQLAlchemy ORM and Alembic migrations], _cat("Architecture"), _prio("High"),
  [S1-02], [Scaffold FastAPI project skeleton with `/v1/` prefix and router layout], _cat("Architecture"), _prio("High"),
  [S1-03], [Implement `/v1/matrices` CRUD endpoints (list, detail, create)], _cat("Feature"), _prio("High"),
  [S1-04], [Implement JWT authentication endpoints (register, login)], _cat("Feature"), _prio("High"),
  [S1-05], [Build COMPADRE seeder to populate the matrix catalogue on startup], _cat("Feature"), _prio("High"),
  [S1-06], [Write initial test suite covering auth and matrix endpoints], _cat("Testing"), _prio("High"),
  [S1-07], [Document FastAPI technology decision, database schema, and stack], _cat("Documentation"), _prio("Med"),
))

// ── Sprint 2 ─────────────────────────────────────────────────────────────────

==== Sprint 2 Backlog (Mar 15–28, 2026)

#_goal[MVP polish: matrix ownership model, Docker stack, frontend redesign, end-to-end tests, CI/CD pipeline.]

#_btable([Sprint 2 backlog], (
  [S2-01], [Refactor backend to strict controller / service / repository layers], _cat("Architecture"), _prio("High"),
  [S2-02], [Create Docker Compose stack with auto-migration entrypoint script], _cat("DevOps"), _prio("High"),
  [S2-03], [Redesign Shiny frontend with four-tab layout (Browse, Simulate, My Matrices, Account)], _cat("Feature"), _prio("High"),
  [S2-04], [Implement matrix ownership model (`source_type`: custom vs. COMPADRE)], _cat("Feature"), _prio("High"),
  [S2-05], [Set up GitHub Actions CI pipeline (unit tests, integration tests)], _cat("DevOps"), _prio("High"),
  [S2-06], [Configure Bandit SAST, pip-audit, Trivy, and CodeQL security workflows], _cat("DevOps"), _prio("Med"),
  [S2-07], [Write integration tests for auth, matrix, and simulation endpoints], _cat("Testing"), _prio("High"),
))

// ── Sprint 3 ─────────────────────────────────────────────────────────────────

==== Sprint 3 Backlog (Mar 29 – May 8, 2026)

#_goal[Component decoupling and TFG documentation foundation: architecture diagrams, requirements analysis, technology alternatives.]

#_btable([Sprint 3 backlog], (
  [S3-01], [Complete frontend–backend decoupling (Shiny talks only to the API)], _cat("Architecture"), _prio("High"),
  [S3-02], [Add cyclic-graph visualisation and multi-matrix display in frontend], _cat("Feature"), _prio("Med"),
  [S3-03], [Write requirements analysis chapter (use cases, scenarios, state diagrams)], _cat("Documentation"), _prio("High"),
  [S3-04], [Write solution alternatives and technology comparison chapter], _cat("Documentation"), _prio("High"),
  [S3-05], [Produce ER diagram, component diagrams, and deployment diagrams], _cat("Documentation"), _prio("High"),
  [S3-06], [Fix GitHub Actions pipeline (Trivy scanner, test runner configuration)], _cat("DevOps"), _prio("Med"),
  [S3-07], [Compile bibliographic references for the TFG document], _cat("Documentation"), _prio("Low"),
))

// ── Sprint 4 ─────────────────────────────────────────────────────────────────

==== Sprint 4 Backlog (May 9–26, 2026)

#_goal[Analytics service, quasi-extinction service, async jobs system, simulation export format v2.]

#_btable([Sprint 4 backlog], (
  [S4-01], [Add simulation snapshot and analytics DB columns (migration 0005)], _cat("Architecture"), _prio("High"),
  [S4-02], [Implement `AnalyticsService` (λ₁, SSD, reproductive value, elasticities, sensitivities)], _cat("Feature"), _prio("High"),
  [S4-03], [Wire `AnalyticsService` into `SimulationService` for all run types], _cat("Feature"), _prio("High"),
  [S4-04], [Add typed analytics records and simulation export format v2 schema], _cat("Feature"), _prio("High"),
  [S4-05], [Implement simulation export and import endpoints (`/v1/simulations/{id}/export`)], _cat("Feature"), _prio("High"),
  [S4-06], [Implement `JobRepository` and `QuasiExtinctionService` (Monte Carlo)], _cat("Feature"), _prio("High"),
  [S4-07], [Add jobs controller and router (`/v1/jobs/`)], _cat("Feature"), _prio("High"),
  [S4-08], [Implement matrix upload/download in the frontend], _cat("Feature"), _prio("Med"),
  
))

// ── Sprint 5 ─────────────────────────────────────────────────────────────────

==== Sprint 5 Backlog (May 27 – Jun 9, 2026)

#_goal[Feature completion: stochastic simulation, quasi-extinction per-stage config, internationalisation, matrix import/export, comprehensive test suite.]

#_btable([Sprint 5 backlog], (
  [S5-01], [Implement stochastic simulation (multiple matrices, uniform random selection, seed)], _cat("Feature"), _prio("High"),
  [S5-02], [Add stochastic analytics (λ_s, mean-matrix elasticities) to `AnalyticsService`], _cat("Feature"), _prio("High"),
  [S5-03], [Implement per-stage thresholds and exclusions in quasi-extinction algorithm], _cat("Feature"), _prio("High"),
  [S5-04], [Add internationalisation support (Galician, Basque, Catalan, Asturian)], _cat("Feature"), _prio("Med"),
  [S5-05], [Refactor matrix browse view to paginated card/list layout], _cat("Feature"), _prio("Med"),
  [S5-06], [Expand unit and integration tests (export, import, stochastic, QE)], _cat("Testing"), _prio("High"),
  [S5-07], [Write Playwright E2E tests for quasi-extinction tab and navigation], _cat("Testing"), _prio("High"),
  [S5-08], [Write planning and management chapter for TFG documentation], _cat("Documentation"), _prio("High"),
  [S5-09], [Deploy application on railway], _cat("Feature"), _prio("Med"),
))
