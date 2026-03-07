# Population Growth Simulator

[![CI](https://github.com/orvizz/population-growth-simulator/actions/workflows/ci.yml/badge.svg)](https://github.com/orvizz/population-growth-simulator/actions/workflows/ci.yml)
[![Coverage](https://codecov.io/gh/orvizz/population-growth-simulator/branch/main/graph/badge.svg)](https://codecov.io/gh/orvizz/population-growth-simulator)
[![Security](https://github.com/orvizz/population-growth-simulator/actions/workflows/security.yml/badge.svg)](https://github.com/orvizz/population-growth-simulator/actions/workflows/security.yml)

A web application for modelling and visualising population dynamics using **stage-structured matrix models**. It ships with the full [COMPADRE Plant Matrix Database](https://compadre-db.org/) (6 000+ matrices across plants, animals and fungi) and lets authenticated users build, share and simulate their own custom matrices.

---

## Features

- **Browse** — search the COMPADRE database by species, kingdom, country and source. Inspect projection matrices (A, U, F) for any entry.
- **Deterministic simulation** — project a population forward using a single matrix: `v(t+1) = A · v(t)`.
- **Stochastic simulation** — provide two or more matrices; at each step one is chosen uniformly at random, producing an ensemble trajectory. Results are reproducible via a random seed.
- **Simulation workspace** — open any saved simulation as a project: re-run with new parameters, save-as-new, download as JSON, or delete.
- **Custom matrices** — authenticated users can create their own matrices with full metadata (species, kingdom, country, life-history stages).
- **Visibility & sharing** — matrices are private by default. Owners can make them public or share them with specific users.
- **Security pipeline** — Bandit SAST, pip-audit CVE scan, Trivy container scan, and GitHub CodeQL run on every push.

---

## Architecture

```
frontend/app.py          →   api/ (FastAPI)   →   db/ (PostgreSQL)
  Shiny for Python            REST API              SQLAlchemy + Alembic
  port 8080                   port 8000
```

The API follows a strict three-layer separation:

| Layer | Location | Responsibility |
|---|---|---|
| Controller | `api/controllers/` | HTTP parsing, routing, response serialisation |
| Service | `api/services/` | Business logic, ownership rules, simulation algorithm |
| Repository | `api/repositories/` | Database queries only |

---

## Quick start (Docker — recommended)

### Prerequisites

- [Docker Desktop](https://www.docker.com/products/docker-desktop/) (or Docker Engine + Compose)

### 1 — Clone and configure

```bash
git clone https://github.com/<YOUR_USERNAME>/population-growth-simulator.git
cd population-growth-simulator
```

Create a `.env` file in the project root (never committed):

```env
POSTGRES_USER=postgres
POSTGRES_PASSWORD=changeme
POSTGRES_DB=matrix_db
POSTGRES_HOST=localhost
POSTGRES_PORT=5435
JWT_SECRET_KEY=change-me-in-production
```

### 2 — Build and start

```bash
make up
```

On Windows without `make`:

```bash
docker compose up -d --build
```

On first startup the entrypoint automatically:
1. Runs all Alembic migrations.
2. Seeds the COMPADRE database (~6 000 matrices, takes ~30 s).

### 3 — Open in your browser

| Service | URL |
|---|---|
| Frontend (Shiny) | http://localhost:8080 |
| REST API | http://localhost:8000 |
| Interactive API docs | http://localhost:8000/docs |

### Useful commands

```bash
make logs        # follow logs from all services
make logs-api    # follow API logs only
make down        # stop containers (data preserved)
make clean       # stop and delete all volumes (full reset)
```

---

## Running locally (without Docker)

### Prerequisites

- Python 3.13+
- PostgreSQL 16+

### Install dependencies

```bash
pip install -r requirements.txt
```

### Set up the database

Create the database and apply migrations:

```bash
createdb matrix_db
python -m alembic upgrade head
python -m db.seed_compadre          # seed COMPADRE data (one-time)
```

### Start the services

```bash
# Terminal 1 — API
python -m uvicorn api.main:app --reload --port 8000

# Terminal 2 — Frontend
cd frontend
python -m shiny run app.py --reload --port 8080
```

---

## API reference

Authentication uses JWT Bearer tokens (7-day expiry). Obtain a token via `POST /v1/auth/login`.

| Method | Path | Auth | Description |
|---|---|---|---|
| GET | `/health` | No | Health check |
| POST | `/v1/auth/register` | No | Create account |
| POST | `/v1/auth/login` | No | Login → JWT token |
| GET | `/v1/matrices` | Optional | List / filter matrices |
| GET | `/v1/matrices/{id}` | Optional | Get matrix detail |
| POST | `/v1/matrices` | Yes | Create custom matrix |
| PATCH | `/v1/matrices/{id}` | Yes | Update own matrix |
| GET | `/v1/matrices/{id}/shares` | Owner | List shares |
| POST | `/v1/matrices/{id}/shares` | Owner | Share with a user |
| DELETE | `/v1/matrices/{id}/shares/{uid}` | Owner | Remove a share |
| POST | `/v1/simulations` | Yes | Run and store simulation |
| GET | `/v1/simulations` | Yes | List own simulations |
| GET | `/v1/simulations/{id}` | Yes | Get simulation + history |
| DELETE | `/v1/simulations/{id}` | Yes | Delete simulation |

Full interactive documentation is available at `/docs` (Swagger UI) when the API is running.

---

## Matrix visibility

| State | Who can access |
|---|---|
| `private` *(default)* | Owner only |
| `shared` | Owner + explicitly listed users |
| `public` | Everyone, including unauthenticated users |

COMPADRE matrices are always `public`. Owners can change visibility at any time via `PATCH /v1/matrices/{id}`. Adding the first share auto-promotes a private matrix to `shared`; removing the last share auto-demotes it back to `private`.

---

## Running the tests

### Unit tests (no database required)

```bash
python -m pytest tests/unit/ -v
```

### Full test suite (requires PostgreSQL)

```bash
python -m pytest tests/ -v
```

The integration test fixture automatically creates and tears down a `matrix_db_test` database.

### Coverage report

```bash
python -m pytest tests/ --cov=api --cov=db --cov-report=term-missing
```

---

## CI / CD

All checks run automatically on every push and pull request to `main`.

| Workflow | Description |
|---|---|
| `ci.yml` | Unit tests → integration tests → coverage upload to Codecov |
| `security.yml` | Bandit (SAST), pip-audit (CVE scan), Trivy (container scan) |
| `codeql.yml` | GitHub CodeQL deep static analysis |
| `dependabot.yml` | Weekly dependency update PRs (pip, Actions, Docker) |

---

## Environment variables

| Variable | Description | Example |
|---|---|---|
| `POSTGRES_USER` | Database user | `postgres` |
| `POSTGRES_PASSWORD` | Database password | `changeme` |
| `POSTGRES_DB` | Database name | `matrix_db` |
| `POSTGRES_HOST` | Database host | `localhost` |
| `POSTGRES_PORT` | Host-side port | `5435` |
| `JWT_SECRET_KEY` | Secret for signing JWT tokens | *(long random string)* |
| `API_BASE_URL` | Frontend → API URL (optional) | `http://localhost:8000` |

---

## Project structure

```
population-growth-simulator/
├── api/                    # FastAPI application
│   ├── controllers/        # HTTP layer
│   ├── services/           # Business logic
│   ├── repositories/       # Database access
│   ├── schemas.py          # Input validation (Pydantic)
│   ├── records.py          # Output models (Pydantic)
│   └── deps.py             # Dependency injection
├── db/                     # Database layer
│   ├── models.py           # SQLAlchemy ORM models
│   ├── session.py          # Session factory
│   └── seed_compadre.py    # COMPADRE seeder
├── alembic/                # Database migrations
│   └── versions/
├── frontend/               # Shiny for Python UI
│   ├── app.py              # Entry point
│   └── components/         # Tab components
├── tests/                  # Test suite
│   ├── unit/               # Unit tests (no DB)
│   └── *.py                # Integration tests
├── docs/                   # Documentation and decisions log
├── docker-compose.yml
├── Dockerfile
└── Makefile
```

---

## Contributing

1. Fork the repository and create a feature branch.
2. Make your changes and add tests.
3. Ensure all tests pass: `python -m pytest tests/ -v`
4. Open a pull request against `main`.

---

## License

This project is licensed under the MIT License. See [LICENSE](LICENSE) for details.

COMPADRE Plant Matrix Database data is used under the terms of the [COMPADRE data use agreement](https://compadre-db.org/Help/DataUse).
