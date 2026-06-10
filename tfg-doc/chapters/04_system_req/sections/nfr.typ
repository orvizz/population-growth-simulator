// chapters/04_system_req/sections/nfr.typ
#import "../../../template.typ": req, req-group

=== Security

The system implements a custom JWT-based authentication mechanism rather than
delegating to a third-party identity provider (e.g., Google or Microsoft).
This was a deliberate academic trade-off: third-party OAuth reduces the attack
surface in production deployments, but custom JWT authentication was chosen to
demonstrate the authentication mechanics as part of the learning objectives of
this project. The implementation follows established security practices to
mitigate the associated risks.

#req-group("NFR-SEC")

#req("Bcrypt Password Hashing", [
  Passwords shall be stored as bcrypt hashes with auto-generated salts; plain-text
  passwords shall never be persisted.
  _Verification: code review (`api/services/auth_service.py`); Bandit SAST scan._
])

#req("JWT Token Expiry", [
  JWT tokens shall use the HS256 algorithm and expire after 7 days.
  _Verification: code review (`api/deps.py`); integration test._
])

#req("Externalised Secrets", [
  The JWT signing secret and database credentials shall be supplied via environment
  variables (`.env` file); no secrets shall be hardcoded in source code.
  _Verification: code review; Bandit SAST scan (no hardcoded secrets)._
])

#req("Input Validation", [
  All API inputs shall be validated by Pydantic schemas before processing; invalid
  input shall return HTTP 422 with a descriptive error body.
  _Verification: `api/schemas.py`; integration tests._
])

#req("COMPADRE Immutability", [
  Matrices with `source_type = "compadre"` shall be permanently read-only; no
  authenticated user may edit or delete them.
  _Verification: service-layer enforcement in `api/services/matrix_service.py`;
  integration tests._
])

#req("Resource Ownership", [
  Custom matrices and simulation runs shall be accessible only to the user who
  created them.
  _Verification: ownership checks in `matrix_service.py` and
  `simulation_service.py`; integration tests._
])

#req("SAST Scan", [
  The codebase shall pass a Bandit SAST scan (medium+ severity threshold) on every
  push to `main`.
  _Verification: GitHub Actions `security.yml`._
])

#req("Dependency CVE Scan", [
  All Python dependencies shall pass a pip-audit CVE scan on every push to `main`.
  _Verification: GitHub Actions `security.yml`._
])

=== Performance

The application targets interactive response times for a single-user to
small-group academic deployment. Computationally intensive operations
(quasi-extinction Monte Carlo analysis) are offloaded to asynchronous background
jobs to keep the API responsive.

#req-group("NFR-PER")

#req("List Endpoint Latency", [
  List and filter endpoints (`GET /v1/matrices`, `GET /v1/simulations`) shall return
  within 500 ms under normal load.
  _Verification: manual testing; integration tests._
])

#req("Deterministic Simulation Latency", [
  A deterministic simulation with n_steps ≤ 1000 and matrix dimension ≤ 10 shall
  complete within 200 ms.
  _Verification: integration tests._
])

#req("Stochastic Simulation Latency", [
  A stochastic simulation with n_steps ≤ 1000 and 2–5 matrices shall complete
  within 500 ms.
  _Verification: integration tests._
])

#req("COMPADRE Catalogue Filtering", [
  The COMPADRE catalogue (~6 000 matrices) shall support filtering by species,
  kingdom, country, and source type with acceptable latency.
  _Verification: database indexes on filtered columns; integration tests._
])

#req("Simulation Step Cap", [
  `n_steps` shall be capped at 1 000 to bound worst-case memory and CPU usage
  per request.
  _Verification: Pydantic validator in `api/schemas.py`._
])

=== Availability and Reliability

The system targets continuous availability throughout the evaluation period.
Reliability is enforced through automatic service restart, database persistence
across container restarts, idempotent migrations, and simulation result snapshots
that are immune to future data changes.

#req-group("NFR-AVL")

