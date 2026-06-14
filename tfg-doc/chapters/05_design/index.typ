// chapters/05_design/index.typ
#import "../../template.typ": guia

// Pull in all tables defined for this chapter
#let t = {
  import "tables.typ": containers-table, cicd-workflows-table, ci-env-table, error-codes-table, env-vars-table
  (
    containers: containers-table,
    cicd-workflows: cicd-workflows-table,
    ci-env: ci-env-table,
    error-codes: error-codes-table,
    env-vars: env-vars-table,
  )
}

= Design <sec:design>

This chapter documents the design decisions and structures that shape the
Population Growth Simulator. It covers the system architecture, internal
component design, development workflow, CI/CD pipeline, observability
approach, and test design. The aim is to explain not only _what_ was built
but _why_ each structural choice was made.

== Architectural Design <sec:arch-design>

The system follows a classic three-tier architecture: a presentation layer, an
application layer, and a data layer. Each tier is deployed as an independent
Docker container and communicates only through well-defined interfaces, allowing
each tier to be scaled, replaced, or tested in isolation.

=== High-Level Overview <sec:arch-overview>

@fig:context shows the system boundary and its two external actors. The
_User_ interacts with the system through a web browser, either browsing
public matrix data or running and saving simulations after authentication.
The _COMPADRE Plant Matrix Database_ @compadre is an external data source whose matrix
data is seeded into the system at startup; it has no runtime relationship
with the running application.

#figure(
  image("../../resources/diagrams/context.svg", height: auto),
  caption: [System context diagram. The Population Growth Simulator sits between the user's browser and the COMPADRE data source.],
) <fig:context>

@fig:building-blocks shows the three tiers and, within the application tier,
the internal layering of the API service. The presentation tier (Shiny
frontend, port 8080) communicates with the application tier exclusively
through HTTP REST calls. The application tier (FastAPI, port 8000) is itself
structured into controllers, services, and repositories. The data tier
(PostgreSQL, port 5432 inside Docker) is accessed only by the repository
layer.

#figure(
  image("../../resources/diagrams/building-blocks.svg", height: auto),
  caption: [Building-blocks view. The three tiers and the internal controller → service → repository layering of the API.],
) <fig:building-blocks>

=== Service Architecture <sec:service-arch>

Within the API tier, a second layer of separation is enforced: no layer may
skip another, and each has a single, well-defined responsibility.

*Controllers* (`api/controllers/`) handle all HTTP concerns. They parse
incoming request bodies into Pydantic schema objects, delegate to the
appropriate service method, and return the resulting record with the correct
HTTP status code. Controllers contain no business logic and perform no
database access.

*Services* (`api/services/`) contain all business logic: ownership checks,
immutability rules for COMPADRE matrices, cross-matrix dimension validation,
and the simulation algorithm itself. Services receive Pydantic schemas as
input and return domain records as output. All persistence is delegated to
repositories.

*Repositories* (`api/repositories/`) are the only layer permitted to interact
with SQLAlchemy sessions. They expose a narrow, entity-centric interface
(`get_by_id`, `create`, `update`, `list`) and return raw ORM objects to the
service layer. No business rule is encoded here.

*Schemas and Records* (`api/schemas.py`, `api/records.py`) form two distinct
families of Pydantic models that cross the API boundary. Schemas (input DTOs)
validate data arriving over HTTP — all field constraints and cross-field
invariants live exclusively in schemas. Records (output models) represent
business entities as they flow out of the service layer into HTTP responses,
constructed from ORM objects via `model_validate` with `from_attributes=True`.
This separation prevents accidental exposure of internal fields and makes the
contract of each layer explicit.

*Dependency injection* (`api/deps.py`) wires the full request dependency tree
using FastAPI's `Depends` mechanism: a SQLAlchemy `Session` scoped to each
request, pre-built service instances receiving their repository dependencies,
and the `get_current_user` guard that validates JWT tokens and resolves the
authenticated user before any controller logic runs.

=== Deployment and Infrastructure <sec:deployment>

@fig:deployment shows the Docker Compose deployment. The three containers
share a Docker-managed bridge network; only the host-side ports listed in
@tab:containers are exposed externally.

