= Cross-Cutting Concepts <cross-cutting-concepts>

Cross-cutting concepts are architectural concerns that affect multiple
components and cannot be assigned to a single layer or module. This chapter
documents them following arc42 section 8.

== Security

=== Authentication and Authorisation

Authentication is implemented with JSON Web Tokens (JWT) signed with the
HS256 algorithm. The `JWT_SECRET_KEY` environment variable holds the signing
secret and is never hardcoded or committed to the repository. Tokens carry the
user identity (`sub` claim set to the user id) and expire after seven days.

Every protected endpoint declares the `get_current_user` FastAPI dependency.
This dependency validates the token signature, checks expiry, and resolves the
authenticated user before any controller logic runs. If the token is missing,
malformed, or expired the dependency raises `HTTP 401` immediately, and the
request never reaches the service layer.

Authorisation is handled exclusively in the service layer. Ownership checks
(`run.user_id == user_id`, `matrix.owner_id == user_id`) are explicit Python
comparisons, not SQL `WHERE` clauses. This keeps the rules visible, auditable,
and fully testable with mocked repositories without a database.

=== Password Storage

User passwords are hashed with bcrypt before being written to the database.
The plaintext password exists only for the duration of the registration or
login request and is never logged or persisted. The `hashed_password` column
in the `users` table stores only the bcrypt digest.

=== Input Validation as a Security Boundary

All data entering the system over HTTP is parsed and validated by Pydantic
schema classes before reaching any business logic. This provides a strict
security boundary at the API surface:

- Unexpected fields are ignored.
- Type coercion is performed explicitly (no implicit casting from string to int).
- Cross-field invariants (e.g. exactly one of `matrix_id` / `matrix_ids`) are
  checked before any database access occurs.

Validation failures are returned as `422 Unprocessable Entity` with structured
field-level error messages, preventing the service layer from ever receiving
malformed input.

=== Static and Dependency Security Analysis

Three automated security tools run on every push and pull request and on a
weekly schedule:

- *Bandit* performs Python SAST, scanning `api/` and `db/` for common
  security anti-patterns. A two-pass strategy is used: a medium-severity pass
  produces an artifact for review, and a high-severity pass gates the pipeline.
- *pip-audit* scans `requirements.txt` against the PyPA Advisory Database for
  known CVEs in direct and transitive dependencies.
- *Trivy* scans the built Docker image for OS-level and library-level
  vulnerabilities at `CRITICAL` and `HIGH` severity.

== Error Handling

=== Uniform Exception Strategy

Business rule violations are raised as `fastapi.HTTPException` inside the
service layer with an explicit HTTP status code and a human-readable detail
message. Controllers never catch and re-wrap these exceptions — FastAPI
propagates them directly to the client as structured JSON error responses.

The following status codes are used consistently throughout the API:

#table(
  columns: (auto, 1fr),
  inset: 8pt,
  align: left,
  table.header([*Code*], [*Condition*]),
  [`400`], [Business rule violation — e.g. vector dimension mismatch, missing `matrix_a`],
  [`401`], [Missing, malformed, or expired JWT token],
  [`403`], [Authenticated but not authorised — wrong owner, COMPADRE immutability],
  [`404`], [Requested resource does not exist],
  [`409`], [Uniqueness conflict — username or email already registered],
  [`422`], [Pydantic schema validation failure — structured field-level detail],
)

=== No Silent Failures

Every error path in the service layer raises an exception explicitly. There
are no bare `except` blocks that swallow errors, no `None` returns where a
resource is expected to exist, and no fallback values that mask unexpected
states. This makes the system's behaviour predictable and the error surface
easy to test.

== Observability

=== Request Logging

Uvicorn and FastAPI emit structured access logs by default for every HTTP
request, capturing the method, path, response status code, and processing
time. These logs are written to standard output and collected by Docker.

=== Health Endpoint

The `GET /health` endpoint returns a static `200 OK` response with no
authentication required. It serves as a liveness probe for Docker Compose
health checks, load balancers, and monitoring tools. The API container is
only considered ready after this endpoint responds successfully.

=== Test Coverage Reporting

