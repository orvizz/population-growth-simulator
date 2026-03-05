# API Layer — Technology Decision

## Decision

**FastAPI** is chosen as the framework for the interoperability API layer.

---

## Context and constraints

Before evaluating options, the constraints that govern this decision:

| Constraint | Detail |
|---|---|
| Single consumer | The only client is the Shiny (Python) app — no external consumers, no mobile clients, no R scripts hitting the API directly |
| Simulation complexity | Simulations are computationally lightweight (iterative matrix multiplication) — sub-second for typical step counts |
| Language | The entire project is Python — DB models, data pipeline, and frontend |
| Existing stack | SQLAlchemy 2.0 + Alembic already in place; the API must integrate with them without conflict |
| Documentation requirement | Swagger/OpenAPI documentation is a stated requirement |
| Context | Academic TFG project — long-term maintainability and clear documentation matter as much as raw performance |

---

## Why not the alternatives

### GraphQL (Strawberry / Ariadne)
GraphQL's main advantage is flexible client-driven querying — the client specifies exactly which fields and filters it needs. This is valuable when consumers are diverse (researchers querying from R, notebooks, third-party tools) and their data needs are unpredictable.

With a single known consumer (the Shiny app), that flexibility is unnecessary complexity. The Shiny app's data needs are fixed and known in advance. GraphQL also does not integrate with Swagger — it has its own introspection protocol (GraphiQL), which means documenting the API requires learning a separate toolchain. Given that Swagger is a stated goal, GraphQL creates friction without compensating benefit.

**Eliminated:** single known consumer makes flexible querying irrelevant; Swagger incompatibility is a direct conflict with stated goals.

