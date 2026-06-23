// chapters/06_implementation/index.typ
#import "../../template.typ": guia

= Implementation

== Application Structure

The application follows the three-tier architecture described in @sec:service-arch and
is deployed as three Docker containers as shown in @fig:deployment. Each tier maps to
a top-level directory in the repository:

- *`frontend/`* - Python Shiny single-page application (`app.py` as entry point).
  Components for each tab live in `frontend/components/`; shared utilities (API client,
  Plotly helpers) in `frontend/components/utils.py`. All data flows through the REST
  API; no computation is performed in the frontend.

- *`api/`* - FastAPI application (`main.py` registers routers and CORS middleware).
  The internal structure enforces the controller → service → repository separation:
  `api/controllers/` for HTTP parsing, `api/services/` for business logic and
  algorithms, `api/repositories/` for database access. Input validation lives in
  `api/schemas.py`; response serialisation in `api/records.py`.

- *`db/`* - SQLAlchemy ORM models (`db/models.py`) and an Alembic migration history
  (`alembic/versions/`). The seed script (`db/seed_compadre.py`) populates COMPADRE
  matrices on first start-up and is idempotent on subsequent restarts.

=== Simulation Algorithms <sec:sim-algorithms>

The simulation logic resides entirely in `api/services/simulation_service.py` and is
invoked by both the ephemeral endpoint (`POST /v1/simulations/run`) and the stored
endpoint (`POST /v1/simulations`).

*Deterministic algorithm.* A single Leslie/Lefkovitch matrix $bold(A)$ is applied
iteratively for $T$ steps:

$
bold(v)(t+1) = bold(A) dot.op bold(v)(t), quad t = 0, 1, dots, T-1
$

The result is the full trajectory $[bold(v)(0), bold(v)(1), dots, bold(v)(T)]$ - a
list of $T+1$ population vectors.

*Stochastic algorithm.* Given $K$ matrices $bold(A)_0, dots, bold(A)_{K-1}$ and a
run count $N$ (parameter `n_runs`, range 10-1 000, default 100), the algorithm
executes $N$ independent runs. Before each run, a single matrix index $i$ is sampled
uniformly at random from the master RNG (`numpy.random.default_rng`). That matrix is
committed for all $T$ steps of the run:

$
i_r ~ "Uniform"({0, dots, K-1}), quad
bold(v)_r(t+1) = bold(A)_{i_r} dot.op bold(v)_r(t), quad r = 1, dots, N
$

After all runs complete, four aggregate trajectories are computed across the
$N times (T+1) times S$ tensor (where $S$ is the number of stages):

```python
all_histories = np.zeros((n_runs, n_steps + 1, n_stages))
# ... fill tensor ...
mean_h = all_histories.mean(axis=0)   # returned as result_history
var_h  = all_histories.var(axis=0)    # result_variance
min_h  = all_histories.min(axis=0)    # result_min_history
max_h  = all_histories.max(axis=0)    # result_max_history
```

The frontend renders the mean trajectory with a shaded min/max band (15 % opacity)
using Plotly `fill="toself"` traces.

*Quasi-extinction algorithm.* The quasi-extinction analysis
(`api/services/quasi_extinction_service.py`) applies the same per-run commitment
pattern. The master RNG picks one matrix per run; the committed matrix is applied for
all $T$ steps; the accumulated population vector is checked against the global or
per-stage extinction threshold after each step to record whether and when the run goes
extinct.

#pagebreak()

== CI/CD Pipeline Implementation

=== Repository Configuration

=== Branch Strategy and Protection Rules

=== Implemented Pipeline Stages

#guia[Screenshots of running pipeline]

=== Documentation Publishing Pipeline

Alongside `ci.yml` and `security.yml`, a third workflow (`docs.yml`) automates
publishing the compiled TFG document. It triggers on every push to `main`
that touches `tfg-doc/**`, plus manual dispatch, and runs three jobs:

+ *`build`* - installs Typst and runs `typst compile tfg-doc/main.typ
  tfg-doc/main.pdf`. The resulting PDF is uploaded as a workflow artifact so
  the two downstream jobs do not each recompile it.
+ *`release`* - downloads the artifact and publishes it as the asset of a
  single rolling GitHub Release tagged `docs-latest`. Because the tag is
  reused on every run rather than incremented, the download URL never
  changes between revisions.
+ *`pages`* - downloads the artifact alongside a generated redirect
  `index.html` and deploys both to GitHub Pages, so the root Pages URL opens
  the PDF directly.

The `release` and `pages` jobs both depend only on `build`, not on each
other, so a failure in one does not block the other from publishing. The
`pages` job additionally requires a one-time manual step that cannot be
scripted: enabling Settings → Pages → Source: "GitHub Actions" on the
repository. On a private repository this can still be configured, but the
published site only becomes publicly reachable once the repository itself
is made public.

=== Secret and Environment Variable Management

== Monitoring Implementation

=== Application Instrumentation

=== Prometheus Configuration

=== Grafana Dashboards

#guia[Screenshots of real dashboards]

=== Configured Alerts

#guia[If applicable]

== Implementation of Tests <sec:test-implementation>

The project is tested at three levels. Unit tests (`tests/unit/`) use
`unittest.mock.MagicMock` to replace all repositories and require no running database;
they can be executed standalone with `python -m pytest tests/unit/ -v`. Integration
tests (`tests/`) exercise the full request-response cycle against a live PostgreSQL
instance. End-to-end tests (`tests/e2e/`) drive the Shiny frontend with Playwright,
either against a mock API (CI default) or the real stack.