The CI pipeline measures test coverage with `pytest-cov` on every push to
`main` and uploads the XML report to Codecov. This provides a continuous,
visible measure of how much of `api/` and `db/` is exercised by the test
suite, and surfaces coverage regressions in pull request reviews.

== Reproducibility

=== Stochastic Simulation Seeds

Stochastic simulations store the `random_seed` value used to initialise the
NumPy random generator alongside the computed trajectory. Any stored
stochastic run can be reproduced exactly by re-submitting the same
`matrix_ids`, `initial_vector`, `n_steps`, and `random_seed` to
`POST /v1/simulations/run`. This is also verified by the unit test suite,
which asserts that identical seeds always produce identical histories.

=== Versioned Database Migrations

All schema changes are captured as Alembic migration scripts in
`alembic/versions/`. Migrations are applied automatically by the container
entrypoint on startup, making the database schema deterministic with respect
to the deployed code version. Running the same migration chain on any clean
PostgreSQL instance always produces the same schema.

=== Containerised Environment

The full stack is defined declaratively in `docker-compose.yml`. Any machine
with Docker installed can reproduce the exact same runtime environment — same
Python version, same OS packages, same PostgreSQL version — with a single
command. This eliminates environment-specific behaviour and ensures that the
CI environment matches the development environment.

== Data Integrity

=== COMPADRE Immutability

Matrices seeded from the COMPADRE database carry `source_type = "compadre"`.
The service layer rejects any `PATCH` request against a COMPADRE matrix with
`HTTP 403`, regardless of the requesting user's identity. This rule is
enforced in `MatrixService.update_matrix` and is covered by dedicated unit
and integration tests. No database constraint is relied upon for this
invariant — the service layer is the single point of enforcement.

=== Stage Names Snapshot

When a simulation is stored, the `stage_names` of the source matrix are
copied into the `simulation_runs.stage_names` column. This snapshot decouples
the historical simulation record from the source matrix: if the matrix is
later updated or deleted, the simulation remains fully interpretable with the
correct stage labels.

=== Ownership Isolation

Each user's simulation library is private. The list, get, export, and delete
endpoints all perform an ownership check in the service layer before returning
or modifying any data. A user who guesses another user's simulation id receives
`HTTP 403`, not the simulation data.

== Testability

=== Layer Isolation by Design

The controller / service / repository separation is not only an architectural
preference — it is the mechanism that makes the business logic unit-testable
without a database. The service layer receives its repositories through
constructor injection, which allows tests to substitute `MagicMock` objects
with configured return values. This pattern is used throughout
`tests/unit/test_simulation_service.py`,
`tests/unit/test_matrix_service.py`, and
`tests/unit/test_auth_service.py`.

=== Two-Speed Test Suite

Unit tests in `tests/unit/` run in seconds with no external dependencies and
provide fast feedback during development. Integration tests in `tests/`
exercise the full HTTP stack against a real PostgreSQL instance and validate
SQL correctness, migration state, and serialisation round-trips. The CI
pipeline runs unit tests first, only proceeding to integration tests if the
unit tests pass.

== Configuration Management

=== Environment Variables

All environment-specific values are externalised to a `.env` file that is
never committed to the repository. The required variables are:

#table(
  columns: (auto, 1fr),
  inset: 8pt,
  align: left,
  table.header([*Variable*], [*Purpose*]),
  [`POSTGRES_USER`],     [Database username],
  [`POSTGRES_PASSWORD`], [Database password],
  [`POSTGRES_DB`],       [Database name],
  [`POSTGRES_HOST`],     [Database host (`localhost` outside Docker, `db` inside)],
  [`POSTGRES_PORT`],     [Host-side port (5435); overridden to 5432 inside Docker],
  [`JWT_SECRET_KEY`],    [HMAC secret for JWT signing — must be kept confidential],
)

=== Docker Port Override

The `.env` file sets `POSTGRES_PORT=5435`, which is the host-side port
exposed by the `db` container. Inside Docker, however, PostgreSQL listens on
the standard port 5432. The `docker-compose.yml` overrides `POSTGRES_PORT` to
`5432` for the `api` and `frontend` services so that they connect correctly
without requiring a separate environment file for Docker. This is an explicit
design decision documented in `CLAUDE.md` to prevent the misconfiguration from
being reintroduced.