### Litestar
Litestar is technically strong — cleaner dependency injection, OpenAPI 3.1 (vs FastAPI's 3.0), native SQLAlchemy plugin, built-in response caching. For a greenfield project with no constraints, it is a reasonable choice.

The critical issue is ecosystem maturity. As of 2025, FastAPI has ~75k GitHub stars, a massive community, and saturates documentation, tutorials, and Stack Overflow. Litestar has ~6k stars. For an academic project where reproducibility and reference availability matter — and where the next person to work on the code may not be familiar with the framework — choosing a smaller ecosystem introduces unnecessary risk. The technical advantages of Litestar over FastAPI are real but marginal for this use case.

**Eliminated:** smaller ecosystem creates maintenance and reproducibility risk that is not justified by the marginal technical gains.

### Flask + flask-smorest
Flask is synchronous. While the simulations themselves are fast, a synchronous framework serialises all requests through a single thread per worker. This is not a correctness problem at small scale, but it is a structural limitation that has no upside — adding async capability to Flask later requires a different framework entirely (Quart), whereas FastAPI's async is already there.

Flask also requires explicit Swagger setup through `flask-smorest` (additional dependency, additional configuration), whereas FastAPI generates it from existing type annotations at zero extra cost.

**Eliminated:** synchronous limitation with no compensating advantage; Swagger requires extra setup that FastAPI provides for free.

### Django Ninja
Django Ninja provides a FastAPI-like interface on top of Django. Its purpose is to add a type-annotated API layer to existing Django projects. This project uses SQLAlchemy and Alembic, not Django's ORM. Running Django Ninja here means carrying Django's full framework weight (ORM, template engine, admin, migrations system) alongside the existing SQLAlchemy stack — two competing persistence layers. The SQLAlchemy models and Alembic migrations would need to either be replaced or maintained in parallel with Django models.

**Eliminated:** direct conflict with the existing SQLAlchemy + Alembic stack.

### Go (Gin / Chi / Fiber)
Go would produce a fast, small, easily containerised API binary. The performance argument is irrelevant here — the bottleneck is never the framework at this scale. The real cost is introducing a second language: DB schema must be duplicated as Go structs, all existing SQLAlchemy models are abandoned, and any future developer must know both Python and Go to work on the project.

**Eliminated:** polyglot overhead is unjustified for a single-consumer academic project; loses all existing SQLAlchemy infrastructure.

---

## Why FastAPI

Given the constraints, FastAPI is the correct choice on every relevant axis:

### 1. Swagger is free
FastAPI generates a fully interactive OpenAPI 3.0 specification and Swagger UI automatically from Python type annotations. No extra packages, no configuration. The moment a route is defined with Pydantic response models, it appears in `/docs` with request/response schemas, example payloads, and a live "Try it out" button. This directly satisfies the documentation requirement at zero cost.

```python
@app.get("/v1/matrices/{matrix_id}", response_model=MatrixResponse)
async def get_matrix(matrix_id: int, db: Session = Depends(get_db)):
    ...
```

This single function definition produces a documented, testable endpoint in Swagger UI automatically.

### 2. Native SQLAlchemy integration
FastAPI's dependency injection system is designed for exactly this pattern — a database session is injected into route handlers as a dependency, opened per-request and closed automatically. The existing `db/models.py` and `db/session.py` require no changes.

```python
def get_db():
    with SessionLocal() as session:
        yield session

@app.get("/v1/matrices")
async def list_matrices(db: Session = Depends(get_db)):
    return db.query(PopulationMatrix).all()
```

### 3. Pydantic separates the API contract from the DB schema
FastAPI uses Pydantic for request and response validation. This enforces the architectural principle that the API contract and the database schema are independent — a change to `db/models.py` does not automatically change what the API returns. The developer explicitly controls the API surface.

```
db/models.py      →  SQLAlchemy ORM  (database shape)
api/schemas.py    →  Pydantic models (API contract)
```

### 4. Async is available without being required
FastAPI supports both `async def` and regular `def` route handlers. For this project, where simulations are fast and synchronous NumPy operations, regular `def` handlers work without any async complexity. If a future use case requires async (long background jobs, WebSockets for streaming simulation results), the framework supports it natively without migration.

### 5. Ecosystem and community
FastAPI is the dominant Python API framework for new projects as of 2025. This has concrete practical consequences for an academic project:

- Any error message or problem has likely been encountered and documented publicly.
- A future developer or academic reviewer will recognise the framework immediately.
- Integration guides exist for every common pattern: JWT auth, file uploads, background tasks, testing with `pytest`.
- The framework is maintained by a large active community and backed by Pydantic v2, which is itself widely used.

### 6. Deployment is a single Docker service
FastAPI runs on `uvicorn`, an ASGI server. Adding the API to the existing `docker-compose.yml` is a straightforward addition of one service. No extra infrastructure, no message queue, no sidecar processes.

```yaml
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

---

## Consequences of this decision

### Structural consequences

**The Shiny app becomes a pure client.** It will call the API over HTTP instead of importing SQLAlchemy sessions directly. The frontend no longer needs to know anything about the database schema — only about the API's JSON response shapes. This is the core decoupling goal.

**The simulation engine moves to the API.** Currently the simulation logic lives inside the Shiny app. It will migrate to `api/services/simulation.py`, callable from any endpoint. The Shiny app sends `{matrix_id, initial_vector, n_steps}` and receives `{result_history}`.

**A Pydantic schema layer is introduced.** For every DB table there will be a corresponding Pydantic response model in `api/schemas.py`. This is a small amount of code duplication by design — it is what makes the API contract stable even when the DB schema changes.

**Two entry points to the system.** During development, `db/seed_compadre.py` and Alembic still talk to the DB directly (as they should — they are infrastructure tools). The Shiny app goes through the API. These two access patterns coexist intentionally.

### Operational consequences

**One extra service in Docker Compose.** The local dev environment goes from one container (PostgreSQL) to two (PostgreSQL + API). Both are managed with `docker compose up -d`.

**Port convention.** API runs on `8000`. Swagger UI at `http://localhost:8000/docs`. PostgreSQL remains on `5435`.

**The Shiny app needs `httpx` or `requests`.** The frontend dependency on `sqlalchemy` and `psycopg2-binary` can eventually be removed from the Shiny app's own requirements once it no longer queries the DB directly.

### What this decision does not resolve

**Authentication is not yet designed.** The API will initially be open (no auth required), which is fine for a local single-user setup. JWT-based auth can be added as a later layer without changing the endpoint structure.

**The Shiny app is not yet migrated.** The immediate next step is building the API; migrating the Shiny app to call it is a subsequent step.

**The API is not yet versioned in implementation**, only by convention (`/v1/` prefix). Formal version management (deprecation headers, multiple active versions) is not needed at this stage.

---

## Summary

| Question | Answer |
|---|---|
| Framework | FastAPI |
| API paradigm | REST |
| Language | Python |
| Swagger | Auto-generated at `/docs` (zero config) |
| DB integration | Existing SQLAlchemy models reused via DI |
| Async | Available but not required at this scale |
| Deployment | Single `uvicorn` process, one Docker Compose service |
| Next step | Scaffold `api/` package and implement `/v1/matrices` read endpoints |
