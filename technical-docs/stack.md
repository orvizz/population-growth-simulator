# Technology Stack

## Processes and ports

| Process | Technology | Port | Entry point |
|---|---|---|---|
| Database | PostgreSQL 16 (Docker) | 5435 | `docker compose up -d db` |
| API | FastAPI + uvicorn | 8000 | `python -m uvicorn api.main:app` |
| Frontend | Shiny (Python) | 8080 | `python -m shiny run frontend/app.py` |

---

## Infrastructure

### Docker & Docker Compose
- **Version:** Docker Compose v2 (`docker compose` syntax)
- **Image:** `postgres:16-alpine`
- **Role:** Runs the PostgreSQL database in an isolated container. The Alpine image is used for minimal size (~85 MB). Data is persisted in a named Docker volume so it survives container restarts.
- **Config file:** `docker-compose.yml` (project root)
- **API service:** The `api` service is also defined in `docker-compose.yml`, built from the project `Dockerfile`, with the source directory mounted as a volume for hot-reload in development.

---

## Database

### PostgreSQL 16
- **Role:** Primary relational database.
- **Notable features used:**
  - **JSONB columns** — stores population matrices (matA, matU, matF), stage names, and extra metadata as binary JSON. Supports indexing and querying inside JSON documents.
  - **Foreign key constraints** — enforces referential integrity between `users`, `population_matrices`, and `simulation_runs`.
- **Port:** 5435 (host) → 5432 (container)
- **Database name:** `matrix_db` (production), `matrix_db_test` (created/dropped by test suite)

---

## API layer

### FastAPI 0.111+
- **Role:** REST API framework. Exposes endpoints under `/v1/`, generates Swagger UI automatically.
- **Key features used:**
  - Auto-generated OpenAPI 3.0 spec → Swagger at `/docs`, ReDoc at `/redoc`
  - Dependency injection via `Depends()` — wires DB session → repository → service → controller
  - `response_model` — serialises domain records to JSON and validates the output shape
  - `OAuth2PasswordBearer` — enforces Bearer token auth on protected routes
- **Files:** `api/main.py`, `api/controllers/`, `api/deps.py`

### uvicorn
- **Role:** ASGI server that runs the FastAPI app.
- **Dev mode:** `--reload` flag restarts the server on file changes.
- **Command:** `python -m uvicorn api.main:app --reload --port 8000`

### Pydantic 2.0+
- **Role:** Data validation for both input DTOs and domain records.
- **Two uses in this project:**
  - `api/schemas.py` — input validation: validates request bodies before they reach the service layer. Enforces square matrix shape, sub-matrix dimension matching, stage name count, etc.
  - `api/records.py` — domain records: constructed from ORM objects (`from_attributes=True`), used as FastAPI `response_model` targets.
- **Why two separate model types:** The DB schema and the API contract must be able to evolve independently. A change to `db/models.py` should not automatically change what the API returns.

### PyJWT 2.8+
- **Role:** Creates and verifies JSON Web Tokens for session management.
- **Algorithm:** HMAC-SHA256 (`HS256`)
- **Token lifetime:** 7 days
- **Secret:** `JWT_SECRET_KEY` from `.env`
- **Files:** `api/deps.py`

### bcrypt 4.1+
- **Role:** Password hashing and verification.
- **Why not passlib:** `passlib` is largely unmaintained as of 2024. `bcrypt` is used directly.
- **Files:** `api/services/auth_service.py`

---

## Frontend

