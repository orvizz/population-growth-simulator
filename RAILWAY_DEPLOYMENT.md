# Railway Deployment Guide

This guide walks through deploying the Population Growth Simulator on Railway using GitHub integration. The project becomes three Railway services: a managed PostgreSQL database, an API service (FastAPI), and a frontend service (Python Shiny).

---

## Prerequisites

- A [Railway](https://railway.app) account
- This repository pushed to GitHub
- The code changes from this repo already applied:
  - `api/main.py` reads CORS origins from `CORS_ORIGINS` env var
  - `db/session.py` and `alembic/env.py` support `DATABASE_URL`
  - `Dockerfile.frontend` exists at the repo root

---

## Architecture on Railway

```
┌─────────────────────────────────────────────────────┐
│  Railway Project                                    │
│                                                     │
│  [Postgres]  ←──  [api]  ←──  [frontend]           │
│  Managed DB        FastAPI       Python Shiny       │
│  (auto URL)        :8000         :8080              │
└─────────────────────────────────────────────────────┘
```

> Service names in Railway are **case-sensitive** and must match exactly when using `${{ }}` references. This guide uses `Postgres`, `api`, and `frontend` — rename to match whatever you call your services.

---

## Step 1 — Create a Railway project

1. Go to [railway.app](https://railway.app) and log in.
2. Click **New Project** → **Empty Project**.
3. Name the project (e.g. `population-growth-simulator`).

---

## Step 2 — Add the PostgreSQL database

1. Inside the project, click **+ New**.
2. Select **Database** → **PostgreSQL**.
3. Railway provisions the database instantly. The service will be named **Postgres** by default.

> No extra configuration needed. Other services reference it with `${{Postgres.DATABASE_URL}}`.

---

## Step 3 — Deploy the API service

### 3.1 Connect the GitHub repo

1. Click **+ New** → **GitHub Repo**.
2. Authorize Railway to access your GitHub if prompted.
3. Select the `population-growth-simulator` repository.
4. Name this service **`api`**.

### 3.2 Configure the build

1. Go to the service's **Settings** tab → **Build** section.
2. Confirm **Dockerfile Path** is `Dockerfile` (the root one — runs Uvicorn by default).
3. Leave **Start Command** empty.

### 3.3 Set environment variables

Go to the service's **Variables** tab and add the following:

| Variable | Value |
|---|---|
| `DATABASE_URL` | `${{Postgres.DATABASE_URL}}` |
| `JWT_SECRET_KEY` | *(generate below)* |
| `CORS_ORIGINS` | `https://${{frontend.RAILWAY_PUBLIC_DOMAIN}}` |

**Generate a JWT secret key** — run this locally and paste the output:
```bash
openssl rand -hex 32
```
On Windows PowerShell:
```powershell
-join ((1..32) | ForEach-Object { '{0:x2}' -f (Get-Random -Maximum 256) })
```

> `CORS_ORIGINS` uses a `${{ }}` reference to the frontend service's public domain. Railway resolves this automatically — no need to hard-code the URL.

---

## Step 4 — Deploy the frontend service

### 4.1 Add a second service from the same repo

1. Click **+ New** → **GitHub Repo**.
2. Select the same `population-growth-simulator` repository.
3. Name this service **`frontend`**.

### 4.2 Configure the build

1. Go to **Settings → Build**.
2. Set **Dockerfile Path** to `Dockerfile.frontend`.
3. Leave **Start Command** empty.

### 4.3 Configure the port

1. Go to **Settings → Networking**.
2. Set the **Internal Port** to `8080`.
3. Click **Generate Domain** to get a public URL.

### 4.4 Set environment variables

| Variable | Value |
|---|---|
| `API_BASE_URL` | `https://${{api.RAILWAY_PUBLIC_DOMAIN}}` |

> This references the API service's public domain automatically. If you named your API service something other than `api`, replace it accordingly.

---

## Step 5 — Verify the deployment

Run these checks in order:

**1. API health check**
```bash
curl https://<api-url>.railway.app/health
# Expected: {"status":"ok"}
```

**2. API docs**

Open `https://<api-url>.railway.app/docs` in a browser — Swagger UI should load.

**3. Frontend**

Open `https://<frontend-url>.railway.app` — the Shiny app should load and the **Browse Matrices** tab should list COMPADRE data.

**4. End-to-end flow**

- Register a new user account
- Log in
- Go to **Simulate** → pick a matrix → run a simulation
- Check that the results appear and are saved

---

## Notes

### First deployment — seeding delay

On the very first deploy, `entrypoint.sh` seeds ~18 000 COMPADRE and COMADRE records into the database. This takes **2–3 minutes**. The API will not respond until seeding is complete. Subsequent deploys skip seeding (idempotent check) and start in seconds.

### Redeployments

Railway automatically redeploys the service on every push to the connected branch. Migrations (`alembic upgrade head`) run automatically on each deploy before the API starts — this is safe and idempotent.

### Full environment variable reference

| Variable | Service | Value |
|---|---|---|
| `DATABASE_URL` | api | `${{Postgres.DATABASE_URL}}` |
| `JWT_SECRET_KEY` | api | 32-byte hex string (generate with `openssl rand -hex 32`) |
| `CORS_ORIGINS` | api | `https://${{frontend.RAILWAY_PUBLIC_DOMAIN}}` |
| `API_BASE_URL` | frontend | `https://${{api.RAILWAY_PUBLIC_DOMAIN}}` |

### Rollback

To roll back to a previous deploy, go to the service's **Deployments** tab and click **Rollback** on any prior deployment.
