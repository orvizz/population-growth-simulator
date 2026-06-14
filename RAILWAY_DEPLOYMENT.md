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
│  [postgres]  ←──  [api]  ←──  [frontend]           │
│  Managed DB        FastAPI       Python Shiny       │
│  (auto URL)        :8000         :8080              │
└─────────────────────────────────────────────────────┘
```

---

## Step 1 — Create a Railway project

1. Go to [railway.app](https://railway.app) and log in.
2. Click **New Project** → **Empty Project**.
3. Name the project (e.g. `population-growth-simulator`).

---

## Step 2 — Add the PostgreSQL database

1. Inside the project, click **+ New**.
2. Select **Database** → **PostgreSQL**.
3. Railway provisions the database instantly and generates a `DATABASE_URL`.

> No configuration needed here. Railway will make `DATABASE_URL` available to other services automatically when you reference it in their variables.

---

## Step 3 — Deploy the API service

### 3.1 Connect the GitHub repo

1. Click **+ New** → **GitHub Repo**.
2. Authorize Railway to access your GitHub if prompted.
3. Select the `population-growth-simulator` repository.
4. Railway detects the `Dockerfile` at the root automatically.

### 3.2 Configure the build

1. Go to the service's **Settings** tab → **Build** section.
2. Confirm **Dockerfile Path** is `Dockerfile` (the root one — this runs Uvicorn by default).
3. Leave **Start Command** empty (the Dockerfile CMD handles it).

### 3.3 Set environment variables

Go to the service's **Variables** tab and add the following:

| Variable | Value | Notes |
|---|---|---|
| `DATABASE_URL` | *(link from PostgreSQL service)* | Click **+ Add Reference** → select the PostgreSQL service → choose `DATABASE_URL` |
| `JWT_SECRET_KEY` | *(generate below)* | Required for auth token signing |
| `CORS_ORIGINS` | `https://<frontend-url>.railway.app` | Fill in after Step 4; leave blank for now and update later |

**Generate a JWT secret key** — run this locally and paste the output:
```bash
openssl rand -hex 32
```
On Windows PowerShell:
```powershell
-join ((1..32) | ForEach-Object { '{0:x2}' -f (Get-Random -Maximum 256) })
```

### 3.4 Note the API public URL

After the first deploy starts, Railway shows a public URL in the service's **Settings → Networking** section — something like `https://api-production-xxxx.railway.app`. Copy this for Step 4.

---

## Step 4 — Deploy the frontend service

### 4.1 Add a second service from the same repo

1. Click **+ New** → **GitHub Repo**.
2. Select the same `population-growth-simulator` repository.

### 4.2 Configure the build

1. Go to **Settings → Build**.
2. Set **Dockerfile Path** to `Dockerfile.frontend`.
3. Leave **Start Command** empty.

### 4.3 Configure the port

1. Go to **Settings → Networking**.
2. Set the **Internal Port** to `8080`.
3. Click **Generate Domain** to get a public URL.

### 4.4 Set environment variables

| Variable | Value | Notes |
|---|---|---|
| `API_BASE_URL` | `https://<api-url>.railway.app` | The public URL from Step 3.4 — no trailing slash |

---

## Step 5 — Wire CORS back to the frontend

Now that the frontend URL is known:

1. Go back to the **API service** → **Variables** tab.
2. Set (or update) `CORS_ORIGINS` to the frontend's Railway URL:
   ```
   CORS_ORIGINS=https://<frontend-url>.railway.app
   ```
3. Click **Deploy** to apply the change.

---

## Step 6 — Verify the deployment

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
- Check that the results appear and are saved under **My Simulations**

---

## Notes

### First deployment — seeding delay

On the very first deploy, `entrypoint.sh` seeds ~18 000 COMPADRE and COMADRE records into the database. This takes **2–3 minutes**. The API will not respond until seeding is complete. Subsequent deploys skip seeding (idempotent check) and start in seconds.

### Redeployments

Railway automatically redeploys the service on every push to the connected branch. Migrations (`alembic upgrade head`) run automatically on each deploy before the API starts — this is safe and idempotent.

### Environment variable reference table (full)

| Variable | Service | Required | Description |
|---|---|---|---|
| `DATABASE_URL` | API | Yes | Injected by Railway PostgreSQL — psycopg2 scheme fixed automatically |
| `JWT_SECRET_KEY` | API | Yes | HMAC-SHA256 key for signing JWT tokens (use 32+ random bytes) |
| `CORS_ORIGINS` | API | Yes | Comma-separated list of allowed frontend origins |
| `API_BASE_URL` | Frontend | Yes | Full public URL of the API service, no trailing slash |

### Rollback

To roll back to a previous deploy, go to the service's **Deployments** tab and click **Rollback** on any prior deployment.
