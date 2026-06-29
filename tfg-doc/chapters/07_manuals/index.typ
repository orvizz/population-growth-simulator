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

== User Manual <sec:user-manual>

The Population Growth Simulator is a web application for exploring structured population
models. It requires no installation: open a browser and navigate to the application URL at
#link("https://popgrowthsim.marioorviz.dev"). \
The interface is organised into four tabs, *Browse Matrices*, *Simulate*,
*Quasi-Extinction*, and *My Matrices*, visible in the header on every page. Most features
are freely accessible without an account. Creating an account unlocks saving and managing
your own work.

=== Getting Started

Open the application in a browser. The *Browse Matrices* tab loads automatically, showing
the full catalogue of population matrices from the COMPADRE and COMADRE databases
(@fig:manual-browse). No login is required to explore the catalogue or run an ephemeral
simulation.

#figure(
  image("../04_system_req/sections/ui/MB-matrix_browse_not_logged.png", width: 100%),
  caption: [Application landing page: Browse Matrices tab with the full matrix catalogue and filter controls.],
) <fig:manual-browse>

=== Creating an Account and Logging In

An account is required to save simulations, manage custom matrices, and run quasi-extinction
analyses. To register, click *Sign Up* in the header, fill in a username, email address, and
a password of at least eight characters containing at least one letter and one number, then
submit the form.

#grid(
  columns: (1fr, 1fr),
  gutter: 1em,
  [
    #figure(
      image("../04_system_req/sections/ui/SGUP-sign_up.png"),
      caption: [Sign-Up form. Enter username, email, and password to create an account.],
    ) <fig:manual-signup>
  ],
  [
    #figure(
      image("../04_system_req/sections/ui/SGUP-sign_up_successful.png"),
      caption: [Confirmation message shown after successful registration.],
    ) <fig:manual-signup-ok>
  ],
)

Once registered, click *Log In*, enter your username and password, and submit. The header
updates to show your username and a *Sign Out* link (@fig:manual-login-ok). To end the
session, click *Sign Out* and the application returns to the unauthenticated state without
losing your browsing context.

#figure(
  image("../04_system_req/sections/ui/LGIN-log_in_successful.png", width: 100%),
  caption: [Header after a successful login: auth buttons are replaced by the signed-in username and a Sign Out link.],
) <fig:manual-login-ok>

=== Browsing the Population Matrix Catalogue

The *Browse Matrices* tab is accessible to everyone. It lists all matrices from COMPADRE
(plants) and COMADRE (animals), plus any public custom matrices created by registered users (over 15 000 entries visible in the default unfiltered view).

To narrow the list, use the filter bar:

- Type a species name in the search field; results update as you type.
- Use the *Kingdom* dropdown to restrict to plants or animals.
- Use the *Source* dropdown to restrict to a specific database.

Active filters combine as AND conditions. Click any row to open the *Matrix detail panel*
for that species (@fig:manual-detail). The panel shows the projection matrix A, the
survival matrix U, and the fecundity matrix F as labelled grids, together with an
interactive life-cycle network diagram. Click the info button to view publication metadata
such as author, study duration, and geographic origin. Use the *Export JSON* or
*Export CSV* buttons to download the matrix data.

#figure(
  image("../04_system_req/sections/ui/MB-matrix_detail.png", width: 100%),
  caption: [Matrix detail panel. Projection matrices, life-cycle network diagram, and export controls.],
) <fig:manual-detail>

=== Managing Your Custom Matrices

The *My Matrices* tab lets registered users build and maintain a personal library of
population matrices. Open the tab and log in if prompted.

*Creating a matrix:* click *New matrix*, choose the number of stages, assign names to each
stage, then fill in the numerical values for the A, U, and F sub-matrices. Save when
finished.

*Editing and deleting:* use the action buttons next to any matrix in the list to open the
edit form or delete the matrix (deletion requires confirmation to prevent accidental loss).

*Visibility:* set each matrix to *private* (visible only to you), *shared* (accessible to
specific users you invite by username), or *public* (visible to all users in the Browse
catalogue).

*Importing:* click *Import* to upload a JSON file or a ZIP archive containing multiple JSON
files; all matrices are added to your library immediately.

#grid(
  columns: (1fr, 1fr),
  gutter: 1em,
  [
    #figure(
      image("../04_system_req/sections/ui/MYM-my_matrices_logged.png"),
      caption: [My Matrices tab. Authenticated view with the matrix list and management controls.],
    ) <fig:manual-mym>
  ],
  [
    #figure(
      image("../04_system_req/sections/ui/MYM-my-matrices-stage-configuration.png"),
      caption: [Stage-name configuration step during matrix creation or editing.],
    ) <fig:manual-mym-stages>
  ],
)

