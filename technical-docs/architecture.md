# Backend Architecture Analysis

## Current state

The project currently has a **direct-access** architecture: the Shiny frontend reads data from pre-processed flat files (`.parquet`, `.json`) at startup and talks directly to the PostgreSQL database through SQLAlchemy. There is no API layer between them.

```
┌─────────────────┐        ┌────────────────┐
│   Shiny (R/Py)  │──────▶│   PostgreSQL   │
│   frontend app  │        │   (Docker)     │
└─────────────────┘        └────────────────┘
         │
         │ reads at startup
         ▼
  .parquet / .json files
```

This works for a single self-contained app, but it has structural problems:

- The frontend is tightly coupled to the database schema — any schema change breaks the app.
- No way to expose data to other consumers (other frontends, scripts, external collaborators).
- Business logic (simulation engine, matrix validation) lives inside the UI code.
- No authentication surface or rate limiting.

---

## Target architecture

Introduce a **REST API** layer between the database and any consumer. The Shiny app becomes just one of potentially many clients.

```
                          ┌──────────────────┐
                          │   Shiny app      │
                          │   (frontend)     │
                          └────────┬─────────┘
                                   │ HTTP
                          ┌────────▼─────────┐
                          │   REST API       │  ◀── Swagger UI
                          │   (Python)       │  ◀── future mobile/web clients
                          └────────┬─────────┘
                                   │ SQLAlchemy
                          ┌────────▼─────────┐
                          │   PostgreSQL     │
                          │   (Docker)       │
                          └──────────────────┘
```

Benefits:
- **Decoupling** — frontend only knows about API contracts (URLs + JSON shapes), not DB schema.
- **Interoperability** — any language or tool can consume the API (R, JavaScript, curl).
- **Single source of truth** — simulation logic lives in the API, not duplicated across clients.
- **Documentation** — Swagger UI auto-documents every endpoint; collaborators can explore and test without reading code.
- **Evolvability** — API versioning (`/v1/`, `/v2/`) lets the DB schema change without breaking existing clients.

---

## Framework options

### Option A — FastAPI ✅ Recommended

FastAPI is a modern Python web framework built on ASGI (async). It generates OpenAPI/Swagger documentation automatically from type annotations.

**Pros:**
- Auto-generates `/docs` (Swagger UI) and `/redoc` from code — zero extra work.
- Native `async`/`await` support — handles concurrent simulation requests efficiently.
- Pydantic models for request/response validation — catches bad input before it hits the DB.
- First-class SQLAlchemy integration.
- Fastest Python web framework in benchmarks (comparable to Node.js/Go for I/O-bound work).
- Actively maintained; the de-facto standard for new Python APIs.

**Cons:**
- Slightly more setup than Flask for very simple cases.
- Async SQLAlchemy requires using `AsyncSession` instead of the current `SessionLocal`.

**Swagger:** Built-in at `/docs`. No extra packages.

```python
# Example — what an endpoint looks like
from fastapi import FastAPI
from pydantic import BaseModel

app = FastAPI()

class MatrixResponse(BaseModel):
    id: int
    species_accepted: str
    kingdom: str | None
    matrix_a: list[list[float | None]]

@app.get("/matrices/{matrix_id}", response_model=MatrixResponse)
async def get_matrix(matrix_id: int):
    ...
```

→ This alone generates a fully interactive Swagger page at `/docs`.

---

### Option B — Flask + flask-smorest

Flask is the classic Python micro-framework. `flask-smorest` adds OpenAPI/Swagger generation on top.

**Pros:**
- Very mature ecosystem; huge amount of documentation and examples.
- Synchronous — simpler mental model, no `async` complexity.
- `flask-smorest` generates clean OpenAPI 3 specs.

**Cons:**
- Synchronous by default — a slow simulation request blocks other requests.
- Swagger requires installing and configuring `flask-smorest` (extra dependency and boilerplate).
- More verbose than FastAPI for the same functionality.
- Pydantic integration is not native (uses Marshmallow schemas instead).

**Swagger:** Via `flask-smorest` at a configurable route.

---

### Option C — Django REST Framework (DRF)

DRF is the API layer built on top of Django, a full-stack web framework.

**Pros:**
- Batteries-included: auth, admin panel, ORM, serializers all built in.
- Mature and battle-tested.
- `drf-spectacular` generates good OpenAPI specs.

**Cons:**
- Heavy — Django brings a full ORM, template engine, etc. that this project doesn't need (it already has SQLAlchemy + Alembic).
- Having two ORM layers (Django ORM + SQLAlchemy) would be a conflict; dropping SQLAlchemy would mean rewriting migrations.
- Significantly more boilerplate for simple endpoints.
- Overkill for a research/academic project.

**Swagger:** Via `drf-spectacular`.

---

### Option D — Litestar

A newer async framework, similar to FastAPI but with a different design philosophy.

**Pros:**
- Auto-generates OpenAPI/Swagger.
- Strong typing and validation.
- SQLAlchemy plugin included.