#req("Uptime Target", [
  The system shall provide ≥ 99.5% uptime during the evaluation period.
  _Verification: Docker restart policy; health check monitoring._
])

#req("Health Endpoint", [
  `GET /health` shall return HTTP 200 when all services are operational.
  _Verification: integration test; Docker health check._
])

#req("Data Persistence", [
  Database state shall persist across container restarts via a named Docker volume.
  _Verification: Docker Compose volume configuration; manual test._
])

#req("Idempotent Migrations", [
  Database schema migrations shall run automatically and idempotently on container
  startup via Alembic `upgrade head`.
  _Verification: `entrypoint.sh`; CI pipeline._
])

#req("Simulation Snapshots", [
  Stored simulation results shall include a snapshot of matrix values at run time,
  unaffected by subsequent matrix edits or deletions.
  _Verification: `matrices_snapshot` JSONB column in `SimulationRun`; unit tests._
])

=== Usability

The application targets biology researchers, students, and educators with no
assumption of technical expertise beyond basic web browsing. No client-side
installation is required beyond a modern web browser.

#req-group("NFR-USA")

#req("Browser-Based Access", [
  The application shall be accessible via a modern web browser with no client-side
  installation required.
  _Verification: end-to-end tests (Playwright); user manual._
])

#req("Cross-Browser Compatibility", [
  The interface shall function correctly on Chrome ≥ 120, Firefox ≥ 121, and
  Edge ≥ 120.
  _Verification: manual cross-browser testing._
])

#req("First-Use Task Completion", [
  A first-time user shall be able to run a simulation within 5 minutes following
  the user manual.
  _Verification: usability evaluation._
])

#req("Password Field Copy-Paste", [
  Password fields shall not disable copy-paste, to allow the use of password
  managers.
  _Verification: manual test._
])

=== Maintainability and Testability

The backend enforces a strict three-tier architecture to keep HTTP handling,
business logic, and data access independently testable. Services are the sole
locus of business rules and can be exercised with mocked repositories without a
live database.

#req-group("NFR-MNT")

#req("Three-Tier Architecture", [
  The backend shall follow a strict controller → service → repository layering;
  no layer may bypass another.
  _Verification: code review; architecture documentation (Chapter 5)._
])

#req("Isolated Unit Tests", [
  Services shall be unit-testable in isolation using mocked repositories, without
  requiring a live database.
  _Verification: `tests/unit/` test suite; CI pipeline._
])

#req("Test Coverage", [
  API layer test coverage shall reach ≥ 80%.
  _Verification: Codecov report; CI badge._
])

#req("Versioned Migrations", [
  Every database schema change shall be implemented as a versioned Alembic
  migration in `alembic/versions/`.
  _Verification: code review._
])

=== Deployability and DevOps

The entire stack is containerised and deployable with a single command. All
configuration is externalised via environment variables. Automated pipelines
enforce correctness and security on every push to the main branch.

#req-group("NFR-DEV")

#req("Single-Command Deployment", [
  The full system (API, frontend, database) shall deploy with a single
  `docker compose up` command.
  _Verification: user manual; manual test._
])

#req("Environment-Based Configuration", [
  All configurable parameters (database credentials, JWT secret, ports) shall be
  supplied via a `.env` file; no values shall be hardcoded in source.
  _Verification: code review; Bandit SAST scan._
])

#req("Correctness Pipeline", [
  A CI pipeline shall run unit and integration tests automatically on every push
  or pull request to `main`.
  _Verification: GitHub Actions `ci.yml`._
])

#req("Security Pipeline", [
  A security pipeline shall run SAST (Bandit), SCA (pip-audit), and container scan
  (Trivy) on every push to `main` and on a weekly schedule.
  _Verification: GitHub Actions `security.yml`._
])

#req("Automated Dependency Updates", [
  Dependency updates shall be managed automatically via Dependabot for pip,
  GitHub Actions, and Docker base images.
  _Verification: `.github/dependabot.yml`._
])