=== Running Population Simulations

The *Simulate* tab computes population trajectories from a selected matrix or set of
matrices. Unauthenticated users can run ephemeral simulations; saving results requires
login.

==== Setting Up a Simulation

The left sidebar guides you through four steps:

+ *Matrix*: Type a species name in the search field and click the species you want to use.
+ *Mode*: Choose *Deterministic* (a single fixed matrix applied at every time step) or
  *Stochastic* (the model randomly selects one matrix per step from a set you provide,
  capturing environmental variability across years or seasons).
+ *In Simulation*: Review the selected matrix; for stochastic runs, add further matrices
  using the *Add* button.
+ *Parameters*: Enter one initial population value per life-history stage, set the number
  of time steps (1–50,000), and optionally a random seed for reproducibility. Give the run a
  name if you intend to save it.

Click *Run* to compute the trajectory (@fig:manual-sim-setup).

#figure(
  image("../04_system_req/sections/ui/SIM-run_simulation_1.png", width: 100%),
  caption: [Simulation setup sidebar: Matrix search, mode selection (stochastic shown), and parameter entry.],
) <fig:manual-sim-setup>

==== Interpreting Results

The results panel displays the *Population dynamics* chart, plotting the abundance of each
life-history stage over time. Switch to the *Analytics* section to see:

- *λ (lambda)*: The asymptotic population growth rate. Values above 1 indicate a growing
  population; values below 1 indicate decline.
- *Stable stage distribution*: The long-term proportion of individuals expected in each
  stage.
- *Elasticities*: How sensitive λ is to proportional changes in each matrix element,
  shown as a colour-coded heatmap. High-elasticity entries flag the demographic rates that
  most strongly influence population fate.
- *Average matrix A*: The mean projection matrix across all matrices (stochastic runs
  only).

Click *View data table* to open a modal with the full numerical trajectory for every stage
at every recorded time step.

#grid(
  columns: (1fr, 1fr),
  gutter: 1em,
  [
    #figure(
      image("../04_system_req/sections/ui/SIM-run_results_1.png"),
      caption: [Results panel: Population dynamics chart and final population breakdown by stage.],
    ) <fig:manual-sim-results>
  ],
  [
    #figure(
      image("../04_system_req/sections/ui/SIM-run_results_2.png"),
      caption: [Analytics panel: Growth rate λ, stable stage distribution, and elasticity matrix.],
    ) <fig:manual-sim-analytics>
  ],
)

==== Saving and Revisiting Runs

To save the current run, enter a name in the *Parameters* step and click *Save as new*
(login required). Saved runs appear in the *Library* view, toggled from the top of the
sidebar. Opening a past run restores its dynamics chart and analytics. To remove a run from
the Library, click the delete button and confirm.

=== Quasi-Extinction Analysis

The *Quasi-Extinction* tab estimates the probability that a stochastic population will fall
below a critical threshold within a given time horizon. The computation runs as a background
job, so you can navigate elsewhere and return once it completes.

==== Configuring a New Analysis

Click *New analysis* in the left sidebar. The configuration form has three parts:

+ *Organism selection*: Search for and add the matrices to use (the same multi-matrix
  interface as stochastic simulation). Using matrices from different years or environmental
  conditions captures temporal variability.
+ *Stage configuration* (optional, @fig:manual-qe-stages): Open the stage modal to set a
  per-stage minimum abundance threshold below which that stage is considered locally
  extinct, or to exclude stages (such as juveniles) that naturally fluctuate near zero.
+ *Simulation parameters*: Set the global extinction threshold (total population count),
  the time horizon, the number of Monte Carlo runs, and an optional random seed.

When all fields are filled, click *Run analysis*. The job starts immediately and a progress
indicator appears in the sidebar; you do not need to wait on the page.

#grid(
  columns: (1fr, 1fr),
  gutter: 1em,
  [
    #figure(
      image("../04_system_req/sections/ui/QE-quasi-extinction-new-analysis.png"),
      caption: [New analysis form. Matrix selection and simulation parameter entry.],
    ) <fig:manual-qe-form>
  ],
  [
    #figure(
      image("../04_system_req/sections/ui/QE-quasi-extinction-new-analysis-configure-stages.png"),
      caption: [Stage-threshold configuration modal. Per-stage thresholds and stage exclusion controls.],
    ) <fig:manual-qe-stages>
  ],
)

==== Reading the Results

When the job finishes the panel populates with several views (@fig:manual-qe-curve,
@fig:manual-qe-extra):

- *Mean population trajectory*: The average population path across all Monte Carlo runs,
  with a clickable stage-name legend.
- *Cumulative quasi-extinction probability*: The proportion of runs in which the
  population crossed the threshold by each point in time. A curve that rises steeply early
  signals high near-term extinction risk.