**Cons:**
- Much smaller community and ecosystem than FastAPI.
- Less documentation and fewer examples.
- Not yet a safe bet for a project that may need community support.

---

## Comparison table

| Criterion | FastAPI | Flask + smorest | Django REST | Litestar |
|---|---|---|---|---|
| Swagger out of the box | ✅ Built-in | ⚠️ Plugin | ⚠️ Plugin | ✅ Built-in |
| Async support | ✅ Native | ⚠️ Limited | ⚠️ Limited | ✅ Native |
| SQLAlchemy integration | ✅ Native | ✅ Works | ❌ Conflicts | ✅ Plugin |
| Pydantic validation | ✅ Native | ❌ Marshmallow | ❌ Serializers | ✅ Native |
| Learning curve | Low | Low | High | Medium |
| Community / ecosystem | Very large | Very large | Very large | Small |
| Boilerplate | Low | Medium | High | Low |
| Fit for this project | ✅ Best | ⚠️ Acceptable | ❌ Too heavy | ⚠️ Risky |

---

## API design — proposed endpoints

Regardless of framework, these are the logical endpoints the API should expose.

### Matrices

| Method | Path | Description |
|---|---|---|
| `GET` | `/v1/matrices` | List matrices (paginated, filterable by species, kingdom, country) |
| `GET` | `/v1/matrices/{id}` | Get a single matrix with all sub-matrices and stage names |
| `POST` | `/v1/matrices` | Create a custom matrix (authenticated) |
| `PUT` | `/v1/matrices/{id}` | Update a matrix (authenticated, owner only) |
| `DELETE` | `/v1/matrices/{id}` | Delete a matrix (authenticated, owner only) |
| `GET` | `/v1/matrices/search?q=Abies` | Full-text search on species name |

### Simulations

| Method | Path | Description |
|---|---|---|
| `POST` | `/v1/simulate` | Run a simulation: takes `matrix_id`, `initial_vector`, `n_steps` |
| `GET` | `/v1/simulations/{id}` | Retrieve a stored simulation result |
| `GET` | `/v1/simulations` | List simulations for the authenticated user |

### Users

| Method | Path | Description |
|---|---|---|
| `POST` | `/v1/auth/register` | Create account |
| `POST` | `/v1/auth/login` | Get JWT token |
| `GET` | `/v1/users/me` | Current user profile |

### Meta

| Method | Path | Description |
|---|---|---|
| `GET` | `/health` | Health check (DB connectivity) |
| `GET` | `/docs` | Swagger UI (FastAPI built-in) |
| `GET` | `/openapi.json` | Raw OpenAPI 3 spec |

---

## Decoupling strategy

### 1. Pydantic schemas separate from ORM models

Never return SQLAlchemy model objects directly. Define separate Pydantic response schemas. This means the DB schema and the API contract can evolve independently.

```
db/models.py          → SQLAlchemy (database layer)
api/schemas.py        → Pydantic (API contract layer)
api/routers/          → FastAPI route handlers
```

### 2. Service layer

Put business logic (running simulations, validating matrices) in a `services/` module, separate from both the DB models and the route handlers. Route handlers only handle HTTP concerns (parsing input, returning responses).

```
api/routers/matrices.py  → HTTP: parse request, call service, return response
services/simulation.py   → Logic: matrix multiplication, eigenvalue, etc.
db/models.py             → Persistence: read/write to PostgreSQL
```

### 3. API versioning

Prefix all routes with `/v1/`. When breaking changes are needed, add `/v2/` routes without removing `/v1/`, giving consumers time to migrate.

### 4. Shiny app as a client

The Shiny frontend calls the API over HTTP instead of importing `db.session` directly. This means the frontend and backend can be deployed separately, scaled independently, or replaced entirely.

```python
# Shiny app — instead of querying DB directly:
import httpx
matrices = httpx.get("http://localhost:8000/v1/matrices?kingdom=Plantae").json()
```

---

## Recommended next steps

1. **Add FastAPI** to `requirements.txt` (`fastapi`, `uvicorn[standard]`, `pydantic>=2`).
2. **Create `api/` package** with `main.py`, `routers/`, `schemas.py`.
3. **Wire SQLAlchemy** sessions into FastAPI's dependency injection system.
4. **Start with `/v1/matrices`** (read-only) — this unblocks the Shiny app from querying the DB directly.
5. **Add `/v1/simulate`** — moves the simulation engine out of the Shiny app.
6. **Deploy both services** with Docker Compose (add an `api` service alongside `db`).

```yaml
# docker-compose.yml addition
services:
  db:
    image: postgres:16-alpine
    ...
  api:
    build: .
    command: uvicorn api.main:app --host 0.0.0.0 --port 8000 --reload
    ports:
      - "8000:8000"
    env_file: .env
    depends_on:
      db:
        condition: service_healthy
```

Swagger UI will then be accessible at `http://localhost:8000/docs` automatically.
