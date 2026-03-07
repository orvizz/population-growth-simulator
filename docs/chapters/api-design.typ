= API Design <api-design>

== Design Principles

The REST API follows a resource-oriented design. All endpoints are versioned
under the `/v1/` prefix so that future breaking changes can be introduced
without disrupting existing clients. Resources are nouns (`/matrices`,
`/simulations`), and HTTP verbs carry semantic meaning.

The API distinguishes between two categories of endpoints:

- *Public endpoints* — accessible without authentication. These cover read
  operations on matrices and ephemeral simulation runs, enabling unauthenticated
  users to explore the dataset and try the simulator.
- *Protected endpoints* — require a valid JWT Bearer token. These cover
  resource creation, mutation, and operations that are scoped to a specific
  user (user's simulation library, custom matrix management).

== Endpoint Reference

#table(
  columns: (auto, auto, auto, auto),
  inset: 8pt,
  align: left,
  table.header([*Method*], [*Path*], [*Auth*], [*Description*]),
  [`GET`],    [`/health`],                    [No],  [Liveness check],
  [`POST`],   [`/v1/auth/register`],          [No],  [Create a user account],
  [`POST`],   [`/v1/auth/login`],             [No],  [Obtain a JWT token],
  [`GET`],    [`/v1/matrices`],               [No],  [List / filter matrices],
  [`GET`],    [`/v1/matrices/{id}`],          [No],  [Get full matrix detail],
  [`POST`],   [`/v1/matrices`],               [Yes], [Create a custom matrix],
  [`PATCH`],  [`/v1/matrices/{id}`],          [Yes], [Update own matrix],
  [`POST`],   [`/v1/simulations/run`],        [No],  [Ephemeral simulation run],
  [`POST`],   [`/v1/simulations`],            [Yes], [Run and store simulation],
  [`GET`],    [`/v1/simulations`],            [Yes], [List own simulations],
  [`GET`],    [`/v1/simulations/{id}`],       [Yes], [Get simulation + history],
  [`GET`],    [`/v1/simulations/{id}/export`],[Yes], [Export simulation as JSON],
  [`POST`],   [`/v1/simulations/import`],     [Yes], [Import from exported file],
  [`DELETE`], [`/v1/simulations/{id}`],       [Yes], [Delete own simulation],
)

== Authentication

Authentication is handled with the OAuth2 password flow. The client sends
credentials to `POST /v1/auth/login` as a form-encoded body (compatible with
the OAuth2 spec). The server responds with a JWT access token and a
`token_type` of `"bearer"`. Subsequent protected requests must include the
token in the `Authorization: Bearer <token>` header.

Tokens are signed with `HS256` using the `JWT_SECRET_KEY` environment
variable and expire after seven days. The `get_current_user` FastAPI dependency
validates the token signature and expiry on every protected request, resolving
it to a `UserRecord`.

== Input Validation — Schemas

All data arriving over HTTP is parsed by Pydantic schema classes defined in
`api/schemas.py`. Validation rules cover:

- *Field-level constraints* — minimum/maximum lengths, numeric bounds (`n_steps`
  in `[1, 1000]`), and non-empty lists.
- *Cross-field invariants* — `SimulationCreate` enforces that exactly one of
  `matrix_id` (deterministic) or `matrix_ids` (stochastic) is provided, and
  that `matrix_ids` contains at least two entries when present.
- *Matrix shape validation* — `MatrixCreate` and `MatrixUpdate` verify that
  `matrix_a` is square and that `matrix_u` / `matrix_f`, when provided, share
  the same dimension as `matrix_a`.

Validation errors are returned automatically by FastAPI as `422 Unprocessable
Entity` responses with a structured JSON body describing each failing field.

== Output Serialisation — Records

Service methods return Pydantic record objects (defined in `api/records.py`)
which FastAPI serialises to JSON. Two projection levels exist for each
resource:

- *Summary records* — lightweight projections used in list responses. For
  matrices these omit `matrix_a`, `matrix_u`, and `matrix_f`. For simulations
  these omit `result_history` and `initial_vector`, keeping list responses
  compact.
- *Full records* — complete representations returned by single-resource GET
  endpoints.

== Ephemeral vs. Stored Simulations

The simulation API exposes two distinct modes.

`POST /v1/simulations/run` performs an ephemeral run: the computation is
executed and the full result is returned in the HTTP response, but nothing is
persisted. This endpoint requires no authentication and is intended for quick
exploration without building up a simulation history.

`POST /v1/simulations` performs a stored run: the computation is executed,
the result is written to `simulation_runs`, and the full record is returned.
This endpoint requires authentication. The stored simulation can later be
retrieved, exported, or deleted.

The export/import pair (`GET /{id}/export` + `POST /import`) allows users to
download a simulation as a JSON file and restore it — either to the same
account or to a different one — without re-running the computation.

== Ownership and Immutability Rules

Ownership rules are enforced entirely in the service layer, never in the
controller or repository.

- A user can only retrieve, export, or delete simulations they own.
- A user can only update matrices they created (`source_type = "custom"`).
- COMPADRE matrices (`source_type = "compadre"`) are immutable for all users,
  including authenticated ones. Any `PATCH` request against a COMPADRE matrix
  returns `403 Forbidden` with a descriptive error message.

== Error Responses

The API uses standard HTTP status codes throughout.

#table(
  columns: (auto, 1fr),
  inset: 8pt,
  align: left,
  table.header([*Code*], [*Meaning*]),
  [`400`], [Bad request — business rule violation (e.g. vector dimension mismatch)],
  [`401`], [Missing or invalid JWT token],
  [`403`], [Authenticated but not authorised (wrong owner, COMPADRE immutability)],
  [`404`], [Requested resource does not exist],
  [`422`], [Input validation failure — Pydantic schema rejected the request body],
)
