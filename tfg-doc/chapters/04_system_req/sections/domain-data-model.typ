// chapters/04_system_req/sections/domain-data-model.typ

=== Domain Data Model

The application's domain is structured around five entities: *User* (registered account),
*PopulationMatrix* (an ecological stage-structured matrix with its species metadata),
*MatrixShare* (an access-control record that grants a second user read access to a private
matrix), *SimulationRun* (the stored result of a deterministic or stochastic population
projection), and *SimulationJob* (a long-running asynchronous analysis such as a
quasi-extinction probability run). @fig:er shows all five domain entities and their primary associations.

#figure(
  image("er.svg", width:90%),
  caption: [Entity-relationship diagram — all domain entities and their primary associations],
) <fig:er>

==== Entity Catalogue

*User*

A registered account with a unique username and email address. Users may own custom
matrices, save simulation runs, and submit background analysis jobs.

#figure(
  {
    set text(size: 8pt)
    table(
      columns: (auto, auto, 1fr),
      stroke: 0.5pt + luma(160),
      align: (left + horizon, left + horizon, left + horizon),
      inset: (x: 6pt, y: 5pt),
      table.header(
        table.cell(fill: rgb("#1F4E79"))[#text(fill: white, weight: "bold")[Attribute]],
        table.cell(fill: rgb("#1F4E79"))[#text(fill: white, weight: "bold")[Type]],
        table.cell(fill: rgb("#1F4E79"))[#text(fill: white, weight: "bold")[Description]],
      ),
      [`id`],          [Integer],  [Surrogate primary key.],
      [`username`],    [String],   [Unique display name (3–64 characters, no whitespace). Used for login and sharing.],
      [`email`],       [String],   [Unique email address. Used for account creation; not exposed in public API responses.],
      [`created_at`],  [DateTime], [UTC timestamp of account creation.],
    )
  },
  caption: [User entity attributes],
) <tab:entity-user>

*PopulationMatrix*

The central domain object. Represents a stage-structured projection matrix (Leslie or
Lefkovitch type) for a specific organism, together with its taxonomic and ecological
metadata. Matrices seeded from the COMPADRE/COMADRE databases are read-only; matrices
created by users are fully editable and support access-control through a three-tier
visibility model.

#figure(
  {
    set text(size: 8pt)
    table(
      columns: (auto, auto, 1fr),
      stroke: 0.5pt + luma(160),
      align: (left + horizon, left + horizon, left + horizon),
      inset: (x: 6pt, y: 5pt),
      table.header(
        table.cell(fill: rgb("#1F4E79"))[#text(fill: white, weight: "bold")[Attribute]],
        table.cell(fill: rgb("#1F4E79"))[#text(fill: white, weight: "bold")[Type]],
        table.cell(fill: rgb("#1F4E79"))[#text(fill: white, weight: "bold")[Description]],
      ),
      [`id`],               [Integer],       [Surrogate primary key.],
      [`source_type`],      [Enum],          [`"compadre"` — seeded from COMPADRE/COMADRE, read-only. `"custom"` — user-created, editable.],
      [`owner`],            [→ User],        [The User who created this matrix. Null for COMPADRE-seeded matrices.],
      [`species_accepted`], [String],        [Accepted binomial or common species name.],
      [`common_name`],      [String],        [Vernacular species name (optional).],
      [`kingdom`],          [String],        [Taxonomic kingdom (e.g., Plantae, Animalia).],
      [`country_code`],     [String],        [ISO 3166-1 alpha-2 country code of the study site.],
      [`matrix_a`],         [Matrix],        [Main projection matrix $bold(A)$ (square 2-D array of Floats). Required.],
      [`matrix_u`],         [Matrix],        [Survival sub-matrix $bold(U)$ (optional, same dimension as $bold(A)$).],
      [`matrix_f`],         [Matrix],        [Fecundity sub-matrix $bold(F)$ (optional, same dimension as $bold(A)$).],
      [`stage_names`],      [List[String]],  [Labels for each life-history stage (length = matrix dimension).],
      [`visibility`],       [Enum],          [`"private"` — owner only. `"shared"` — owner + explicitly granted users. `"public"` — all users including unauthenticated.],
      [`created_at`],       [DateTime],      [UTC timestamp of record creation.],
    )
  },
  caption: [PopulationMatrix entity attributes],
) <tab:entity-matrix>

*MatrixShare*

A junction entity recording that a specific User has been granted read access to a
specific custom matrix whose visibility is `"shared"`. The pair (matrix, grantee) is
unique; duplicate grants are rejected.

#figure(
  {
    set text(size: 8pt)
    table(
      columns: (auto, auto, 1fr),
      stroke: 0.5pt + luma(160),
      align: (left + horizon, left + horizon, left + horizon),
      inset: (x: 6pt, y: 5pt),
      table.header(
        table.cell(fill: rgb("#1F4E79"))[#text(fill: white, weight: "bold")[Attribute]],
        table.cell(fill: rgb("#1F4E79"))[#text(fill: white, weight: "bold")[Type]],
        table.cell(fill: rgb("#1F4E79"))[#text(fill: white, weight: "bold")[Description]],
      ),
      [`id`],                 [Integer],  [Surrogate primary key.],
      [`matrix`],             [→ PopulationMatrix], [The matrix being shared. Cascade-deleted when the matrix is removed.],
      [`shared_with_user`],   [→ User],   [The user receiving access. Cascade-deleted when the user account is removed.],
      [`created_at`],         [DateTime], [UTC timestamp when the share was granted.],
    )
  },
  caption: [MatrixShare entity attributes (unique constraint on matrix + shared\_with\_user)],
) <tab:entity-share>

*SimulationRun*

A persisted population-projection run. Stores the full trajectory (population vector at
every time step), a snapshot of the input matrices, and the computed ecological analytics.
Snapshotting the matrix data at run time makes stored simulations immune to subsequent
edits or deletions of the source matrices.

#figure(
  {
    set text(size: 8pt)
    table(
      columns: (auto, auto, 1fr),
      stroke: 0.5pt + luma(160),
      align: (left + horizon, left + horizon, left + horizon),
      inset: (x: 6pt, y: 5pt),
      table.header(
        table.cell(fill: rgb("#1F4E79"))[#text(fill: white, weight: "bold")[Attribute]],
        table.cell(fill: rgb("#1F4E79"))[#text(fill: white, weight: "bold")[Type]],
        table.cell(fill: rgb("#1F4E79"))[#text(fill: white, weight: "bold")[Description]],
      ),
      [`id`],                [Integer],        [Surrogate primary key.],
      [`user`],              [→ User],          [Owner of this run. Nullable (unauthenticated ephemeral runs are not stored).],
      [`name`],              [String],          [Optional user-facing label for the run.],
      [`stochastic`],           [Boolean],              [`false` — deterministic (single matrix). `true` — stochastic (multiple matrices; each run commits to one randomly-chosen matrix for all steps).],
      [`matrix_id`],            [→ PopulationMatrix],   [Source matrix for deterministic runs. Null for stochastic runs.],
      [`matrix_ids`],           [List[Integer]],        [Source matrix IDs for stochastic runs (≥2). Null for deterministic runs.],
      [`initial_vector`],       [List[Float]],          [Starting population vector $bold(v)(0)$ (one value per life-history stage).],
      [`n_steps`],              [Integer],              [Number of projection time steps (1–1 000).],
      [`random_seed`],          [Integer],              [PRNG seed for stochastic runs; enables exact reproduction.],
      [`result_history`],       [List[List[Float]]],    [Population vector $bold(v)(t)$ at each time step $t = 0 dots n$. For stochastic runs this is the mean population vector across all $N$ runs at each step.],
      [`matrices_snapshot`],    [List[Matrix]],         [Copy of `matrix_a` arrays captured at run time; immutable thereafter.],
      [`matrix_sequence`],      [List[Integer]],        [Index into `matrix_ids` committed to for each run; one entry per run (length = `n_runs`, stochastic only).],
      [`n_runs`],               [Integer],              [Number of independent runs executed (10–1 000, default 100). Null for deterministic runs.],
      [`result_variance`],      [List[List[Float]]],    [Variance of the population vector per stage at each time step, computed across all $N$ runs. Null for deterministic runs.],
      [`result_min_history`],   [List[List[Float]]],    [Per-stage minimum population value at each step across all runs. Null for deterministic runs.],
      [`result_max_history`],   [List[List[Float]]],    [Per-stage maximum population value at each step across all runs. Null for deterministic runs.],
      [`analytics`],            [Dictionary],           [Computed ecological metrics: $lambda_1$, stable-stage distribution, reproductive value, sensitivities and elasticities (deterministic); or $lambda_s$, mean-matrix elasticities (stochastic).],
      [`created_at`],           [DateTime],             [UTC timestamp of run creation.],
    )
  },
  caption: [SimulationRun entity attributes],
) <tab:entity-simrun>

*SimulationJob*

A persistent record for a long-running background analysis (currently: quasi-extinction
probability estimation via Monte Carlo). The job progresses through a defined status
lifecycle. Both the input parameters and the matrix data are captured at submission time
so that the background task is independent of any subsequent changes to the source matrices.

#figure(
  {
    set text(size: 8pt)
    table(
      columns: (auto, auto, 1fr),
      stroke: 0.5pt + luma(160),
      align: (left + horizon, left + horizon, left + horizon),
      inset: (x: 6pt, y: 5pt),
      table.header(
        table.cell(fill: rgb("#1F4E79"))[#text(fill: white, weight: "bold")[Attribute]],
        table.cell(fill: rgb("#1F4E79"))[#text(fill: white, weight: "bold")[Type]],
        table.cell(fill: rgb("#1F4E79"))[#text(fill: white, weight: "bold")[Description]],
      ),
      [`id`],                [Integer],     [Surrogate primary key.],
      [`user`],              [→ User],       [Submitting user. Set to null if the account is later deleted.],
      [`job_type`],          [String],       [Identifies the analysis algorithm, e.g., `"quasi_extinction"`.],
      [`status`],            [Enum],         [`"pending"` → `"running"` → `"completed"` or `"failed"`. Set by the background worker.],
      [`params`],            [Dictionary],   [Full input snapshot captured at submission: matrix IDs, initial vector, threshold, time horizon, stage configuration.],
      [`matrices_snapshot`], [List[Matrix]], [Copy of `matrix_a` arrays at submission time; the job uses these even if source matrices change.],
      [`result`],            [Dictionary],   [Computed output on successful completion (e.g., cumulative quasi-extinction probability curve).],
      [`error`],             [Text],         [Human-readable error message on failure.],
      [`created_at`],        [DateTime],     [UTC timestamp when the job was submitted.],
      [`updated_at`],        [DateTime],     [UTC timestamp of the most recent status change; useful for polling.],
    )
  },
  caption: [SimulationJob entity attributes],
) <tab:entity-job>

==== Key Domain Rules

*Matrix origin and mutability.* A matrix with `source_type = "compadre"` originates from
the COMPADRE or COMADRE databases and is seeded automatically on application start-up. These
matrices are read-only system data: no authenticated user may edit or delete them. Matrices
with `source_type = "custom"` are created by registered users through the API and may be
freely edited, shared, or deleted by their owner.

*Simulation snapshotting.* When a simulation run or background job is created, the system
copies the `matrix_a` arrays of all input matrices into a `matrices_snapshot` field on the
new record. From that point forward, stored simulations and jobs are self-contained: editing
or deleting the source matrices has no effect on previously computed results, preserving
reproducibility of the scientific record.

*Deterministic vs. stochastic mode.* A `SimulationRun` is deterministic when a single
`matrix_id` is provided: the same projection matrix $bold(A)$ is used at every step via
$bold(v)(t+1) = bold(A) dot bold(v)(t)$. It is stochastic when two or more matrices are
provided via `matrix_ids`: at each step a matrix is chosen uniformly at random (seeded by
`random_seed`) and the `matrix_sequence` field records which index was selected, making the
run exactly reproducible from the stored seed alone.

*Async job lifecycle.* A `SimulationJob` is created synchronously with status `"pending"`;
the HTTP response is returned immediately (HTTP 202 Accepted). A background worker then
claims the job, sets status to `"running"`, and on completion writes either the `result`
payload (status `"completed"`) or an `error` message (status `"failed"`). The `updated_at`
timestamp changes on each transition and is the intended polling signal for the client.

#pagebreak(weak: true)