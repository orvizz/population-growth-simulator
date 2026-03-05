# Launching the System

The full system has three processes:

| Process | Technology | Port | Purpose |
|---|---|---|---|
| Database | PostgreSQL 16 (Docker) | 5435 | Persistent storage |
| API | FastAPI + uvicorn | 8000 | REST endpoints + Swagger UI |
| Frontend | Shiny (Python) | 8080 | User interface |

For a complete deployment guide (including Docker Compose and first-time setup) see [`DEPLOY.md`](../DEPLOY.md) at the project root.

---

## Quick start — local development

The recommended dev setup runs PostgreSQL in Docker and the other two processes locally with hot-reload.

### 1. Prerequisites

- Python 3.11+, Docker Desktop running
- `.env` file at the project root (see [environment variables](#environment-variables))
- Dependencies: `pip install -r requirements.txt`

### 2. Start the database

```bash
docker compose up -d db
```

### 3. First-time only — apply migrations and seed data

```bash
python -m alembic upgrade head
python -m db.seed_compadre
```

### 4. Start the API (terminal 1)

```bash
python -m uvicorn api.main:app --reload --port 8000
```

### 5. Start the frontend (terminal 2)

```bash
cd frontend
python -m shiny run app.py --reload --port 8080
```

---

## URLs

| URL | Description |
|---|---|
| `http://localhost:8080` | Shiny frontend |
| `http://localhost:8000/health` | API health check |
| `http://localhost:8000/docs` | Swagger UI (interactive) |
| `http://localhost:8000/redoc` | ReDoc (read-only docs) |
| `http://localhost:8000/openapi.json` | Raw OpenAPI 3 spec |

---

## Option B — Full Docker Compose

Runs database and API in containers. The frontend still runs locally (Shiny is not containerised yet).

```bash
docker compose up -d          # builds API image on first run (~1 min)
docker compose exec api python -m alembic upgrade head
docker compose exec api python -m db.seed_compadre

# Frontend still runs locally:
cd frontend && python -m shiny run app.py --reload --port 8080
```

---

## Verifying the API

```bash
# Health
curl http://localhost:8000/health

# Register + login
curl -X POST http://localhost:8000/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{"username":"mario","email":"mario@example.com","password":"secret123"}'

TOKEN=$(curl -s -X POST http://localhost:8000/v1/auth/login \
  -d "username=mario&password=secret123" \
  | python -c "import sys,json; print(json.load(sys.stdin)['access_token'])")

# Create a matrix
curl -X POST http://localhost:8000/v1/matrices \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"species_accepted":"Test species","matrix_a":[[0.5,1.2],[0.3,0.8]],"stage_names":["juvenile","adult"]}'
```

---

## Environment variables

| Variable | Required | Description |
|---|---|---|
| `POSTGRES_USER` | yes | PostgreSQL username |
| `POSTGRES_PASSWORD` | yes | PostgreSQL password |
| `POSTGRES_DB` | yes | Database name (`matrix_db`) |
| `POSTGRES_HOST` | yes | `localhost` locally, `db` inside Docker |
| `POSTGRES_PORT` | yes | `5435` |
| `JWT_SECRET_KEY` | yes | HMAC-SHA256 signing key for JWT tokens |
| `API_BASE_URL` | no | Frontend uses this to find the API. Default: `http://localhost:8000` |

Generate a secure `JWT_SECRET_KEY`:
```bash
python -c "import secrets; print(secrets.token_hex(32))"
```

> `POSTGRES_HOST` is automatically overridden to `db` for the API container in `docker-compose.yml`. The `.env` value (`localhost`) is used only for local development and Alembic migrations.
