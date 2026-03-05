# Database — Alembic + SQLAlchemy

PostgreSQL is managed via Docker. Schema migrations are handled by Alembic. SQLAlchemy ORM models live in `db/`.

> **Extended documentation** lives in [`technical-docs/`](technical-docs/):
> - [Full setup tutorial](technical-docs/tutorial.md) — step-by-step guide from clone to seeded DB
> - [Technology stack](technical-docs/stack.md) — registry of every library and tool used
> - [Database schema](technical-docs/database-schema.md) — ER diagram, column descriptions, JSONB formats
> - [Backend architecture](technical-docs/architecture.md) — API options, decoupling strategy, Swagger
> - [API technology decision](technical-docs/api-decision.md) — rationale for FastAPI, trade-offs, structural consequences
> - [Launching the backend](technical-docs/launch.md) — local dev and Docker Compose startup guide
> - [Testing](technical-docs/testing.md) — how to run the suite, fixture design, test coverage table

---

## Setup

### 1. Configure environment

Copy `.env` (already gitignored) and fill in credentials:

```
POSTGRES_USER=postgres
POSTGRES_PASSWORD=<password>
POSTGRES_DB=matrix_db
POSTGRES_HOST=localhost
POSTGRES_PORT=5435
```

### 2. Start the database

```bash
docker compose up -d
```

Postgres runs on port **5435** (to avoid conflicts with a local 5432).

### 3. Install Python dependencies

```bash
pip install -r requirements.txt
```

### 4. Apply migrations

```bash
python -m alembic upgrade head
```

### 5. Verify tables

```bash
docker compose exec db psql -U postgres -d matrix_db -c "\dt"
```

Expected output: `alembic_version`, `population_matrices`, `simulation_runs`, `users`.

---

## Project structure

```
alembic.ini                  # Alembic config (DB URL is set in env.py, not here)
alembic/
  env.py                     # Loads .env, wires Base.metadata for autogenerate
  script.py.mako             # Template for new migration files
  versions/
    0001_initial_schema.py   # Initial migration: creates all 3 tables
db/
  __init__.py
  models.py                  # SQLAlchemy ORM models (User, PopulationMatrix, SimulationRun)
  session.py                 # engine + SessionLocal factory
```

---

## ORM models (`db/models.py`)

| Table | Key columns |
|---|---|
| `users` | `id`, `username`, `email`, `password_hash`, `created_at` |
| `population_matrices` | `id`, `source_type`, `owner_id→users`, `species_accepted`, `kingdom`, `country_code`, `matrix_a/u/f` (JSONB), `stage_names` (JSONB) |
| `simulation_runs` | `id`, `user_id→users`, `matrix_id→population_matrices`, `initial_vector` (JSONB), `n_steps`, `result_history` (JSONB) |

---

## Using the session in application code

```python
from db.session import SessionLocal
from db.models import User

with SessionLocal() as session:
    users = session.query(User).all()
```

---

## Common Alembic commands

```bash
# Apply all pending migrations
python -m alembic upgrade head

# Roll back the last migration
python -m alembic downgrade -1

# Roll back everything
python -m alembic downgrade base

# Show current revision in the DB
python -m alembic current

# Show migration history
python -m alembic history --verbose
```

## Adding a new migration

After changing `db/models.py`, autogenerate a migration:

```bash
python -m alembic revision --autogenerate -m "describe_your_change"
```

**Always review the generated file** in `alembic/versions/` before applying it — autogenerate can miss things like index changes or column type alterations. Then apply:

```bash
python -m alembic upgrade head
```

---

## Stopping / resetting the database

```bash
# Stop without deleting data
docker compose down

# Stop AND delete all data (volume)
docker compose down -v
# Then re-apply migrations to start fresh:
python -m alembic upgrade head
```
