# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Commands

### Run the full stack (recommended)
```bash
make up        # builds images, runs migrations + COMPADRE seed, starts all services
make down      # stop containers (data preserved)
make clean     # stop containers and delete all volumes (full reset)
make logs      # follow logs from all containers
make logs-api  # follow API logs only
```

On Windows, `make` may not be available in the shell — use the underlying commands directly:
```bash
docker compose up -d --build
docker compose down
docker compose logs -f api
```

Services after startup:
- Frontend: http://localhost:8080
- API: http://localhost:8000
- Swagger UI: http://localhost:8000/docs

### Run the test suite
```bash
python -m pytest tests/unit/ -v          # unit tests only (no DB needed)
python -m pytest tests/ -v               # full suite (requires DB running)
python -m pytest tests/test_matrices.py -v   # single file
python -m pytest tests/ -k "test_create"    # by name pattern
```

Unit tests (`tests/unit/`) use `unittest.mock` and need no DB. Integration tests connect to the DB from `.env`. The fixture auto-creates and drops a `matrix_db_test` database per session.

### Run services locally (without Docker)
```bash
python -m uvicorn api.main:app --reload --port 8000

cd frontend
python -m shiny run app.py --reload --port 8080
```

### Database migrations
```bash
python -m alembic upgrade head                            # apply all pending migrations
python -m alembic revision --autogenerate -m "description"  # generate migration from model diff
# Inside a running container:
docker compose exec api python -m alembic upgrade head
```

## Architecture

Three-tier application:

```
frontend/app.py  →  api/ (FastAPI)  →  db/ (PostgreSQL via SQLAlchemy + Alembic)
  (Shiny UI)          REST API             ORM models + migrations
```

### API layer (`api/`)

Strict controller → service → repository separation — no layer may skip another:

- **`api/controllers/`** — HTTP only. Parse requests, delegate to service, return records. No business logic, no DB access.
- **`api/services/`** — Business logic only. Enforces ownership, immutability rules, simulation algorithm. No direct DB access.
- **`api/repositories/`** — DB access only. No business rules.
- **`api/schemas.py`** — Input DTOs (Pydantic). All input validation lives here.
- **`api/records.py`** — Output domain records (Pydantic, `from_attributes=True`). Returned as API response models.
- **`api/deps.py`** — FastAPI dependency providers: DB session, service factories, JWT auth guard (`get_current_user`).
- **`api/main.py`** — App factory: registers routers and CORS middleware.

API prefix: `/v1/`. Auth uses JWT Bearer tokens (7-day expiry). Login uses OAuth2 password form (`/v1/auth/login`).

### Endpoints

| Method | Path | Auth | Description |
|---|---|---|---|
| GET | `/health` | no | Health check |
| POST | `/v1/auth/register` | no | Register user |
| POST | `/v1/auth/login` | no | Login → JWT token |
| GET | `/v1/matrices` | no | List/filter matrices |
| GET | `/v1/matrices/{id}` | no | Get matrix detail |
| POST | `/v1/matrices` | yes | Create custom matrix |
| PATCH | `/v1/matrices/{id}` | yes | Update own matrix |
| GET | `/v1/matrices/{id}/export` | optional* | Export as JSON (default) or CSV (`?format=csv`) |
| POST | `/v1/matrices/import` | yes | Batch import JSON/ZIP → `BatchImportResult` |
| POST | `/v1/simulations/run` | no | Ephemeral simulation (not stored) |
| POST | `/v1/simulations` | yes | Run + store simulation |
| GET | `/v1/simulations` | yes | List own simulations |
| GET | `/v1/simulations/{id}` | yes | Get simulation + history + analytics |
| GET | `/v1/simulations/{id}/export` | yes | Export as JSON (format_version 2) |
| POST | `/v1/simulations/import` | yes | Import from JSON (v1 or v2) |
| DELETE | `/v1/simulations/{id}` | yes | Delete own simulation |
| POST | `/v1/jobs/quasi-extinction` | yes | Start async quasi-extinction job → 202 |
| GET | `/v1/jobs` | yes | List own jobs (summary) |
| GET | `/v1/jobs/{id}` | yes | Poll job status + result |
| DELETE | `/v1/jobs/{id}` | yes | Delete completed/failed job |

### Database layer (`db/`)

- **`db/models.py`** — SQLAlchemy ORM: `User`, `PopulationMatrix`, `SimulationRun`, `SimulationJob`.
- **`db/session.py`** — `SessionLocal` session factory.
- **`db/seed_compadre.py`** — Seeds COMPADRE data on first startup (called by `entrypoint.sh`).
- **`alembic/versions/`** — Migrations run automatically by `entrypoint.sh` on container start.