#figure(
  image("../../resources/diagrams/deployment.svg", height: auto, width: 80%),
  caption: [Deployment diagram. Three Docker containers communicate over an internal bridge network; only host-side ports are externally accessible.],
) <fig:deployment>

#t.containers

The `db` container uses a named volume (`postgres_data`) to persist data
across container restarts. The `api` and `frontend` services declare a
`depends_on` condition tied to the `db` health check, so they only start
after PostgreSQL is ready to accept connections. On startup, the `api`
container runs `entrypoint.sh`, which performs three idempotent steps before
launching Uvicorn: apply pending Alembic migrations (`alembic upgrade head`),
seed COMPADRE data (`python db/seed_compadre.py`), and start the server.
Restarting the container does not duplicate data or re-apply already-applied
migrations.

A deliberate port override exists: `.env` sets `POSTGRES_PORT=5435` (the
host-side port), while `docker-compose.yml` overrides `POSTGRES_PORT=5432`
for the `api` and `frontend` services so that they connect to the correct
container-internal port without requiring a separate environment file for
Docker.

== Detailed Design <sec:detailed-design>

=== Main System Flows <sec:system-flows>

The following eight sequence diagrams document all major user journeys through
the system. Each diagram captures the actors involved, the message exchange
between tiers, and the key business rules enforced at each step.

*User registration* (@fig:seq-register). The service layer checks that
neither the chosen username nor the email is already taken before hashing the
password with bcrypt and persisting the new user record.

#figure(
  image("../../resources/diagrams/register.svg", width: 85%),
  caption: [Sequence diagram: user registration. Uniqueness is checked before the password is hashed.],
) <fig:seq-register>

*User login* (@fig:seq-login). The client submits credentials through the
OAuth2 password form. The service verifies the bcrypt digest and, on success,
issues a signed JWT (HS256, seven-day expiry) that the client must include as
a Bearer token in subsequent authenticated requests.

#figure(
  image("../../resources/diagrams/login.svg", width: 85%),
  caption: [Sequence diagram: user login. Successful authentication produces a signed JWT.],
) <fig:seq-login>

*Search and browse matrices* (@fig:seq-search). This endpoint is public — no
authentication is required. The repository applies optional filters (species,
kingdom, source type) and returns summary projections rather than full matrix
data to keep responses compact.

#figure(
  image("../../resources/diagrams/search-matrix.svg", width: 85%),
  caption: [Sequence diagram: browse and filter matrices. The endpoint is public and returns summary projections.],
) <fig:seq-search>

*Create a custom matrix* (@fig:seq-create-matrix). Authentication is required.
The controller validates the request body through a Pydantic schema; the
service sets the `owner_id` to the authenticated user and persists the matrix
with `source_type = "custom"`.

#figure(
  image("../../resources/diagrams/create-matrix.svg", width: 85%),
  caption: [Sequence diagram: create a custom matrix. Ownership is set at creation time.],
) <fig:seq-create-matrix>

*Save a simulation* (@fig:seq-save-sim). The server runs the projection
algorithm and stores the complete trajectory (`result_history`) alongside a
snapshot of the matrix stage names. Storing server-side guarantees
reproducibility and uniform results across all client devices.

#figure(
  image("../../resources/diagrams/save-simulation.svg", width: 85%),
  caption: [Sequence diagram: save a simulation. The full trajectory is computed and stored server-side.],
) <fig:seq-save-sim>

*Open a saved simulation* (@fig:seq-open-sim). The service verifies that the
requesting user owns the simulation before returning the full history. An
unauthorised request receives `HTTP 403`.

#figure(
  image("../../resources/diagrams/open-simulation.svg", width: 85%),
  caption: [Sequence diagram: open a saved simulation. Ownership is checked before the trajectory is returned.],
) <fig:seq-open-sim>

*Export a simulation* (@fig:seq-export). The stored trajectory is serialised
to a JSON payload and returned to the client. No recomputation occurs.

#figure(
  image("../../resources/diagrams/export-simulation.svg", width: 85%),
  caption: [Sequence diagram: export a simulation as JSON. The stored result is serialised without recomputation.],
) <fig:seq-export>

