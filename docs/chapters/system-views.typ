= System Views <system-views>

The following views describe the system using the arc42 documentation framework.
Diagrams are authored in PlantUML (`docs/diagrams/`) and rendered to SVG by
running `bash docs/diagrams/render.sh` (requires PlantUML on PATH).

== Context View

The context view shows the system as a black box and identifies the external
actors that interact with it.

#figure(
  image("../diagrams/context.svg"),
  caption: [Context view — the system and its external actors],
)

The system has two external actors.

- *User* — a scientist or student interacting with the application through a
  web browser. Users can browse matrices without authentication and run or save
  simulations after registering an account.
- *COMPADRE* — an external scientific database of plant population projection
  matrices. Data from COMPADRE is not fetched at runtime; it is loaded once at
  startup by the seed script and stored locally in the PostgreSQL database.

== Building Block View

The building block view decomposes the system into its three tiers and the
internal layers of the API.

#figure(
  image("../diagrams/building-blocks.svg"),
  caption: [Building block view — tiers and internal API layers],
)

The building block view highlights the strict layer ordering: no layer may
communicate with a non-adjacent layer. The frontend is the only component
that contacts the API from outside, and the repositories are the only
components that touch the database.

== Runtime Views

Each runtime view describes the message flow for one specific use case.
Solid arrows represent synchronous calls; dashed arrows represent responses.

=== User Registration

#figure(
  image("../diagrams/register.svg"),
  caption: [Runtime view — user registration],
)

Registration checks username and email uniqueness before hashing the password
with bcrypt and persisting the new account. No JWT is issued at registration;
the user must log in separately.

=== Login

#figure(
  image("../diagrams/login.svg"),
  caption: [Runtime view — login and JWT issuance],
)

The login endpoint follows the OAuth2 password flow. Credentials are verified
by bcrypt comparison against the stored hash. On success a signed JWT with a
seven-day expiry is returned and stored client-side by the frontend.

=== Search and Browse Matrices

#figure(
  image("../diagrams/search-matrix.svg"),
  caption: [Runtime view — matrix search and detail retrieval],
)

The list endpoint is public — no authentication is required. Filters are
applied at the database level using `ILIKE` for text fields. List responses
return `MatrixSummaryRecord` projections (no matrix data) to keep payloads
small; the full matrix is fetched only when the user selects a specific entry.

=== Create a Custom Matrix

#figure(
  image("../diagrams/create-matrix.svg"),
  caption: [Runtime view — creating a custom matrix],
)

Matrix creation requires authentication. The controller enforces Pydantic
shape validation (square matrix, matching sub-matrix dimensions, stage name
count) before the service sets `source_type = "custom"` and the requesting
user as owner.

=== Save Simulation

#figure(
  image("../diagrams/save-simulation.svg"),
  caption: [Runtime view — running and storing a simulation],
)

The simulation is computed server-side via a NumPy matrix-vector projection
loop and persisted in full. The stored `result_history` contains every
population vector from step 0 to step _n_, making future retrieval
self-contained with no need to re-run the algorithm.

=== Open a Saved Simulation

#figure(
  image("../diagrams/open-simulation.svg"),
  caption: [Runtime view — listing and opening a saved simulation],
)

The list endpoint returns lightweight summary records (no `result_history`)
for efficiency. The full record, including the complete trajectory, is fetched
only when the user selects a specific simulation. An ownership check prevents
users from accessing each other's simulations.

=== Export Simulation

#figure(
  image("../diagrams/export-simulation.svg"),
  caption: [Runtime view — exporting a simulation to a JSON file],
)

The export endpoint builds a self-contained JSON payload from the stored
simulation record. The frontend triggers a file download from the response.
The exported file includes all information required to re-import the
simulation — including the full `result_history` — so no recomputation is
needed on import.

=== Import Simulation

#figure(
  image("../diagrams/import-simulation.svg"),
  caption: [Runtime view — importing a simulation from a JSON file],
)

Import stores the exported payload as a new simulation record without
re-running the algorithm. The `result_history` in the file is used as-is.
This allows sharing simulation results across accounts or restoring a
previously exported run.
