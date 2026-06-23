// chapters/02_planning/risks.typ
// Risk identification: one analysis card per identified risk, grouped by RBS
// category (see the Risk Breakdown Structure in the Appendix, @sec:risk-mgmt-plan).
// Probability and per-objective impact levels follow the scales defined there;
// the merged score cell is Probability x worst-affected-objective Impact, coloured
// by the zone it falls into on the Probability-Impact Matrix (@tab:pi-matrix).
#import "../../template.typ": risk-analysis, category-band

// ── Technical risks ─────────────────────────────────────────────────────────
#category-band[Technical Risks]

#risk-analysis(
  id: "T-01",
  name: [Simulation and analytics correctness errors],
  category: [Technical, Quality],
  description: [The deterministic and stochastic simulation engines
    (`api/services/simulation_service.py`) and the ecological analytics service
    ($lambda_1$, stable stage distribution, reproductive value, sensitivities,
    elasticities) implement non-trivial linear-algebra formulas drawn from
    Caswell @caswell2001. An implementation error could silently produce numerically
    valid but biologically meaningless results, which schema validation cannot
    catch and which could go unnoticed without domain review.],
  probability: [Low (30%)],
  impact: (
    cost:     [Low (10%)],
    schedule: [Moderate (20%)],
    scope:    [Low (10%)],
    quality:  [Very High (80%)],
  ),
  score: [0.24], zone: "red",
  strategy: [Mitigate],
  response: [Unit-test the analytics service against reference matrices with
    hand-verified eigenvalues; require the biology co-tutor
    (#link(<stake:si-5>)[SI-5]) to review and sign off on the formulas before
    they are presented as validated; add a regression test pinned to the
    corrected values whenever a discrepancy is found.],
  status: [Open, monitored via `tests/unit/test_analytics_service.py`; not
    materialised.],
)

#risk-analysis(
  id: "T-02",
  name: [Database performance at COMPADRE scale],
  category: [Technical, Performance & Reliability],
  description: [The COMPADRE seed loads close to 6,000 matrices into
    `population_matrices`. Unindexed search and filter queries (by species,
    kingdom, country, source) issued from the Browse Matrices tab could degrade
    response times as the catalog grows, especially once user-created custom
    matrices accumulate on top of the seeded set.],
  probability: [Medium (50%)],
  impact: (
    cost:     [Very Low (5%)],
    schedule: [Low (10%)],
    scope:    [Low (10%)],
    quality:  [Moderate (20%)],
  ),
  score: [0.10], zone: "yellow",
  strategy: [Mitigate],
  response: [Add database indexes on the commonly filtered columns; paginate
    `GET /v1/matrices` responses; cache repeated search results at the API
    layer.],
  status: [Open, indexes and pagination in place; monitored under realistic
    load.],
)

#risk-analysis(
  id: "T-03",
  name: [JWT / API security vulnerabilities],
  category: [Technical, Security],
  description: [The REST API is the only access path to user data, custom
    matrices, and simulation results, authenticated via JWT Bearer tokens. A
    flaw in token handling, password storage, or endpoint authorisation could
    allow unauthorized access to another user's matrices or simulations.],
  probability: [Very Low (10%)],
  impact: (
    cost:     [Low (10%)],
    schedule: [Low (10%)],
    scope:    [Very Low (5%)],
    quality:  [Very High (80%)],
  ),
  score: [0.08], zone: "yellow",
  strategy: [Mitigate],
  response: [Use battle-tested libraries for password hashing and JWT signing;
    keep token expiry short (7 days) and never persist secrets in the database;
    enforce automated scanning on every push via Bandit (SAST), pip-audit
    (CVEs), Trivy (container scan), and GitHub CodeQL.],
  status: [Open, continuously monitored by `security.yml` and
    `codeql.yml`; no high-severity findings to date.],
)

#risk-analysis(
  id: "T-04",
  name: [Breaking changes from upstream dependency updates],
  category: [Technical, Technology],
  description: [The project depends on a fast-moving Python ecosystem
    (FastAPI, SQLAlchemy, NumPy, Pydantic, Shiny for Python). An upstream
    release can introduce breaking changes that silently alter behaviour or
    break the build.],
  probability: [Medium (50%)],
  impact: (
    cost:     [Low (10%)],
    schedule: [Moderate (20%)],
    scope:    [Very Low (5%)],
    quality:  [Low (10%)],
  ),
  score: [0.10], zone: "yellow",
  strategy: [Mitigate],
  response: [Pin dependency versions in `requirements.txt`; let Dependabot open
    weekly update PRs individually rather than bulk-upgrading, and require CI
    (unit + integration + E2E) to pass before any dependency PR is merged.],
  status: [Open, Dependabot active; no unresolved breakage to date.],
)