- *Time to extinction distribution*: How often each time step was the first moment of
  extinction across runs.
- *Which stage triggered extinction*: Which life-history stage most frequently caused the
  population to cross the threshold, helping identify demographic bottlenecks.
- *Stochastic growth rate (λ_s) distribution*: The spread of long-run growth rates across
  Monte Carlo runs.
- *Data table*: The full numerical mean trajectory for every stage at every time step.

#grid(
  columns: (1fr, 1fr),
  gutter: 1em,
  [
    #figure(
      image("../04_system_req/sections/ui/QE-quasi-extinction-logged-3.png"),
      caption: [Cumulative quasi-extinction probability curve over the analysis time horizon.],
    ) <fig:manual-qe-curve>
  ],
  [
    #figure(
      image("../04_system_req/sections/ui/QE-quasi-extinction-logged-4.png"),
      caption: [Supplementary results: extinction timing distribution, causation by life stage, and stochastic growth rate distribution.],
    ) <fig:manual-qe-extra>
  ],
)

Past analyses are listed in the left sidebar. To remove one, click the delete button next
to its entry and confirm.

=== Selecting the Interface Language

The language selector is available in the header on every tab. Click it to open a dropdown
and choose one of the six supported locales: English, Spanish (Español), Asturian
(Asturianu), Galician (Galego), Basque (Euskara), or Catalan (Català). The selected
language takes effect immediately across all labels, buttons, and messages, and is
remembered across sessions.

#figure(
  image("../04_system_req/sections/ui/LANG-language_selector.png", width: 85%),
  caption: [Language selector dropdown. Six locales available from the header on any tab.],
) <fig:manual-lang>

== Installation and Configuration Manual <sec:installation-manual>

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

Target audience: a developer or operator maintaining a running instance, whether the
local Docker Compose stack (@sec:docker-deployment) or a Railway environment
(@sec:railway-deployment). Railway-specific rollback and first-deploy behaviour are
already covered in @sec:railway-operations; this section covers day-to-day operation
of the Docker Compose stack, plus monitoring that applies to both.

=== Logs and Service Status

View logs for a single service, following new output as it arrives:

```bash
docker compose logs -f api
docker compose logs -f frontend
docker compose logs -f db
```

`docker compose ps` lists all three containers with their current status and exposed
ports; `docker compose logs --tail=100` without `-f` prints the last 100 lines across
every service without following, useful for a quick post-mortem.

=== Restarting a Service

```bash
docker compose restart api
```

Restarting `api` or `frontend` re-runs `entrypoint.sh`, which re-checks (idempotently)
that migrations are applied and COMPADRE/COMADRE are seeded before starting the
process - safe to do at any time. Restarting `db` is safe too: data persists in the
`postgres_data` volume regardless of container restarts (only `docker compose down -v`
discards it).

=== Database Backup and Restore

```bash
# Backup
docker compose exec db pg_dump -U $POSTGRES_USER $POSTGRES_DB > backup_$(date +%F).sql

# Restore (into an existing, empty database)
docker compose exec -T db psql -U $POSTGRES_USER $POSTGRES_DB < backup.sql
```

For Railway, the managed PostgreSQL instance exposes its own connection string in the
service's *Variables* tab, which `pg_dump`/`psql` can target directly using the
`-h`/`-p`/`-d` flags instead of `docker compose exec`.

=== Applying New Migrations

`entrypoint.sh` applies all pending Alembic migrations automatically on container
start. To apply a migration to an already-running container without restarting it
(for example while debugging):

```bash
docker compose exec api python -m alembic upgrade head
```

=== Updating Images

```bash
docker compose pull   # no-op for locally built images; relevant if a base image moved
docker compose up -d --build
```

Because `api` and `frontend` are built from the local `Dockerfile`/`Dockerfile.frontend`
rather than pulled from a registry, "updating" in practice means rebuilding after a
`git pull` - `docker compose up -d --build` picks up both source changes and any
updated `requirements.txt` dependencies.

=== Monitoring

- *Test coverage*: the Codecov badge in `README.md` reflects the latest `main` build;
  click through to codecov.io for line-by-line coverage detail.
- *Code quality*: once SonarCloud is activated in CI (see @sec:future-work), its
  dashboard adds code-smell, duplication, and security-hotspot tracking alongside
  coverage.
- *Security scanning*: the `security.yml` and `codeql.yml` workflows (@sec:cicd) run on
  every push/PR and weekly on a schedule; their results appear under the repository's
  *Security* tab on GitHub.
- *Railway*: each service's *Metrics* tab shows CPU/memory/network usage and recent
  deploy history; the *Observability* view aggregates logs across all three services in
  one place.
