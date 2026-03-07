= System Architecture <architecture>

== Overview

The system follows a classic three-tier architecture composed of a presentation
layer, an application layer, and a data layer. Each tier runs as an independent
Docker container and communicates only through well-defined interfaces.

```
┌─────────────────────┐
│  Frontend (Shiny)   │  :8080  — Python Shiny reactive UI
│  presentation tier  │
└────────┬────────────┘
         │ HTTP / REST (JSON)
┌────────▼────────────┐
│  API (FastAPI)      │  :8000  — REST API, business logic
│  application tier   │
└────────┬────────────┘
         │ SQLAlchemy ORM
┌────────▼────────────┐
│  Database (Postgres)│  :5432  — persistent storage
│  data tier          │
└─────────────────────┘
```

The frontend never accesses the database directly. The API never accepts raw
SQL from the outside. This strict separation means each tier can be scaled,
replaced, or tested in isolation.

== API Layer Internal Structure

Within the API tier a second, finer-grained layering is enforced:
_controller_ → _service_ → _repository_. No layer may skip another.

=== Controllers (`api/controllers/`)

Controllers are responsible exclusively for HTTP concerns: parsing request
bodies into schema objects, invoking the appropriate service method, and
returning the resulting record with the correct HTTP status code. Controllers
contain no business logic and perform no database access.

=== Services (`api/services/`)

Services contain all business logic: ownership checks, immutability rules for
COMPADRE matrices, dimension validation across matrices, and the simulation
algorithm itself. Services receive and return domain objects (schemas in,
records out). They delegate all persistence to repositories.

=== Repositories (`api/repositories/`)

Repositories are the only layer permitted to interact with SQLAlchemy sessions.
They expose a narrow, entity-centric interface (`get_by_id`, `create`,
`update`, `delete`, `list`) and return raw ORM objects to the service layer.
No business rule is encoded here.

=== Schemas and Records (`api/schemas.py`, `api/records.py`)

Two distinct families of Pydantic models cross the API boundary.

- *Schemas* (input DTOs) validate data arriving over HTTP. All input
  validation — field constraints, cross-field invariants — lives exclusively
  in schemas.
- *Records* (output models) represent business entities as they flow out of
  the service layer and into HTTP responses. They are constructed from ORM
  objects via `model_validate` with `from_attributes=True`.

This separation prevents accidental exposure of internal fields and makes the
contract of each layer explicit.

=== Dependency Injection (`api/deps.py`)

FastAPI's dependency injection system is used to provide:
- A SQLAlchemy `Session` scoped to each request.
- Pre-built service instances that receive their repository dependencies.
- The `get_current_user` guard that validates JWT tokens and resolves the
  authenticated user.

The dependency tree is wired entirely in `deps.py`, keeping controllers and
services free of any framework-specific boilerplate.

== Data Layer

The database layer (`db/`) contains three components.

- *ORM models* (`db/models.py`) — SQLAlchemy declarative classes for `User`,
  `PopulationMatrix`, and `SimulationRun`.
- *Session factory* (`db/session.py`) — a `SessionLocal` factory consumed by
  the dependency injection layer.
- *COMPADRE seeder* (`db/seed_compadre.py`) — a startup script that populates
  the database with real-world population matrices from the COMPADRE Plant
  Matrix Database. The seeder is idempotent; re-running it on an already-seeded
  database is a no-op.

== Container Architecture

Three containers are defined in `docker-compose.yml`.

#table(
  columns: (auto, auto, auto),
  inset: 8pt,
  align: left,
  table.header([*Service*], [*Image*], [*Exposed port*]),
  [`db`], [`postgres:16-alpine`], [`5435` (host) → `5432` (container)],
  [`api`], [built from `Dockerfile`], [`8000`],
  [`frontend`], [built from `frontend/Dockerfile`], [`8080`],
)

The `api` and `frontend` containers wait for `db` to pass its health check
before starting. The `api` container runs `entrypoint.sh` on startup, which
applies pending Alembic migrations and then seeds COMPADRE data before
launching Uvicorn.

== Design Decisions and Trade-offs

=== Single-language Stack

Running Python on all three tiers (API, frontend, seed scripts) eliminates
build tool heterogeneity and makes it straightforward to share utility code.
The trade-off is that Python is not the most performant language for CPU-bound
work; however, matrix projection steps are delegated to NumPy's native BLAS
routines, so this is not a practical bottleneck for the expected workloads.

=== Server-side Simulation

The decision to run the simulation algorithm on the server rather than in the
browser was deliberate. Executing server-side guarantees that results are
reproducible (the server controls the RNG), stored persistently, and identical
regardless of the client device. It also prevents matrix data from being
unnecessarily transmitted to the client before computation.

=== COMPADRE Read-only Constraint

Matrices seeded from the COMPADRE database are marked `source_type = "compadre"`
and are rejected by the service layer if an update is attempted, regardless of
the requesting user's identity. This protects the integrity of the reference
dataset while still allowing users to create their own matrices with full
edit rights.