#risk-analysis(
  id: "T-05",
  name: [Stochastic / Monte Carlo resource exhaustion],
  category: [Technical, Performance & Reliability],
  description: [Stochastic simulations and the quasi-extinction Monte Carlo job
    (`quasi_extinction_service.py`) run many repeated matrix multiplications per
    request. Without limits, a request with a very large number of steps or
    Monte Carlo iterations could exhaust memory or block the API process.],
  probability: [Low (30%)],
  impact: (
    cost:     [Very Low (5%)],
    schedule: [Low (10%)],
    scope:    [Low (10%)],
    quality:  [Moderate (20%)],
  ),
  score: [0.06], zone: "yellow",
  strategy: [Mitigate],
  response: [Cap `n_steps` at 1000 in `SimulationCreate` validation; use NumPy
    arrays rather than Python lists for population history; run
    quasi-extinction analyses as an asynchronous, DB-backed background job
    (`SimulationJob`) so a long-running Monte Carlo run cannot block the
    request/response cycle.],
  status: [Open, caps and async execution in place; not materialised.],
)

#risk-analysis(
  id: "T-06",
  name: [Windows / Linux development environment inconsistency],
  category: [Technical, Complexity & Interfaces],
  description: [Development happens on a Windows host while the application
    runs in Linux containers. Differences such as line-ending conventions or
    path handling can produce defects that only appear inside Docker, not in
    the local editor.],
  probability: [High (70%)],
  impact: (
    cost:     [Very Low (5%)],
    schedule: [Low (10%)],
    scope:    [Very Low (5%)],
    quality:  [Low (10%)],
  ),
  score: [0.07], zone: "yellow",
  strategy: [Mitigate],
  response: [Document known fixes in `CLAUDE.md` (e.g. `entrypoint.sh` must use
    LF endings); treat Docker Compose as the single source of truth for runtime
    behaviour rather than the host OS.],
  status: [Materialised, `entrypoint.sh` was committed with CRLF endings
    early in development, which prevented containers from starting until
    corrected with `sed -i 's/\\r//' entrypoint.sh`. Logged in the Issue Log and
    fixed; no recurrence since.],
)

// ── External risks ──────────────────────────────────────────────────────────
#category-band[External Risks]

#risk-analysis(
  id: "E-01",
  name: [COMPADRE data format or availability change],
  category: [External, Suppliers & External Services],
  description: [The platform's seeded matrix catalog depends entirely on the
    COMPADRE Plant Matrix Database, distributed as an external `.RData` file
    with a companion `.parquet` metadata file. A change to that schema, or the
    file becoming unavailable from its source, would break the seeding pipeline
    (`db/seed_compadre.py`).],
  probability: [Low (30%)],
  impact: (
    cost:     [Low (10%)],
    schedule: [Moderate (20%)],
    scope:    [High (40%)],
    quality:  [Moderate (20%)],
  ),
  score: [0.12], zone: "yellow",
  strategy: [Mitigate],
  response: [Vendor a pinned snapshot of the COMPADRE `.RData`/`.parquet`
    files inside the repository rather than re-downloading them at build time;
    document the expected schema so the ETL step can be adapted quickly if a
    future COMPADRE release changes it.],
  status: [Open, current snapshot vendored and seeding verified; not
    materialised.],
)

#risk-analysis(
  id: "E-02",
  name: [University documentation template or format requirement changes],
  category: [External, Regulation],
  description: [The TFG document follows formatting and structural guidelines
    set by the Escuela de Ingeniería Informática. A late change to those
    requirements (template, required sections, defense format) could force
    rework close to the submission deadline.],
  probability: [Very Low (10%)],
  impact: (
    cost:     [Very Low (5%)],
    schedule: [Low (10%)],
    scope:    [Very Low (5%)],
    quality:  [Very Low (5%)],
  ),
  score: [0.01], zone: "green",
  strategy: [Accept],
  response: [Monitor official guidance published by the School for the current
    academic year; keep at least one buffer day in the documentation schedule
    reserved for template-related adjustments.],
  status: [Open, not materialised.],
)

// ── Organizational risks ────────────────────────────────────────────────────
#category-band[Organizational Risks]

#risk-analysis(
  id: "O-01",
  name: [Sole-developer key-person risk],
  category: [Organizational, Resources],
  description: [Per the OBS (@fig:obs), one person performs every role on this
    project: planning, analysis, development, testing, and documentation. An
    extended illness or personal emergency has no fallback within the team and
    would stall all project activity simultaneously.],
  probability: [Low (30%)],
  impact: (
    cost:     [Moderate (20%)],
    schedule: [Very High (80%)],
    scope:    [High (40%)],
    quality:  [Moderate (20%)],
  ),
  score: [0.24], zone: "red",
  strategy: [Mitigate],
  response: [Commit and push work-in-progress frequently in small increments
    so no work is at risk of loss; keep `CLAUDE.md` and this document current
    enough that work could in principle be resumed after an interruption;
    notify both tutors proactively if availability is at risk so the schedule
    can be renegotiated early.],
  status: [Open, not materialised.],
)

