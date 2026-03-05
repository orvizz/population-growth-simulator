# Technology Stack

## Infrastructure

### Docker & Docker Compose
- **Version:** Docker Compose v2 (`docker compose` syntax)
- **Image:** `postgres:16-alpine`
- **Role:** Runs the PostgreSQL database in an isolated container. The Alpine-based image is used for minimal size. Data is persisted in a named volume so it survives container restarts.
- **Config file:** `docker-compose.yml` (project root)

```yaml
services:
  db:
    image: postgres:16-alpine
    ports:
      - "5435:5432"   # host:container — uses 5435 to avoid local PG conflicts
    volumes:
      - postgres_data:/var/lib/postgresql/data
```

---

## Database

### PostgreSQL 16
- **Role:** Primary relational database.
- **Notable features used:**
  - **JSONB columns** — stores matrices (matA, matU, matF), stage names, and extra metadata as binary JSON. Supports indexing and querying inside JSON documents.
  - **Foreign key constraints** — enforces referential integrity between `users`, `population_matrices`, and `simulation_runs`.
- **Port:** 5435 (host) → 5432 (container)
- **Database name:** `matrix_db`

---

## Python Libraries

### SQLAlchemy 2.0+
- **Role:** ORM (Object-Relational Mapper) and database abstraction layer.
- **Key features used:**
  - `DeclarativeBase` — modern class-based model definition (SQLAlchemy 2.0 style)
  - `Mapped` / `mapped_column` — type-annotated column definitions
  - `relationship()` — defines Python-level associations between models (`User` ↔ `PopulationMatrix` ↔ `SimulationRun`)
  - `JSONB` from `sqlalchemy.dialects.postgresql` — PostgreSQL-specific JSON binary type
  - `SessionLocal` factory — creates database sessions for queries
- **Files:** `db/models.py`, `db/session.py`

### Alembic 1.13+
- **Role:** Database schema migration tool. Tracks schema changes over time so the DB can be evolved without manually writing SQL or dropping and recreating tables.
- **Key features used:**
  - `alembic upgrade head` — applies all pending migrations
  - `alembic downgrade` — rolls back migrations
  - `--autogenerate` — diffs ORM models against the live DB and generates migration code automatically
  - `env.py` — custom entry point that loads credentials from `.env` and connects `Base.metadata` for autogenerate
- **Files:** `alembic.ini`, `alembic/env.py`, `alembic/script.py.mako`, `alembic/versions/`

### psycopg2-binary
- **Role:** PostgreSQL driver for Python. SQLAlchemy uses it under the hood to communicate with the database.
- **Why binary:** The `-binary` variant bundles its own compiled C extensions so no system-level PostgreSQL headers are needed during install.
- **Connection string format:** `postgresql+psycopg2://user:password@host:port/dbname`

### python-dotenv
- **Role:** Loads environment variables from `.env` into `os.environ` at startup.
- **Used in:** `db/session.py` (app runtime) and `alembic/env.py` (migration runtime).
- **Why:** Keeps credentials out of source code and makes the project portable across environments (dev, CI, prod) by swapping the `.env` file.

### pandas + pyarrow
- **Role:** Used in the data pipeline to read and manipulate COMPADRE metadata.
- **Parquet format:** `metadata.parquet` stores the 9146-row metadata table in a columnar binary format — much faster to read than CSV and preserves column types.

### rdata
- **Role:** Parses R's native `.RData` binary format in pure Python.
- **Used in:** `db/seed_compadre.py` (slow path) and `growt-simulator-app/preproccesor.py`.
- **Why:** The COMPADRE database is distributed as an R S4 object inside an `.RData` file. `rdata` converts it to Python dicts and pandas DataFrames without needing R installed.

---

## Data Source

### COMPADRE Plant Matrix Database
- **Version:** 6.25.8.0
- **Format:** R S4 object inside `.RData`
- **Contents:** 9146 population projection matrices from published ecological studies, covering 806 plant species across 4 kingdoms.
- **Structure:**
  - `metadata` slot — DataFrame with 58 columns (species taxonomy, geography, study details)
  - `mat` slot — list of matrix objects, each with `matA`, `matU`, `matF`, `matC`, `MatrixID`
  - `matrixClass` slot — list of DataFrames with stage/life-stage names per matrix
- **Reference:** Salguero-Gómez et al. (2015). COMPADRE: a global database of plant demography. *Journal of Ecology*.

---

## Project File Map

```
population-growth-simulator/
│
├── .env                          # Credentials (gitignored)
├── docker-compose.yml            # PostgreSQL container definition
├── requirements.txt              # Python dependencies
│
├── db/
│   ├── __init__.py
│   ├── models.py                 # SQLAlchemy ORM: User, PopulationMatrix, SimulationRun
│   ├── session.py                # engine + SessionLocal
│   └── seed_compadre.py          # ETL: COMPADRE → population_matrices
│
├── alembic.ini                   # Alembic configuration
└── alembic/
    ├── env.py                    # Migration environment (loads .env, wires metadata)
    ├── script.py.mako            # Template for generated migration files
    └── versions/
        └── 0001_initial_schema.py   # Creates all 3 tables + species index
```
