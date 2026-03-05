# Deployment Guide

Everything you need to go from a fresh clone to a fully running system.

---

## System overview

```
Browser
  │
  ▼  :8080
Shiny frontend   (frontend/app.py)
  │  HTTP / httpx
  ▼  :8000
FastAPI + uvicorn  (api/)
  │  SQLAlchemy / psycopg2
  ▼  :5435
PostgreSQL 16  (Docker)
```

Three processes. Two ways to run them: local development (recommended) or full Docker Compose.

---

## Prerequisites

| Requirement | Version | Check |
|---|---|---|
| Python | 3.11+ | `python --version` |
| Docker Desktop | any recent | `docker compose version` |
| Git | any | `git --version` |

---

## Environment setup

### 1. Clone

```bash
git clone https://github.com/orvizz/population-growth-simulator.git
cd population-growth-simulator
```

### 2. Create `.env`

The `.env` file is gitignored. Create it at the project root:

```bash
# .env
POSTGRES_USER=postgres
POSTGRES_PASSWORD=your_password_here
POSTGRES_DB=matrix_db
POSTGRES_HOST=localhost
POSTGRES_PORT=5435

JWT_SECRET_KEY=change_this_to_a_random_secret
```

Generate a strong `JWT_SECRET_KEY`:

```bash
python -c "import secrets; print(secrets.token_hex(32))"
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

---

## Option A — Local development (recommended)

PostgreSQL runs in Docker. The API and frontend run directly with Python so file changes hot-reload instantly.

### Step 1 — Start the database

```bash
docker compose up -d db
```

Verify it is ready:

```bash
docker compose exec db pg_isready -U postgres -d matrix_db
# /var/run/postgresql:5432 - accepting connections
```

### Step 2 — Apply migrations

```bash
python -m alembic upgrade head
```

### Step 3 — Seed COMPADRE data (first time only)

```bash
python -m db.seed_compadre
# Seeding 9146 records into population_matrices...
# Done. Inserted: 9146, skipped: 0
```

### Step 4 — Start the API

Open a terminal and run:

```bash
python -m uvicorn api.main:app --reload --port 8000
```

Verify:

```bash
curl http://localhost:8000/health
# {"status":"ok"}
```

Swagger UI is at **http://localhost:8000/docs**.

### Step 5 — Start the frontend

Open a second terminal and run:

```bash
cd frontend
python -m shiny run app.py --reload --port 8080
```

The application is now at **http://localhost:8080**.

---

## Option B — Full Docker Compose

Runs the database and API in containers. Useful when you want a reproducible environment or need to share the stack with a collaborator without them installing Python dependencies.

> The Shiny frontend is not containerised and still runs locally (Step 4 below).

### Step 1 — Start database and API

```bash
docker compose up -d
```

On first run Docker builds the API image (~1–2 minutes). Output ends with:

```
Container tfg_postgres  Started
Container tfg_api       Started
```

### Step 2 — Apply migrations and seed (first time only)

```bash
docker compose exec api python -m alembic upgrade head
docker compose exec api python -m db.seed_compadre
```

### Step 3 — Verify

```bash
curl http://localhost:8000/health
# {"status":"ok"}

docker compose exec db psql -U postgres -d matrix_db -c \
  "SELECT COUNT(*) FROM population_matrices;"
#  count
# -------
#   9146
```

### Step 4 — Start the frontend

```bash
cd frontend
python -m shiny run app.py --reload --port 8080
```

---

## All URLs at a glance

| URL | Description |
|---|---|
| http://localhost:8080 | Shiny frontend |
| http://localhost:8000/health | API health check |
| http://localhost:8000/docs | Swagger UI — explore and test all endpoints |
| http://localhost:8000/redoc | ReDoc — read-only API reference |
| http://localhost:8000/openapi.json | Raw OpenAPI 3 spec |

---

## Running the tests

The test suite requires only the database to be running (no API server needed).

```bash
# Install dev dependencies (includes pytest + httpx)
pip install -r requirements-dev.txt

# Make sure the DB is running
docker compose up -d db

# Run all 31 tests
python -m pytest tests/ -v
```

The test runner creates a `matrix_db_test` database automatically and drops it when done. Production data is never touched.

Useful flags:

```bash
python -m pytest tests/ -x          # stop on first failure
python -m pytest tests/test_matrices.py -v   # single file
python -m pytest tests/ -q          # minimal output
```

---

## Stopping everything

```bash
# Stop API and database containers (data preserved)
docker compose down

# Stop and delete all data (fresh start)
docker compose down -v

# After down -v, re-apply migrations and re-seed:
docker compose up -d db
python -m alembic upgrade head
python -m db.seed_compadre
```

---

## Environment variable reference

| Variable | Required | Used by | Description |
|---|---|---|---|
| `POSTGRES_USER` | yes | API, Alembic, seeder | PostgreSQL username |
| `POSTGRES_PASSWORD` | yes | API, Alembic, seeder | PostgreSQL password |
| `POSTGRES_DB` | yes | API, Alembic, seeder, Docker | Database name (`matrix_db`) |
| `POSTGRES_HOST` | yes | API, Alembic, seeder | `localhost` locally · `db` inside Docker Compose |
| `POSTGRES_PORT` | yes | API, Alembic, seeder | `5435` |
| `JWT_SECRET_KEY` | yes | API | HMAC-SHA256 key — signs all auth tokens |
| `API_BASE_URL` | no | Frontend | API address seen by the frontend. Default: `http://localhost:8000` |

> `docker-compose.yml` overrides `POSTGRES_HOST=db` for the `api` container so it can reach the database by Docker service name. The `.env` value (`localhost`) is used only for local processes.

---

## Troubleshooting

| Symptom | Likely cause | Fix |
|---|---|---|
| `connection refused` on port 8000 | API not started | `python -m uvicorn api.main:app --reload --port 8000` |
| `connection refused` on port 5435 | DB container not running | `docker compose up -d db` |
| `alembic: command not found` | Alembic not on PATH | Use `python -m alembic` |
| `shiny: command not found` | Shiny not on PATH | Use `python -m shiny run ...` |
| `FATAL: password authentication failed` | `.env` mismatch | Check `.env` credentials match `docker-compose.yml` |
| `matrix_db_test already exists` | Test run crashed before cleanup | `docker compose exec db psql -U postgres -c "DROP DATABASE matrix_db_test;"` |
| Migrations fail midway | DB in partial state | `python -m alembic downgrade -1` then fix and re-run |
| Changes not hot-reloading | Missing `--reload` flag | Add `--reload` to uvicorn / `shiny run` command |
| `JWT_SECRET_KEY` is empty | `.env` not loaded | Check `.env` exists at project root and contains the key |

---

## Adding a new database migration

After editing `db/models.py`:

```bash
python -m alembic revision --autogenerate -m "describe_the_change"
# Review the generated file in alembic/versions/ before applying
python -m alembic upgrade head
```

Always review autogenerated migrations — Alembic can miss JSONB type changes and index modifications.
