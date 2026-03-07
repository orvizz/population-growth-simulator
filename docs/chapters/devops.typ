= DevOps and CI/CD <devops>

== Overview

Two GitHub Actions workflow files drive the automated pipeline.

#table(
  columns: (auto, auto, 1fr),
  inset: 8pt,
  align: left,
  table.header([*File*], [*Trigger*], [*Purpose*]),
  [`ci.yml`],       [Push / PR to `main`], [Correctness — tests and coverage],
  [`security.yml`], [Push / PR to `main`, weekly schedule], [Security — SAST, dependency audit, container scan],
)

Separating correctness from security into distinct workflow files achieves two
goals. First, it prevents a security job failure from blocking a merge when
the fix requires a dependency update that is out of the developer's immediate
control. Second, the security workflow runs on a weekly schedule independently
of code changes, surfacing newly disclosed CVEs in dependencies or base images
that no code commit could have detected.

== CI Workflow (`ci.yml`)

The CI workflow runs on every push and pull request targeting `main`. It
provisions a PostgreSQL 16 service container so that integration tests can run
in the same job without any external infrastructure.

=== Steps

+ *Checkout* — `actions/checkout@v4`.
+ *Set up Python 3.13* — `actions/setup-python@v5` with pip caching.
+ *Install dependencies* — `pip install -r requirements.txt pytest pytest-cov`.
+ *Run database migrations* — `python -m alembic upgrade head`, applying all
  pending migrations to the CI PostgreSQL instance.
+ *Run unit tests* — `pytest tests/unit/ -v --tb=short`. These complete in
  seconds and provide fast feedback before slower integration tests run.
+ *Run integration tests* — `pytest tests/ --ignore=tests/unit/ -v --tb=short`.
+ *Generate coverage report* — a combined run with `--cov=api --cov=db`
  produces both a terminal summary and an XML report.
+ *Upload to Codecov* — the XML report is sent to Codecov for trend tracking
  and badge generation. `fail_ci_if_error: false` prevents a Codecov outage
  from blocking the pipeline.

=== Environment Variables

The CI job sets the following environment variables to configure the
application against the provisioned PostgreSQL container.

```yaml
POSTGRES_USER: postgres
POSTGRES_PASSWORD: postgres
POSTGRES_DB: matrix_db
POSTGRES_HOST: localhost
POSTGRES_PORT: 5432
JWT_SECRET_KEY: ci-test-secret-key-not-used-in-production
```

== Security Workflow (`security.yml`)

The security workflow runs on push, pull request, and every Monday at 08:00
UTC. It is composed of three independent jobs.

=== Bandit SAST

Bandit @bandit performs static analysis of the Python source in `api/` and
`db/` looking for common security anti-patterns (e.g. hardcoded passwords,
use of insecure hash functions, SQL injection risks).

The job runs in two passes.

*Audit pass* — scans at medium severity/confidence and writes the findings to a
JSON artifact (`bandit-report.json`) uploaded as a workflow artifact. This run
uses `|| true` to avoid failing the job, ensuring the artifact is always
produced.

*Gate pass* — re-scans at high severity/confidence without `|| true`. If Bandit
finds any high-severity, high-confidence issue, the job fails and the merge is
blocked.

=== pip-audit

pip-audit @pipaudit checks `requirements.txt` against the PyPA Advisory
Database for known CVEs in any direct or transitive dependency. The report is
written as JSON and uploaded as a workflow artifact. The job fails if any
vulnerability is found, prompting an immediate dependency update.

=== Trivy Container Scan

Trivy @trivy scans the built Docker image for OS-level and library-level
vulnerabilities at `CRITICAL` and `HIGH` severity. The image is built from
the project `Dockerfile` before scanning, so the scan reflects the exact image
that would be deployed.

The job is configured with `exit-code: "0"` so that findings are reported to
the job log without failing the pipeline. This is a deliberate choice: OS
vulnerabilities in the base image may not have fixes available immediately, and
blocking every push on an unpatched upstream CVE would be counterproductive.
The weekly schedule ensures that the report is reviewed regularly.

== Docker Setup

The project ships three Docker-related files.

`Dockerfile` — builds the API image. It installs Python dependencies from
`requirements.txt` and copies the application source. The `entrypoint.sh`
script is set as the container entrypoint.

`frontend/Dockerfile` — builds the Shiny frontend image.

`docker-compose.yml` — defines the full three-container stack and wires
services together. Notable details.

- The `db` service uses a named volume to persist data across container
  restarts.
- The `api` and `frontend` services declare `depends_on` with a health check
  condition, so they only start after PostgreSQL is ready to accept connections.
- The `POSTGRES_PORT` environment variable is overridden to `5432` inside the
  containers (the value in `.env` is `5435`, the host-side port), preventing a
  misconfiguration that would cause the application to connect to the wrong port
  when running inside Docker.

=== `entrypoint.sh`

The API container entrypoint performs three steps before starting the server.

+ Apply pending Alembic migrations: `python -m alembic upgrade head`.
+ Seed COMPADRE data: `python db/seed_compadre.py`.
+ Start Uvicorn: `python -m uvicorn api.main:app --host 0.0.0.0 --port 8000`.

Steps 1 and 2 are idempotent. Restarting the container does not duplicate data
or re-apply already-applied migrations.

*Important:* `entrypoint.sh` must have Unix line endings (LF). Editing this
file on Windows with a tool that writes CRLF line endings will cause the script
to fail with a cryptic interpreter error. The convention is to run
`sed -i 's/\r//' entrypoint.sh` after any Windows-side edit.

== Local Development

The full stack can be started locally with:

```bash
make up        # build images, apply migrations, seed COMPADRE, start services
make logs      # follow all logs
make down      # stop containers (data preserved)
make clean     # stop containers and delete all volumes
```

On Windows where `make` is not available the underlying Docker Compose commands
can be used directly:

```bash
docker compose up -d --build
docker compose logs -f api
docker compose down
```

Services after startup:

#table(
  columns: (auto, auto),
  inset: 8pt,
  align: left,
  table.header([*Service*], [*URL*]),
  [Frontend],    [`http://localhost:8080`],
  [API],         [`http://localhost:8000`],
  [Swagger UI],  [`http://localhost:8000/docs`],
)