Key model notes:
- `PopulationMatrix.metadata_` → serialized as `"metadata"` in API responses via `validation_alias`.
- `source_type`: `"compadre"` = read-only seeded data; `"custom"` = user-created.
- `SimulationRun.matrix_id` = FK for deterministic runs; `SimulationRun.matrix_ids` = JSONB list for stochastic.
- `SimulationRun.matrices_snapshot` = JSONB snapshot of matrix_a values at run time (immune to future edits).
- `SimulationRun.matrix_sequence` = JSONB list of matrix indices chosen at each step (stochastic only).
- `SimulationRun.analytics` = JSONB dict with computed analytics (see `docs/analytics.md`).
- `SimulationJob` — tracks async quasi-extinction jobs; lifecycle: pending → running → completed | failed.

### Simulation system

`POST /v1/simulations` runs the simulation **server-side** and stores the result.

**Deterministic:** provide `matrix_id` (single matrix). Each step: `v(t+1) = A @ v(t)`.
**Stochastic:** provide `matrix_ids` (≥2 matrices, same dimension). Each step: pick one matrix uniformly at random, then `v(t+1) = A_i @ v(t)`. Store `random_seed` for reproducibility.

`SimulationCreate` schema validates: exactly one of `matrix_id`/`matrix_ids`, `n_steps` in [1, 1000], `initial_vector` non-empty. Dimension matching is validated in `SimulationService` (requires DB).

**Analytics:** every simulation (ephemeral or stored) computes and returns ecological analytics — λ₁, stable stage distribution, reproductive value, sensitivities, elasticities for deterministic runs; λ_s, mean matrix, elasticities of mean for stochastic runs. Formulas and reliability caveats are in `docs/analytics.md`.

**Matrix snapshots:** matrix_a values are copied into the simulation record at run time. Stored simulations are immune to future matrix edits or deletions.

**Quasi-extinction jobs:** `POST /v1/jobs/quasi-extinction` starts an async Monte Carlo analysis (FastAPI BackgroundTasks, DB-backed). The background task creates its own DB session — the architecture is designed for future migration to Celery/Redis. Poll `GET /v1/jobs/{id}` for status and result.

### Frontend (`frontend/app.py`)

Single-file Python Shiny app. Never touches the DB — all data flows through the API. Four tabs:
- **Browse matrices** — search and inspect COMPADRE/custom matrices (public)
- **Simulate** — run deterministic or stochastic simulations, display population dynamics plot (auth required)
- **My matrices** — create and edit custom matrices (auth required)
- **Account** — login/register/logout

The `API_BASE_URL` environment variable controls the backend URL (default: `http://localhost:8000`).

### Tests

| Layer | Location | DB required |
|---|---|---|
| Schema validators | `tests/unit/test_schemas.py` | No |
| Service logic (mocked repos) | `tests/unit/test_matrix_service.py`, `test_auth_service.py`, `test_simulation_service.py`, `test_quasi_extinction_service.py` | No |
| Pure analytics math | `tests/unit/test_analytics_service.py` | No |
| HTTP integration | `tests/test_auth.py`, `tests/test_matrices.py`, `tests/test_health.py`, `tests/test_simulations.py`, `tests/test_jobs.py` | Yes |

### CI / Security workflows (`.github/workflows/`)

- **`ci.yml`** — tests + coverage + SonarCloud (push/PR to main)
- **`security.yml`** — Bandit SAST, pip-audit (CVEs), Trivy (container scan) — weekly + push/PR
- **`codeql.yml`** — GitHub CodeQL deep SAST — weekly + push/PR
- **`dependabot.yml`** — weekly PRs for pip, GitHub Actions, and Docker base image updates

SonarCloud requires a `SONAR_TOKEN` GitHub secret and `sonar-project.properties` configured with your org/project keys. See `docs/SONARCLOUD_SETUP.md`.

### Legacy / experimental (`growt-simulator-app/`)

Earlier prototype — standalone Shiny app, COMPADRE loaders, schema tools. Not part of the current architecture, kept for reference.

## Environment

Requires a `.env` file (not committed). Required variables:
```
POSTGRES_USER=...
POSTGRES_PASSWORD=...
POSTGRES_DB=...
POSTGRES_HOST=localhost   # overridden to "db" inside Docker
POSTGRES_PORT=5435        # host-side port; containers use 5432 (overridden in docker-compose.yml)
JWT_SECRET_KEY=...
```

## Known gotchas

- `entrypoint.sh` must have LF line endings (not CRLF). If edited on Windows: `sed -i 's/\r//' entrypoint.sh`.
- `docker-compose.yml` overrides `POSTGRES_PORT: 5432` for api/frontend services because `.env` has the host-side port (5435).


## Frontend Mockups

Frontend mockups are in C:\UNI\cuarto curso\tfg\population-growth-simulator\.superpowers\brainstorm\1188-1773245158. You can run them into a server and use the playwright MCP to take a look at them