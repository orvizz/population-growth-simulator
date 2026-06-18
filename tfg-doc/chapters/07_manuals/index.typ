// chapters/07_manuals/index.typ
#import "../../template.typ": guia

// Pull in all tables defined for this chapter
#let t = {
  import "tables.typ": railway-env-vars-table, docker-make-targets-table
  (
    railway-env-vars: railway-env-vars-table,
    docker-make-targets: docker-make-targets-table,
  )
}

= Manuals

#guia[In the event that manuals are included, a clear distinction must be made
regarding their target audience, especially between technical manuals (e.g.,
installation, operation) and user manuals.

Typically, in a manual for an end user, it is more important to show them how they can
perform their processes using the application rather than providing a detailed guide of
every single screen. Conversely, in an installation manual, it can be crucial to
provide very detailed information to reproduce the installation environment.]

== User Manual

#guia[Focus on use cases and the value provided to the end user. Use screenshots to
illustrate the main workflows.]

== Installation and Configuration Manual

The project can be run in three ways: executing each component manually on
the host machine, running the full stack with Docker Compose, or deploying
to production on Railway. The first is best suited to active development and
debugging (hot-reload, no container overhead); the second reproduces the
full multi-service environment locally with a single command; the third is
how the live deployment is operated.

=== Manual Execution (Without Docker) <sec:manual-execution>

*Prerequisites:* Python 3.13+ and PostgreSQL 16+ installed locally.

+ *Install dependencies* - `pip install -r requirements.txt`.
+ *Set up the database* - create the database and bring the schema up to
  date:
  ```bash
  createdb matrix_db
  python -m alembic upgrade head
  python -m db.seed_compadre   # one-time COMPADRE seed
  ```
  Unlike the Docker entrypoint (@sec:docker-deployment), this seed command
  has no idempotency guard - re-running it manually would re-insert
  duplicate matrices, so it should only be run once against a fresh
  database.
+ *Start the services*, each in its own terminal:
  ```bash
  # Terminal 1 - API
  python -m uvicorn api.main:app --reload --port 8000

  # Terminal 2 - Frontend
  cd frontend
  python -m shiny run app.py --reload --port 8080
  ```
  The `--reload` flag enables hot-reload on source changes, which is the
  main reason to prefer this method during development.

=== Docker Deployment <sec:docker-deployment>

Running `make up` (`docker compose up -d --build`) builds and starts three
containers: `db`, `api`, and `frontend`. @fig:docker-deployment shows the
three containers running locally, each printing connection logs as the
frontend and API exchange requests.

#figure(
  image("../../resources/img/docker-deployment.png", width: 90%),
  caption: [Docker Desktop view of the three running containers (`frontend`, `api`, `db`) after `make up`.],
) <fig:docker-deployment>

- *`db`* uses the official `postgres:16-alpine` image with no custom build.
  Data persists across restarts in the named volume `postgres_data`. A
  `pg_isready` healthcheck gates startup of the other two services, so they
  only start once the database is actually accepting connections.
- *`api`* is built from the root `Dockerfile`: a `python:3.13-slim` base
  image installs `requirements.txt`, copies the source tree, and sets
  `entrypoint.sh` as the container `ENTRYPOINT`. On every start, the
  entrypoint runs `alembic upgrade head`, then seeds COMPADRE only if zero
  COMPADRE rows already exist, then seeds COMADRE only if zero COMADRE rows
  already exist, and finally `exec`s into the container's `CMD` (Uvicorn).
  This makes startup idempotent - restarting the container never
  re-seeds or fails on already-applied migrations.
- *`frontend`* is, perhaps counter-intuitively, built from the *same root
  `Dockerfile`* as `api` (`docker-compose.yml` declares `build: .` with no
  `dockerfile:` override) - it only overrides the container `command:` to
  launch Shiny instead of Uvicorn. In practice this means the frontend
  container also runs the same idempotent migration/seed check on startup,
  which is harmless but redundant. A separate, entrypoint-less
  `Dockerfile.frontend` exists specifically for the Railway deployment
  (@sec:railway-deployment), so that the frontend service there does not
  redundantly attempt migrations in production.

Host-to-container port mapping is `5435 → 5432` for the database (the host
port avoids colliding with a locally installed PostgreSQL on the default
port) and a direct `8000`/`8080` mapping for `api`/`frontend`.
@tab:docker-make-targets lists the available Makefile shortcuts.

#t.docker-make-targets

=== Railway Deployment <sec:railway-deployment>

The application is deployed on Railway using its GitHub integration, across
two environments (@sec:railway-environments). Each environment is composed
of three services that mirror the Docker Compose setup: a managed
PostgreSQL database, an `api` service (FastAPI, built from the root
`Dockerfile`), and a `frontend` service (Python Shiny, built from
`Dockerfile.frontend`).

==== Architecture <sec:railway-architecture>

Railway provisions PostgreSQL automatically when added to the project; no
manual database configuration is required. The `api` and `frontend` services
are each connected to the same GitHub repository as a separate service, with
the Dockerfile path set per service in its Settings → Build configuration.
Services reference one another through Railway's `${{ }}` variable
interpolation rather than hard-coded URLs - for example, the API's CORS
configuration points at the frontend's public domain, and the frontend's API
client points back at the API's public domain. This means a service's public
URL can change (e.g. on a custom domain change) without requiring a manual
update to the other service.

#figure(
  image("../../resources/img/railway-deployment.png", width: 80%),
  caption: [Railway `production` environment project canvas: the database service feeds the API service (labelled `backend` in this deployment), which in turn serves the `frontend` service at its public domain.],
) <fig:railway-deployment>

==== Environments <sec:railway-environments>

The Railway project defines two environments, each provisioning its own
independent copy of the three services and database:

- *`production`* tracks the `main` branch and is routed to the custom domain
  `https://popgrowthsim.marioorviz.dev`.
- *`staging`* tracks the `dev` branch and is reachable only at its
  Railway-generated `*.railway.app` domain - no custom domain is configured
  for it.

Because the two environments are fully isolated, pushing to `dev` redeploys
and verifies a change on `staging` without any risk to the live
`production` environment; merging `dev` into `main` is what triggers the
corresponding `production` redeploy.

==== Environment Variables <sec:railway-env>

#t.railway-env-vars

The `JWT_SECRET_KEY` value is a 32-byte hex string generated once per
environment (`openssl rand -hex 32`) and must be kept confidential -
unlike the CI environment, it is never a placeholder in production.

==== Operational Notes <sec:railway-operations>

On the very first deploy, `entrypoint.sh` seeds around 18,000 COMPADRE and
COMADRE records into the database, which takes 2-3 minutes; the API does not
respond until seeding completes. The check is idempotent, so subsequent
deploys skip it and start in seconds. Railway automatically redeploys each
service on every push to its connected branch, running Alembic migrations
(`alembic upgrade head`) before the API starts. To roll back, the
*Deployments* tab of a service lists prior deploys with a one-click
*Rollback* action.

=== Deployment Verification <sec:deployment-verification>

Regardless of which method was used, the following checks confirm the
system is running correctly (substitute the appropriate base URL - local
host/port or the public Railway domain):

+ *API health check* - `GET /health` returns `{"status": "ok"}`.
+ *API docs* - the Swagger UI at `/docs` loads and lists all `/v1/` endpoints.
+ *Frontend* - the Shiny app loads and the *Browse Matrices* tab lists
  COMPADRE data.
+ *End-to-end flow* - register a user, log in, run a simulation from the
  *Simulate* tab, and confirm the result is saved.

== Operations and Monitoring Manual
