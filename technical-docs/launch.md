# Launching the Backend

The backend consists of two processes:

| Process | Role | Default port |
|---|---|---|
| PostgreSQL (Docker) | Database | 5435 |
| FastAPI (uvicorn) | REST API + Swagger | 8000 |

---

## Prerequisites

- Python 3.11+
- Docker Desktop running
- Dependencies installed: `pip install -r requirements.txt`
- `.env` file at the project root (see below)

### Required `.env` variables

```
POSTGRES_USER=postgres
POSTGRES_PASSWORD=your_password
POSTGRES_DB=matrix_db
POSTGRES_HOST=localhost
POSTGRES_PORT=5435

JWT_SECRET_KEY=change_this_to_a_long_random_string
```

> **Security:** `JWT_SECRET_KEY` signs every auth token. Use a strong random value in any environment that is not purely local. Generate one with:
> ```bash
> python -c "import secrets; print(secrets.token_hex(32))"
> ```

---

## Option A — Local development (recommended)

Run the database in Docker and the API directly with Python. Hot-reload is active so code changes apply immediately.

### Step 1 — Start the database

```bash
docker compose up -d db
```

### Step 2 — Apply migrations (first time, or after pulling new migrations)

```bash
python -m alembic upgrade head
```

### Step 3 — Start the API

```bash
python -m uvicorn api.main:app --reload --port 8000
```

The API is now available at:

| URL | Description |
|---|---|
| `http://localhost:8000/health` | Health check |
| `http://localhost:8000/docs` | Swagger UI (interactive) |
| `http://localhost:8000/redoc` | ReDoc (read-only docs) |
| `http://localhost:8000/openapi.json` | Raw OpenAPI 3 spec |

### Step 4 — (First time only) Seed COMPADRE data

```bash
python -m db.seed_compadre
```

---

## Option B — Full Docker Compose

Runs both PostgreSQL and the API in containers. Useful for testing deployment behaviour or sharing a reproducible environment.

```bash
docker compose up -d
```

On first run this builds the API image (~1 minute). Subsequent starts are instant.

Apply migrations and seed from inside the container:

```bash
docker compose exec api python -m alembic upgrade head
docker compose exec api python -m db.seed_compadre
```

The API is available at the same URLs as Option A. Hot-reload is active because the source directory is mounted as a volume.

### Stopping

```bash
docker compose down          # stop, keep data
docker compose down -v       # stop, delete all data
```

---

## Verifying the API is working

### Health check

```bash
curl http://localhost:8000/health
# {"status":"ok"}
```

### Register a user and create a matrix

```bash
# Register
curl -X POST http://localhost:8000/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{"username":"mario","email":"mario@example.com","password":"secret123"}'

# Login — get token
TOKEN=$(curl -s -X POST http://localhost:8000/v1/auth/login \
  -d "username=mario&password=secret123" | python -c "import sys,json; print(json.load(sys.stdin)['access_token'])")

# Create a matrix
curl -X POST http://localhost:8000/v1/matrices \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"species_accepted":"Test species","matrix_a":[[0.5,1.2],[0.3,0.8]],"stage_names":["juvenile","adult"]}'
```

### Explore via Swagger

Open `http://localhost:8000/docs` in a browser. Click **Authorize**, enter your Bearer token, and try any endpoint interactively.

---

## Environment variable reference

| Variable | Required | Description |
|---|---|---|
| `POSTGRES_USER` | yes | PostgreSQL username |
| `POSTGRES_PASSWORD` | yes | PostgreSQL password |
| `POSTGRES_DB` | yes | Database name (`matrix_db`) |
| `POSTGRES_HOST` | yes | Host (`localhost` locally, `db` in Docker) |
| `POSTGRES_PORT` | yes | Port (`5435`) |
| `JWT_SECRET_KEY` | yes | HMAC-SHA256 signing key for JWT tokens |

> When running the API inside Docker Compose, `POSTGRES_HOST` is automatically overridden to `db` (the service name) in `docker-compose.yml`. The `.env` value (`localhost`) is only used for local development.
