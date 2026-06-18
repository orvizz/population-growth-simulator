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

== Implementation of Tests

The project is tested at two levels. Unit tests (`tests/unit/`) use
`unittest.mock.MagicMock` to replace all repositories and require no running database;
they can be executed standalone with `python -m pytest tests/unit/ -v`. Integration
tests (`tests/`) exercise the full request-response cycle against a live PostgreSQL
instance.

#figure(
  {
    set text(size: 8.5pt)
    table(
      columns: (1fr, auto, auto, auto),
      stroke: 0.5pt + luma(160),
      align: (left + horizon, center + horizon, center + horizon, center + horizon),
      inset: (x: 6pt, y: 5pt),
      table.header(
        table.cell(fill: rgb("#1F4E79"))[#text(fill: white, weight: "bold")[Test module]],
        table.cell(fill: rgb("#1F4E79"))[#text(fill: white, weight: "bold")[Tests]],
        table.cell(fill: rgb("#1F4E79"))[#text(fill: white, weight: "bold")[Passed]],
        table.cell(fill: rgb("#1F4E79"))[#text(fill: white, weight: "bold")[Focus]],
      ),
      [`test_schemas.py`],               [49], [49], [Input validation (Pydantic schemas)],
      [`test_simulation_service.py`],    [53], [53], [Simulation algorithms and service logic],
      [`test_quasi_extinction_service.py`], [36], [36], [Quasi-extinction Monte Carlo and job lifecycle],
      [`test_analytics_service.py`],     [23], [23], [Eigenvalue analytics (λ₁, λ_s, elasticities)],
      [`test_matrix_service.py`],        [54], [54], [Matrix CRUD, visibility, sharing],
      [`test_auth_service.py`],          [10], [10], [Registration, login, JWT],
      [*Total*],                         [*225*], [*225*], [],
    )
  },
  caption: [Unit test results by module (`python -m pytest tests/unit/ -v`, 225 collected, 225 passed)],
) <tab:unit-test-results>

Key test classes related to the stochastic simulation rework:

- `TestComputeStochastic` (6 tests) - verifies the multi-run algorithm shape, variance,
  reproducibility with seed, and the bimodal commitment property
  (`test_all_runs_commit_to_single_matrix`: with a doubling matrix and a zeroing matrix,
  after 3 steps the minimum is 0.0 and the maximum is 8.0 - no intermediate values are
  possible because each run commits to a single matrix).

- `TestPerRunMatrixSelection` (1 test) - verifies that quasi-extinction probability with
  a doubling/zeroing pair is ~0.5 (per-run commitment), not ~0.97 (which per-step
  selection would produce over 5 steps).
