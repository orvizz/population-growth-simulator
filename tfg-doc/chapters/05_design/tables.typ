// chapters/05_design/tables.typ
// All tables for Chapter 5. Included from index.typ.

#let containers-table = [
  #figure(
    table(
      columns: (auto, 1fr, auto),
      inset: 8pt,
      align: left,
      table.header([*Service*], [*Image*], [*Exposed port (host)*]),
      [`db`],       [`postgres:16-alpine`],          [`5435 → 5432 (container)`],
      [`api`],      [built from `Dockerfile`],        [`8000`],
      [`frontend`], [built from `frontend/Dockerfile`], [`8080`],
    ),
    caption: [Docker Compose services and exposed ports.],
  ) <tab:containers>
]

#let cicd-workflows-table = [
  #figure(
    table(
      columns: (auto, auto, 1fr),
      inset: 8pt,
      align: left,
      table.header([*File*], [*Trigger*], [*Purpose*]),
      [`ci.yml`],       [Push / PR to `main`],                    [Correctness — tests and coverage],
      [`security.yml`], [Push / PR to `main`; weekly (Monday)],   [Security — SAST, dependency audit, container scan],
    ),
    caption: [GitHub Actions workflow files.],
  ) <tab:cicd-workflows>
]

#let ci-env-table = [
  #figure(
    table(
      columns: (auto, 1fr),
      inset: 8pt,
      align: left,
      table.header([*Variable*], [*Value in CI*]),
      [`POSTGRES_USER`],     [`postgres`],
      [`POSTGRES_PASSWORD`], [`postgres`],
      [`POSTGRES_DB`],       [`matrix_db`],
      [`POSTGRES_HOST`],     [`localhost`],
      [`POSTGRES_PORT`],     [`5432`],
      [`JWT_SECRET_KEY`],    [`ci-test-secret-key-not-used-in-production`],
    ),
    caption: [Environment variables configured for the CI job.],
  ) <tab:ci-env>
]

#let error-codes-table = [
  #figure(
    table(
      columns: (auto, 1fr),
      inset: 8pt,
      align: left,
      table.header([*Code*], [*Condition*]),
      [`400`], [Business rule violation — e.g. vector dimension mismatch, missing `matrix_a`],
      [`401`], [Missing, malformed, or expired JWT token],
      [`403`], [Authenticated but not authorised — wrong owner, COMPADRE immutability],
      [`404`], [Requested resource does not exist],
      [`409`], [Uniqueness conflict — username or email already registered],
      [`422`], [Pydantic schema validation failure — structured field-level detail],
    ),
    caption: [HTTP status codes used consistently across the API.],
  ) <tab:error-codes>
]

#let env-vars-table = [
  #figure(
    table(
      columns: (auto, 1fr),
      inset: 8pt,
      align: left,
      table.header([*Variable*], [*Purpose*]),
      [`POSTGRES_USER`],     [Database username],
      [`POSTGRES_PASSWORD`], [Database password],
      [`POSTGRES_DB`],       [Database name],
      [`POSTGRES_HOST`],     [Database host (`localhost` outside Docker, `db` inside)],
      [`POSTGRES_PORT`],     [Host-side port (5435); overridden to 5432 inside containers],
      [`JWT_SECRET_KEY`],    [HMAC secret for JWT signing — must be kept confidential],
    ),
    caption: [Runtime environment variables loaded from `.env`.],
  ) <tab:env-vars>
]