*Import a simulation* (@fig:seq-import). The client uploads a previously
exported JSON file. The service deserialises the payload and re-persists it as
a new simulation record owned by the authenticated user, without re-running
the algorithm.

#figure(
  image("../../resources/diagrams/import-simulation.svg", width: 85%),
  caption: [Sequence diagram: import a simulation from JSON. The trajectory is restored from the file without rerunning the algorithm.],
) <fig:seq-import>

=== Persistent Data Model <sec:data-model>

The database contains three tables managed by SQLAlchemy ORM models defined
in `db/models.py`. @fig:er-diagram shows the entities, their attributes, and
the foreign-key relationships between them.

#figure(
  image("../../resources/diagrams/er.svg", height: auto),
  caption: [Entity-relationship diagram. Three tables store users, matrices, and simulation trajectories.],
) <fig:er-diagram>

*`users`.* Stores registered user accounts. Passwords are stored as bcrypt
hashes; the plaintext password exists only for the duration of the
registration or login request and is never persisted. The `username` and
`email` columns carry unique constraints enforced at the database level as a
second line of defence after the service-layer uniqueness check.

*`population_matrices`.* The central reference entity. Two kinds of records
coexist in this table, distinguished by `source_type`.

COMPADRE matrices (`source_type = "compadre"`) are seeded from the COMPADRE
Plant Matrix Database at startup. They have `owner_id = NULL` and are
read-only: any attempt to modify them through the API is rejected with
`HTTP 403`. Custom matrices (`source_type = "custom"`) are created by
authenticated users and can be updated by their owner.

Matrix data is stored as JSONB columns (`matrix_a`, `matrix_u`, `matrix_f`,
`stage_names`, `metadata_`). The ORM column is named `metadata_` (with a
trailing underscore) to avoid a collision with SQLAlchemy's internal
`metadata` attribute; the API serialises it as `"metadata"` through a Pydantic
`validation_alias`.

*`simulation_runs`.* Records a complete simulation result. The
`result_history` JSONB column stores the full list of population vectors from
step 0 (the initial vector) to step `n_steps`. For stochastic runs, this is
the mean population vector across all $N$ runs at each step, making retrieval
self-contained without re-running the algorithm.

For deterministic runs, `matrix_id` is set and `matrix_ids` is null. For
stochastic runs, `matrix_ids` is set (as a JSONB array of integers) and
`matrix_id` is null. The `random_seed` column enables exact reproduction of
stochastic runs. The `stage_names` column is a snapshot of the stage labels
at run time, so that historical simulations remain interpretable even if the
source matrix is later updated or deleted.

Four additional JSONB columns support the multi-run stochastic model:
`n_runs` records how many independent runs were executed; `result_variance`,
`result_min_history`, and `result_max_history` store the per-stage ensemble
statistics (variance, minimum, and maximum population values) at each time
step across all runs. The `matrix_sequence` JSONB column holds one committed
matrix index per run — not one per step — so the full run-level matrix
attribution is reproducible. All four columns are nullable and set to null for
deterministic runs.

Schema evolution is managed by Alembic. The migration chain runs from
`0001_initial_schema` (users and population_matrices) through
`0007_add_stochastic_stats` (multi-run stochastic columns on
simulation_runs). Migrations are applied automatically by `entrypoint.sh` on
container startup and are idempotent.

=== Design Patterns Applied <sec:design-patterns>

The following design patterns are applied throughout the codebase. Each is
documented with its intent and the concrete classes that fulfil each role.

*Repository Pattern.* Intent: decouple persistence from business logic, making
services independently testable. Roles: abstract interface → implicit Python
duck typing; concrete repositories → `MatrixRepository`
(`api/repositories/matrix_repository.py`), `SimulationRepository`, and
`UserRepository`. The service layer never accesses SQLAlchemy sessions
directly; it always goes through a repository. In the test suite, repositories
are replaced with `unittest.mock.MagicMock` objects so that service logic can
be verified without a database.