#risk-analysis(
  id: "O-02",
  name: [Competing coursework workload],
  category: [Organizational, Prioritization],
  description: [As a 4th-year student, time available for this project
    competes directly with other concurrent subject deadlines, which are not
    under the project's control and can shift with little notice.],
  probability: [High (70%)],
  impact: (
    cost:     [Very Low (5%)],
    schedule: [High (40%)],
    scope:    [Low (10%)],
    quality:  [Low (10%)],
  ),
  score: [0.28], zone: "red",
  strategy: [Mitigate],
  response: [Built-in buffer days absorb short-term schedule pressure; user
    stories are prioritised with MoSCoW labels (@sec:stories) so Should/Could
    items can be paused first without affecting the Must-priority core; progress
    is tracked weekly against the plan (@sec:tracking-plan).],
  status: [Active management, buffer days are being consumed as planned;
    no Must-priority scope affected to date.],
)

// ── Project Management risks ────────────────────────────────────────────────
#category-band[Project Management Risks]

#risk-analysis(
  id: "PM-01",
  name: [Effort estimation / schedule slippage],
  category: [Project Management, Estimation],
  description: [Several phases of this solo project (e.g. the requirements and
    technology research phase, the frontend reactive-state implementation)
    already ran longer than their initial estimate, a common risk in
    single-developer academic projects where there is no second estimator to
    sanity-check planning assumptions.],
  probability: [High (70%)],
  impact: (
    cost:     [Low (10%)],
    schedule: [High (40%)],
    scope:    [Low (10%)],
    quality:  [Very Low (5%)],
  ),
  score: [0.28], zone: "red",
  strategy: [Mitigate],
  response: [Track actual versus planned duration per phase in the Tracking
    Plan (@sec:tracking-plan); re-estimate remaining phases from observed
    velocity rather than the original plan; trim Should/Could-priority scope
    before touching Must-priority requirements if slippage continues.],
  status: [Partially materialised, the requirements/technology research
    phase and the frontend reactive-state implementation each ran about one
    week over their original estimate (@sec:tracking-plan); absorbed using
    buffer days, no deadline impact to date.],
)

#risk-analysis(
  id: "PM-02",
  name: [Scope creep from stakeholder requests],
  category: [Project Management, Control],
  description: [The Biology Faculty stakeholders (#link(<stake:si-7>)[SI-7], and
    co-tutor #link(<stake:si-5>)[SI-5]) are an active source of domain feedback.
    A reasonable, well-intentioned request for an additional feature outside the
    agreed Stakeholder Requirements (@sec:stakeholder-requirements) baseline
    could expand scope beyond what the remaining schedule supports.],
  probability: [Medium (50%)],
  impact: (
    cost:     [Low (10%)],
    schedule: [Moderate (20%)],
    scope:    [High (40%)],
    quality:  [Low (10%)],
  ),
  score: [0.20], zone: "red",
  strategy: [Mitigate],
  response: [Treat the SR-F/SR-NF baseline (@sec:stakeholder-requirements) as
    frozen for the current release; log new requests in the Project Issue Log
    instead of implementing them immediately; route accepted-but-out-of-scope
    requests to the Future Work section (@sec:future-work) unless a
    Must-priority item is explicitly descoped to make room.],
  status: [Open, not materialised.],
)

#risk-analysis(
  id: "PM-03",
  name: [Tutor / co-tutor feedback delay],
  category: [Project Management, Communication],
  description: [Validation milestones, in particular biological-correctness
    review from the co-tutor (#link(<stake:si-5>)[SI-5]) and methodological
    review from the tutor (#link(<stake:si-4>)[SI-4]), depend on feedback
    turnaround that is outside the developer's direct control.],
  probability: [Medium (50%)],
  impact: (
    cost:     [Very Low (5%)],
    schedule: [Moderate (20%)],
    scope:    [Very Low (5%)],
    quality:  [Low (10%)],
  ),
  score: [0.10], zone: "yellow",
  strategy: [Mitigate],
  response: [Schedule bi-weekly check-ins with both tutors; send asynchronous
    written progress updates so feedback does not require a synchronous
    meeting; document decisions taken without feedback so they can be revisited
    once it arrives.],
  status: [Open, not materialised.],
)