### Shiny for Python
- **Role:** Frontend web application. Provides the user interface for browsing matrices, authentication, and creating/editing custom matrices.
- **Key features used:**
  - `reactive.value` — mutable state (auth token, selected matrix, search results)
  - `reactive.calc` — derived state (user's matrices, fetched from API)
  - `reactive.effect` + `reactive.event` — side effects triggered by UI actions (login, search, create)
  - `ui.page_navbar` / `ui.layout_sidebar` / `ui.card` — layout components
- **File:** `frontend/app.py`
- **Port:** 8080

### httpx
- **Role:** HTTP client used by the Shiny frontend to call the FastAPI backend.
- **Sync client** — used in Shiny server functions (which are synchronous).
- **Also used in:** `tests/` (FastAPI `TestClient` uses httpx internally)
- **Files:** `frontend/app.py`

---

## Database tooling

### SQLAlchemy 2.0+
- **Role:** ORM and database abstraction layer.
- **Key features used:**
  - `DeclarativeBase` — modern class-based model definition
  - `Mapped` / `mapped_column` — type-annotated column definitions
  - `relationship()` — Python-level associations between models
  - `JSONB` from `sqlalchemy.dialects.postgresql` — PostgreSQL-specific binary JSON type
  - `SessionLocal` factory — creates database sessions per request (via `get_db()`)
- **Files:** `db/models.py`, `db/session.py`

### Alembic 1.13+
- **Role:** Database schema migration tool.
- **Key features used:**
  - `alembic upgrade head` — applies all pending migrations
  - `alembic downgrade` — rolls back migrations
  - `--autogenerate` — diffs ORM models against the live DB
  - `env.py` — loads `.env` and connects `Base.metadata` for autogenerate
- **Files:** `alembic.ini`, `alembic/env.py`, `alembic/versions/`

### psycopg2-binary
- **Role:** PostgreSQL driver. SQLAlchemy uses it to communicate with the database.
- **Why binary:** Bundles compiled C extensions — no system PostgreSQL headers needed.
- **Connection string:** `postgresql+psycopg2://user:password@host:port/dbname`

### python-dotenv
- **Role:** Loads `.env` into `os.environ` at startup.
- **Used in:** `api/main.py` (app startup), `alembic/env.py` (migration runtime), `tests/conftest.py`

---

## Data pipeline

### pandas + pyarrow
- **Role:** Used in the COMPADRE data pipeline to read and process the metadata.
- **Parquet:** `metadata.parquet` stores the 9146-row metadata table in columnar binary format.

### rdata
- **Role:** Parses R's native `.RData` binary format in pure Python.
- **Used in:** `db/seed_compadre.py` (slow path), `growt-simulator-app/preproccesor.py`
- **Why:** COMPADRE is distributed as an R S4 object. `rdata` converts it without requiring R.

---

## Testing

### pytest 8.0+
- **Role:** Test runner.
- **Config:** No `pytest.ini` — discovery is by convention (`tests/test_*.py`)
- **Fixtures:** Session-scoped test database, per-test table truncation, auth fixtures

### FastAPI TestClient
- **Role:** In-process HTTP client for testing FastAPI apps without a running server.
- **Under the hood:** Uses httpx.
- **File:** `tests/conftest.py`

---

## Data source

### COMPADRE Plant Matrix Database
- **Version:** 6.25.8.0
- **Format:** R S4 object inside `.RData`
- **Contents:** 9146 population projection matrices, 806 species, 4 kingdoms
- **Reference:** Salguero-Gómez et al. (2015). COMPADRE: a global database of plant demography. *Journal of Ecology*.

---

## Project file map

```
population-growth-simulator/
│
├── .env                              # Credentials (gitignored)
├── Dockerfile                        # API container image
├── docker-compose.yml                # db + api services
├── requirements.txt                  # Runtime dependencies
├── requirements-dev.txt              # + pytest, httpx
│
├── api/                              # FastAPI application
│   ├── main.py                       # App factory, router mounts, CORS
│   ├── deps.py                       # get_db, JWT helpers, service factories, get_current_user
│   ├── schemas.py                    # Input DTOs (request validation)
│   ├── records.py                    # Domain records (response serialisation)
│   ├── controllers/
│   │   ├── auth.py                   # POST /v1/auth/register, /login
│   │   └── matrices.py               # GET/POST/PATCH /v1/matrices
│   ├── services/
│   │   ├── auth_service.py           # register, authenticate, get_by_id
│   │   └── matrix_service.py         # list, get, create, update + access guards
│   └── repositories/
│       ├── user_repository.py        # SQL: users table
│       └── matrix_repository.py      # SQL: population_matrices table
│
├── db/                               # Database layer
│   ├── models.py                     # SQLAlchemy ORM models
│   ├── session.py                    # engine + SessionLocal
│   └── seed_compadre.py              # ETL: COMPADRE → population_matrices
│
├── alembic.ini                       # Alembic config
├── alembic/
│   ├── env.py                        # Migration environment
│   └── versions/
│       └── 0001_initial_schema.py    # Creates all 3 tables + species index
│
├── frontend/
│   └── app.py                        # Shiny frontend (3 tabs: Browse, My Matrices, Account)
│
├── tests/
│   ├── conftest.py                   # Fixtures: test DB, client, alice, bob, compadre_matrix
│   ├── test_health.py                # 1 test
│   ├── test_auth.py                  # 8 tests
│   └── test_matrices.py              # 22 tests
│
└── technical-docs/                   # Architecture and process documentation
```