*Dependency Injection.* Intent: provide service and repository instances to
controllers without coupling them to instantiation logic. Roles: injector →
FastAPI's `Depends` mechanism; provider → `api/deps.py`; consumers → all
controller route functions. Each request receives a fresh DB session scoped to
its lifetime; services and repositories are constructed within `deps.py` and
injected into the controllers that need them.

*DTO / Record Split.* Intent: maintain a strict boundary between input
validation and output serialisation. Roles: input DTO → Pydantic Schema
classes in `api/schemas.py`; output model → Record classes in `api/records.py`.
This separation prevents the accidental exposure of internal ORM fields in
responses and makes the API surface explicit and auditable.

*Immutability Guard.* Intent: protect the integrity of the COMPADRE reference
dataset regardless of the requesting user's identity. Roles: guard location
→ `MatrixService.update_matrix` in `api/services/matrix_service.py`; trigger
→ `source_type == "compadre"`; response → `HTTPException(status_code=403)`.
The rule is enforced entirely in the service layer with no reliance on a
database constraint, making it fully testable with mocked repositories.

== Development Workflow and Tooling <sec:dev-workflow>

=== Repository and Version Control <sec:vcs>

The project is hosted on GitHub. @fig:branch-strategy shows the branching
model used throughout development.

#figure(
  image("../../resources/diagrams/branch-strategy.svg", height: auto),
  caption: [Branch strategy. All changes arrive on \`main\` through a pull request; direct pushes are not permitted.],
) <fig:branch-strategy>

The `main` branch is the single integration branch and is kept in a
deployable state at all times. All new work is developed on short-lived
feature or fix branches named `feature/<topic>` or `fix/<topic>`. A pull
request targeting `main` is required before any branch can be merged; the CI
workflow (Section sec:ci) must pass before the merge is allowed. This
guarantees that `main` never contains code that fails the test suite.

=== Team Workflow <sec:team-workflow>

This is a single-developer project. The development cycle follows a
lightweight agile-inspired loop: identify a task or defect, create a feature
branch from `main`, implement the change together with its tests, open a pull
request, wait for CI to pass, and merge. Commit messages follow the
imperative-mood convention (e.g. `Add stochastic simulation endpoint`,
`Fix COMPADRE immutability check`), keeping the git log readable as a
chronological record of intent.

== Continuous Integration and Deployment (CI/CD) <sec:cicd>

=== Pipeline Overview <sec:cicd-overview>

@fig:cicd-pipeline shows the two GitHub Actions workflows that together form
the automated pipeline. @tab:cicd-workflows summarises their triggers and
purposes.

#figure(
  image("../../resources/diagrams/cicd-pipeline.svg", height: auto),
  caption: [CI/CD pipeline. Two parallel GitHub Actions workflows handle correctness and security concerns independently.],
) <fig:cicd-pipeline>

#t.cicd-workflows

The two workflows are kept separate deliberately. A security job failure (for
example, a newly disclosed CVE in a transitive dependency) does not block a
feature merge, because the fix may require an upstream release that is outside
the developer's immediate control. Conversely, the weekly schedule of the
security workflow surfaces vulnerabilities in base images and dependencies
that no code commit could have detected.

=== Continuous Integration <sec:ci>

The CI workflow (`ci.yml`) runs on every push and pull request targeting
`main`. It provisions a PostgreSQL 16 service container within the CI job so
that integration tests can run against a real database without any external
infrastructure.

The workflow executes the following steps in order:

+ *Checkout* — `actions/checkout@v4` fetches the repository at the triggering commit.
+ *Setup Python 3.13* — `actions/setup-python@v5` installs Python and enables pip dependency caching.
+ *Install dependencies* — installs `requirements.txt` plus the test packages (`pytest`, `pytest-cov`).
+ *Apply migrations* — `python -m alembic upgrade head` brings the CI database schema to the current version.
+ *Unit tests* — `pytest tests/unit/ -v` runs the fast, database-free unit tests first. Failures here abort the pipeline before slower integration tests are attempted.
+ *Integration tests* — `pytest tests/ --ignore=tests/unit/ -v` runs the full HTTP integration suite against the provisioned PostgreSQL instance.
+ *Generate coverage report* — a combined `--cov=api --cov=db` run produces both a terminal summary and an XML report.
+ *Upload to Codecov* — the XML report is sent to Codecov for trend tracking. `fail_ci_if_error: false` prevents a Codecov service outage from blocking the pipeline.

@tab:ci-env lists the environment variables configured for the CI job. The
`JWT_SECRET_KEY` value is a non-production placeholder used only within the
isolated CI environment.

#t.ci-env

=== Continuous Deployment <sec:cd>

No automated deployment pipeline exists in the current implementation.
Deployment is performed manually by running `docker compose up -d --build` on
the target host after pulling the latest `main` branch. Automating this step
— for example, building a tagged Docker image in CI and deploying it to a
cloud host on merge to `main` — is identified as future work.

== Monitoring Design <sec:monitoring>

=== Observability Strategy <sec:observability>

A lightweight observability approach was chosen, appropriate to the
educational and research focus of the application. Two mechanisms are in place.

Uvicorn emits structured access logs by default for every HTTP request,
capturing the method, path, response status code, and processing time. These
logs are written to standard output and collected by Docker, making them
visible via `docker compose logs -f api` during local development and
available to any log aggregation tool in a cloud deployment.

Test coverage is tracked via Codecov on every push to `main`. The CI pipeline
uploads an XML coverage report for `api/` and `db/`, giving a continuous,
visible measure of how much of the codebase is exercised by the test suite and
surfacing coverage regressions in pull request reviews.

=== Monitoring Architecture <sec:monitoring-arch>

The `GET /health` endpoint returns a static `200 OK` response with no
authentication required. It serves as a liveness probe for Docker Compose
health checks: the `api` container is only considered ready after this
endpoint responds successfully, which gates the `frontend` container from
starting before the API is available. The same endpoint can be polled by an
external load balancer or uptime monitor in a production deployment.

The `db` container is configured with a PostgreSQL-specific health check
(`pg_isready`) that gates the `api` and `frontend` containers through
Docker Compose `depends_on` conditions. This prevents the application from
starting against a database that has not yet finished initialising.

=== Dashboard and Alert Design <sec:dashboards>

Prometheus metrics collection, Grafana dashboards, and alert rules are not
implemented in the current release. This is a deliberate scope decision:
adding a Prometheus exporter (e.g. `prometheus-fastapi-instrumentator`),
a Prometheus scrape configuration, and Grafana dashboard definitions would
meaningfully increase the operational surface area without adding educational
or research value in this phase. Integrating full observability infrastructure
is identified as future work in Section~sec:future-work.

== Test Design <sec:test-design>

The test suite is organised around a two-speed philosophy. Fast unit tests
with no external dependencies provide immediate feedback during development;
thorough integration tests against a real PostgreSQL instance validate the
full HTTP contract, SQL correctness, and migration state.

*Unit tests* (`tests/unit/`) use `unittest.mock.MagicMock` to substitute
repository implementations, allowing service business logic and Pydantic
schema validators to be exercised in complete isolation from the database.
The suite covers `MatrixService`, `SimulationService`, `AuthService`, and the
schema validation edge cases defined in `api/schemas.py`. Unit tests complete
in seconds and are run first in CI; a failure here aborts the pipeline before
integration tests are attempted.

*Integration tests* (`tests/`) use FastAPI's `TestClient` against a dedicated
`matrix_db_test` database. Shared pytest fixtures (`alice`, `bob`,
`compadre_matrix_id`, `alice_matrix`) create and tear down test data per
session, keeping tests isolated from one another. This layer validates full
request-to-database-to-response round-trips, including authentication flows,
ownership rules, and the simulation computation path.

*End-to-end tests* (`tests/e2e/`) use Playwright for Python to drive the
Shiny frontend in a real browser. Two run modes are supported: `RUN_MODE=mock`
serves canned fixture data through a lightweight mock API server (no database
required); `RUN_MODE=real` exercises the full stack. E2E tests are currently
run manually and are not part of the CI pipeline.

The test plan (what is tested and why) is described in Section~4.3. Section
6.4 will present the implementation results and coverage numbers.
