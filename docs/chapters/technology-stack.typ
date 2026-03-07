= Technology Stack

This chapter describes every technology selected for the project, the role each
one plays, and the rationale behind choosing it over available alternatives.

== Programming Language — Python 3.13

Python was chosen as the sole language for both the backend and the frontend.
The decision rests on three pillars.

First, the scientific ecosystem: NumPy, the de-facto standard for numerical
computing in Python, provides efficient n-dimensional array operations that map
directly onto the matrix algebra at the core of the simulation engine. No
equivalent library exists in other languages at the same level of maturity and
community support.

Second, productivity: Python's concise syntax and rich standard library
accelerate development. For an academic project with a fixed deadline this
factor carries significant weight.

Third, ecosystem coherence: using a single language for the entire stack
eliminates the friction of cross-language tooling, dependency management, and
cognitive context switching.

Python 3.13 specifically was selected to benefit from the latest performance
improvements to the interpreter and to match the version available in the CI
runner.

== Backend Framework — FastAPI

FastAPI @fastapi is the web framework that exposes the REST API. It was
preferred over Flask and Django REST Framework for the following reasons.

- *Automatic OpenAPI documentation.* FastAPI generates a Swagger UI at `/docs`
  with zero additional code. This is valuable during development and for
  demonstrating the API to non-technical stakeholders.
- *Native Pydantic integration.* Request and response models are declared as
  Pydantic classes; FastAPI handles validation, serialisation, and error
  formatting automatically.
- *Async-first design.* FastAPI is built on top of Starlette and supports
  `async`/`await` natively, leaving the door open for future non-blocking I/O
  without a rewrite.
- *Type safety.* The heavy use of Python type annotations propagates throughout
  the codebase, catching errors at development time rather than at runtime.

== Data Validation — Pydantic v2

Pydantic @pydantic is used exclusively for input and output modelling. All
data arriving from HTTP requests is parsed and validated by _schemas_ (input
DTOs), while all data leaving the service layer is serialised through _records_
(output models). This strict separation is detailed in @api-design.

Pydantic v2 was chosen over v1 because its Rust-backed validation core
delivers substantially faster parsing, which matters when many matrices or
simulation payloads are processed in a single request.

== Numerical Computing — NumPy

NumPy @numpy underpins the simulation engine. Population projection matrices
are converted to `ndarray` objects and each time step is computed as a single
matrix-vector product (`A @ v`), making use of NumPy's optimised BLAS
routines. The stochastic engine additionally relies on
`numpy.random.default_rng` for reproducible pseudo-random matrix selection.

== Database — PostgreSQL 16

PostgreSQL was selected as the relational database for the following reasons.

- *JSONB support.* Several columns (`matrix_a`, `matrix_u`, `matrix_f`,
  `result_history`, `stage_names`, `matrix_ids`) store variable-length nested
  structures. PostgreSQL's native JSONB type indexes and queries these
  efficiently without sacrificing the guarantees of a relational engine.
- *Reliability and maturity.* PostgreSQL is a production-grade RDBMS with
  decades of development behind it, making it a safe long-term choice.
- *SQLAlchemy compatibility.* The ORM layer integrates with PostgreSQL through
  the well-maintained `psycopg2` driver.

Version 16 specifically introduces performance improvements to parallel query
execution and JSONB handling.

== ORM — SQLAlchemy

SQLAlchemy @sqlalchemy acts as the bridge between Python objects and the
database. The _declarative_ mapping style (using `Base` and class-level column
definitions) was chosen because it keeps model definitions readable and
co-located with the Python type system.

The repository pattern is layered on top of SQLAlchemy sessions so that no
business logic leaks into raw query code and no SQL leaks into the service
layer.

== Database Migrations — Alembic

Alembic @alembic manages schema evolution. Every change to `db/models.py` is
captured as a versioned migration script in `alembic/versions/`. Migrations are
applied automatically by the container entrypoint on startup, ensuring that the
database schema is always in sync with the running code without manual
intervention.

== Frontend Framework — Python Shiny

The frontend is a single-file Python Shiny @shiny application. Shiny was
chosen because it allows building reactive data applications entirely in Python,
eliminating the need to introduce JavaScript or a separate frontend language.
This keeps the repository homogeneous and lowers the barrier to extending the
UI.

The application never touches the database directly; all data flows through the
REST API. This means the frontend is fully decoupled from the backend and can
be replaced with any other HTTP client in the future.

== Containerisation — Docker and Docker Compose

Docker @docker packages each service (API, frontend, database) into an
isolated container with a deterministic environment. Docker Compose @compose
orchestrates the three containers, defines the shared network, injects
environment variables, and manages startup order with health checks. This
setup means the entire stack can be started on any machine with a single
command (`docker compose up -d --build`) and the behaviour is identical in
development, CI, and production.

== Authentication — JWT

Authentication is implemented with JSON Web Tokens (JWT) @jwt signed with a
server-side secret. Tokens carry the user identity and expire after seven days.
The choice of JWT over server-side sessions avoids storing session state in the
database and makes horizontal scaling straightforward.

== Testing — pytest

pytest @pytest was chosen as the test runner for its concise fixture system,
rich assertion introspection, and the ability to parametrize tests. The suite
is divided into unit tests (no database required, using `unittest.mock`) and
integration tests (requiring a live PostgreSQL instance), allowing fast
feedback during development without sacrificing end-to-end coverage.

== CI/CD — GitHub Actions

GitHub Actions @gha orchestrates the automated pipelines. Two workflow files
are maintained: one for correctness (tests and coverage) and one for security
(static analysis, dependency auditing, and container scanning). The rationale
for this split is described in @devops.