#figure(
  {
    set text(size: 8.5pt)
    table(
      columns: (auto, auto, auto, auto),
      stroke: 0.5pt + luma(160),
      align: (left + horizon, center + horizon, center + horizon, center + horizon),
      inset: (x: 6pt, y: 5pt),
      table.header(
        table.cell(fill: rgb("#1F4E79"))[#text(fill: white, weight: "bold")[Test module]],
        table.cell(fill: rgb("#1F4E79"))[#text(fill: white, weight: "bold")[Tests]],
        table.cell(fill: rgb("#1F4E79"))[#text(fill: white, weight: "bold")[Passed]],
        table.cell(fill: rgb("#1F4E79"))[#text(fill: white, weight: "bold")[Focus]],
      ),
      [`test_schemas.py`],               [56], [56], [Input validation (Pydantic schemas)],
      [`test_simulation_service.py`],    [55], [55], [Simulation algorithms and service logic],
      [`test_quasi_extinction_service.py`], [38], [38], [Quasi-extinction Monte Carlo and job lifecycle],
      [`test_analytics_service.py`],     [22], [22], [Eigenvalue analytics (λ₁, λ_s, elasticities)],
      [`test_matrix_service.py`],        [56], [56], [Matrix CRUD, visibility, sharing],
      [`test_auth_service.py`],          [10], [10], [Registration, login, JWT],
      [`test_frontend_utils.py`],        [7],  [7],  [Frontend `api()` HTTP helper: empty-body handling, error sanitisation],
      [`test_matrix_grid.py`],           [5],  [5],  [Shared matrix cell-grid editor (`render_matrix_grid`, `read_matrix`)],
      [*Total*],                         [*249*], [*249*], [],
    )
  },
  caption: [Unit test results by module (`python -m pytest tests/unit/ -v`, 249 collected, 249 passed)],
) <tab:unit-test-results>

#figure(
  {
    set text(size: 8.5pt)
    table(
      columns: (auto, auto, auto),
      stroke: 0.5pt + luma(160),
      align: (left + horizon, center + horizon, center + horizon),
      inset: (x: 6pt, y: 5pt),
      table.header(
        table.cell(fill: rgb("#1F4E79"))[#text(fill: white, weight: "bold")[Test module]],
        table.cell(fill: rgb("#1F4E79"))[#text(fill: white, weight: "bold")[Tests]],
        table.cell(fill: rgb("#1F4E79"))[#text(fill: white, weight: "bold")[Focus]],
      ),
      [`test_auth.py`],              [10], [Registration, login, token validation],
      [`test_health.py`],            [1],  [Health check endpoint],
      [`test_jobs.py`],               [43], [Quasi-extinction job lifecycle, polling, deletion],
      [`test_matrices.py`],           [59], [Matrix CRUD, filtering, pagination, PATCH (incl. US-11 edit fields), export/import],
      [`test_matrix_visibility.py`],  [35], [Private/shared/public visibility transitions, sharing],
      [`test_simulations.py`],        [60], [Ephemeral and stored simulations, export/import, deletion],
      [*Total*],                      [*208*], [],
    )
  },
  caption: [Integration test results by module (`python -m pytest tests/ --ignore=tests/unit --ignore=tests/e2e -v`, requires PostgreSQL)],
) <tab:integration-test-results>

#figure(
  {
    set text(size: 8.5pt)
    table(
      columns: (auto, auto, auto),
      stroke: 0.5pt + luma(160),
      align: (left + horizon, center + horizon, center + horizon),
      inset: (x: 6pt, y: 5pt),
      table.header(
        table.cell(fill: rgb("#1F4E79"))[#text(fill: white, weight: "bold")[Test module]],
        table.cell(fill: rgb("#1F4E79"))[#text(fill: white, weight: "bold")[Tests]],
        table.cell(fill: rgb("#1F4E79"))[#text(fill: white, weight: "bold")[Focus]],
      ),
      [`test_auth.py`],            [5],  [Login/registration modals, auth state],
      [`test_browse.py`],          [10], [Matrix browser search and filtering],
      [`test_my_matrices.py`],     [11], [Create, delete, and edit flows, the edit-flow tests (pre-population, species/kingdom save, matrix cell save, stage add + grid resize) were added alongside the US-11 (@us:11) frontend fix],
      [`test_navigation.py`],      [2],  [Tab navigation, UI state],
      [`test_quasi_extinction.py`],[10], [Quasi-extinction analysis UI],
      [`test_simulate.py`],        [9],  [Simulation UI flow: search, add matrices, run, save, delete],
      [*Total*],                   [*47*], [],
    )
  },
  caption: [End-to-end test results by module (`python -m pytest tests/e2e/ -v --browser firefox`, mock-API mode)],
) <tab:e2e-test-results>

Across all three levels, *504 tests* pass (249 unit + 208 integration + 47 E2E). Running
the unit and integration suites together with `--cov=api --cov=db
--cov=frontend.components.utils` (the scope tracked by Codecov in CI) reports *83%*
line coverage; the lowest-covered areas are the COMPADRE/COMADRE seeding scripts
(`db/seed_compadre.py`, `db/seed_comadre.py`, 0%, exercised only by the one-time
container startup path, not by the test suite) and `frontend/components/utils.py`'s
error-formatting branches for less common HTTP failure shapes.

Key test classes related to the stochastic simulation rework:

- `TestComputeStochastic` (6 tests) - verifies the multi-run algorithm shape, variance,
  reproducibility with seed, and the bimodal commitment property
  (`test_all_runs_commit_to_single_matrix`: with a doubling matrix and a zeroing matrix,
  after 3 steps the minimum is 0.0 and the maximum is 8.0 - no intermediate values are
  possible because each run commits to a single matrix).

- `TestPerRunMatrixSelection` (1 test) - verifies that quasi-extinction probability with
  a doubling/zeroing pair is ~0.5 (per-run commitment), not ~0.97 (which per-step
  selection would produce over 5 steps).
