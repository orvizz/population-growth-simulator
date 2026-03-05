# Backend Architecture

## Implemented architecture

The system is made up of three independent processes that communicate over HTTP:

```
┌──────────────────────────────────────────────────────┐
│  frontend/app.py                                     │
│  Shiny (Python)  :8080                               │
│  Browse matrices · Create/edit · Auth UI             │
└─────────────────────────┬────────────────────────────┘
                          │ HTTP  (httpx)
                          │
┌─────────────────────────▼────────────────────────────┐
│  api/                                                │
│  FastAPI  :8000                                      │
│  /docs (Swagger) · /v1/auth · /v1/matrices           │
│                                                      │
│  controllers/ → services/ → repositories/            │
└─────────────────────────┬────────────────────────────┘
                          │ SQLAlchemy + psycopg2
                          │
┌─────────────────────────▼────────────────────────────┐
│  PostgreSQL 16  :5435  (Docker)                      │
│  matrix_db                                           │
│  users · population_matrices · simulation_runs       │
└──────────────────────────────────────────────────────┘
```

The frontend never touches the database. The database is never exposed outside Docker. All data access goes through the API.

---

## Internal API layer structure

The `api/` package is split into four layers. Each layer only imports from the layer directly below it.

```
HTTP request
     │
     ▼
┌─────────────────────────────────────────────────────────────────┐
│  controllers/                                                   │
│  auth.py · matrices.py                                          │
│                                                                 │
│  Responsibility: HTTP only.                                     │
│  Parse request → call service → return record.                  │
│  No business logic. No SQL.                                     │
└────────────────────────────┬────────────────────────────────────┘
                             │ calls
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│  services/                                                      │
│  auth_service.py · matrix_service.py                            │
│                                                                 │
│  Responsibility: business rules.                                │
│  Owns all domain decisions:                                     │
│    - COMPADRE matrices are immutable                            │
│    - Only the owner can modify a custom matrix                  │
│    - Username/email uniqueness                                  │
│    - Password hashing and verification                          │
│  Raises HTTPException on rule violations.                       │
│  Returns domain Records (never ORM objects).                    │
└────────────────────────────┬────────────────────────────────────┘
                             │ calls
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│  repositories/                                                  │
│  user_repository.py · matrix_repository.py                     │
│                                                                 │
│  Responsibility: pure data access.                              │
│  All SQL lives here and only here.                              │
│  No business logic. No HTTP concerns.                           │
│  Returns SQLAlchemy ORM objects.                                │
└────────────────────────────┬────────────────────────────────────┘
                             │ uses
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│  db/                                                            │
│  models.py · session.py                                         │
│                                                                 │
│  SQLAlchemy ORM definitions. Managed by Alembic migrations.     │
└─────────────────────────────────────────────────────────────────┘
```

---

## Data models

Two distinct model types cross different layer boundaries:

### Schemas (`api/schemas.py`) — input DTOs

Pydantic models that validate data arriving at the HTTP boundary. Used only as function parameters in controllers. Never returned.

Validators implemented:
- `matrix_a` must be square (n×n)
- `matrix_u` and `matrix_f`, if provided, must match `matrix_a` dimensions
- `stage_names` length must equal matrix dimension
- `username` must not contain spaces
- `password` minimum 8 characters

```
HTTP request body ──▶ Schema (validated) ──▶ service method argument
```

### Records (`api/records.py`) — domain objects

Pydantic models with `from_attributes=True`. Constructed by services from ORM objects. Used as FastAPI `response_model` targets. Never used for input.

```
ORM object ──▶ Record.model_validate(orm_obj) ──▶ controller return ──▶ JSON response
```

The separation means the database schema and the API response shape can diverge independently. For example, `PopulationMatrix.metadata_` (the ORM attribute name) is exposed as `"metadata"` in `MatrixRecord` without changing either the DB or the controller.

---

## Dependency injection

FastAPI's DI system wires the layers together at request time. The chain is:

```
get_db()                      # yields SQLAlchemy Session
  └─▶ get_auth_service()      # constructs AuthService(UserRepository(db))
  └─▶ get_matrix_service()    # constructs MatrixService(MatrixRepository(db))
        └─▶ get_current_user() # decodes JWT → AuthService.get_by_id() → UserRecord
```

Tests override `get_db()` to inject a test session. Because FastAPI propagates overrides through the full DI chain, all services and repositories automatically use the test database.

---

## Implemented endpoints

### Auth — `/v1/auth`

| Method | Path | Auth | Description |
|---|---|---|---|
| `POST` | `/v1/auth/register` | — | Create account |
| `POST` | `/v1/auth/login` | — | Get JWT Bearer token |

### Matrices — `/v1/matrices`

| Method | Path | Auth | Description |
|---|---|---|---|
| `GET` | `/v1/matrices` | — | List (paginated, filterable by species/kingdom/country/source) |
| `GET` | `/v1/matrices/{id}` | — | Full matrix with A/U/F data |
| `POST` | `/v1/matrices` | required | Create custom matrix — caller becomes owner |
| `PATCH` | `/v1/matrices/{id}` | required + owner | Partial update — COMPADRE matrices always 403 |

### Meta

| Method | Path | Description |
|---|---|---|
| `GET` | `/health` | Health check |
| `GET` | `/docs` | Swagger UI |
| `GET` | `/redoc` | ReDoc |
| `GET` | `/openapi.json` | Raw OpenAPI 3 spec |

---

## Access control rules

All rules are enforced in the service layer, not in controllers or repositories:

| Action | Rule |
|---|---|
| Read any matrix | Public — no auth required |
| Create matrix | JWT required — caller becomes `owner_id` |
| Edit matrix | JWT required + `owner_id == current_user.id` |
| Edit COMPADRE matrix | Always 403 regardless of auth |
| COMPADRE `source_type` | Set only by seeder — cannot be set via API |

---

## What was deliberately left out

These are known limitations, not bugs. They represent the next implementation phase.

| Feature | Status | Notes |
|---|---|---|
| `DELETE /v1/matrices/{id}` | Not implemented | Straightforward addition — same ownership guard as PATCH |
| `POST /v1/simulate` | Not implemented | Simulation engine still lives in `growt-simulator-app/` |
| `GET /v1/users/me` | Not implemented | No profile management needed yet |
| API versioning enforcement | Convention only | Routes are prefixed `/v1/` but no version middleware |
| Token refresh | Not implemented | Tokens expire after 7 days |
| Rate limiting | Not implemented | No traffic management needed at current scale |

---

## Historical context

Before this architecture was implemented, the project used a direct-access model: the Shiny app read pre-processed flat files (`.parquet`, `.json`) at startup and queried the database through SQLAlchemy imports. This was replaced by the API layer described above. The original files (`growt-simulator-app/preproccesor.py`, `loader.py`, etc.) are preserved in `growt-simulator-app/` for reference but are no longer part of the active data flow.

The framework selection process and the rationale for choosing FastAPI over alternatives are documented in [`api-decision.md`](api-decision.md).
