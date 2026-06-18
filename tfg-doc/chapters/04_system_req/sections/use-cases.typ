// chapters/04_system_req/sections/use-cases.typ
// Use case descriptions - tabular format (one table per UC, auto-numbered UC-01 … UC-21).
// Layout: blue header with UC-id and name, grey label column (32 %), white content column.
#import "../../../template.typ": use-case

// ── Authentication ─────────────────────────────────────────────────────────────

#use-case(
  name:           [Register User],
  description:    [A visitor creates a new account by providing a unique username, email address, and password, gaining access to the features reserved for registered users.],
  actors:         [Visitor (primary).],
  trigger:        [The visitor clicks the "Register" option in the authentication panel.],
  preconditions:  [The visitor is not authenticated. The registration form is accessible.],
  postconditions: [A new user account is created; the user can immediately log in with the new credentials.],
  normal-flow: (
    [Visitor opens the registration form.],
    [Visitor enters a username, email address, and password (minimum 8 characters).],
    [Visitor submits the form.],
    [System validates that the username and email are unique and that the password meets the length requirement.],
    [System creates the user account.],
    [System confirms successful registration and presents the login form.],
  ),
  exceptions: [
    (4') Username or email is already registered → system returns a descriptive error identifying the conflicting field. \
    (4'') Password is shorter than 8 characters → system returns a validation error.
  ],
)

#use-case(
  name:           [Log In],
  description:    [A registered user authenticates with their credentials and receives a session token that unlocks restricted features.],
  actors:         [Visitor (primary).],
  trigger:        [The visitor clicks the "Log In" option in the authentication panel.],
  preconditions:  [The visitor has a registered account.],
  postconditions: [The user is authenticated; a 7-day JWT token is issued; restricted features (simulations, custom matrices, quasi-extinction) become accessible.],
  normal-flow: (
    [Visitor opens the login form.],
    [Visitor enters their username or email address and password.],
    [Visitor submits the form.],
    [System validates credentials against the stored hash.],
    [System issues a JWT token valid for 7 days.],
    [System grants the user access to registered-user features.],
  ),
  exceptions: [
    (4') Credentials are invalid → system returns a generic "Invalid credentials" error (no enumeration of which field is wrong).
  ],
)

#use-case(
  name:           [Log Out],
  description:    [An authenticated user terminates their current session, revoking access to restricted features.],
  actors:         [Registered User (primary).],
  trigger:        [The user clicks "Log Out" in the account panel.],
  preconditions:  [The user is authenticated with a valid JWT token.],
  postconditions: [The session token is cleared client-side; the user is returned to the public view as a visitor.],
  normal-flow: (
    [User clicks "Log Out".],
    [System clears the session token from the client.],
    [System redirects the user to the public Browse Matrices view.],
  ),
)

// ── Browse Matrices ────────────────────────────────────────────────────────────

#use-case(
  name:           [Browse Matrix Catalog],
  description:    [Any visitor can browse the publicly accessible catalog of population matrices, comprising COMPADRE seeded data and user-created public matrices, displayed in a paginated list with key metadata per entry.],
  actors:         [Visitor (primary); COMPADRE (secondary - provides the seeded data).],
  trigger:        [The visitor opens the "Browse Matrices" tab.],
  preconditions:  [The matrix catalog has been seeded. The API is available.],
  postconditions: [A paginated matrix list is displayed; each entry shows species name, common name, kingdom, source type, and matrix dimension.],
  normal-flow: (
    [Visitor navigates to the "Browse Matrices" tab.],
    [System queries the catalog API with default pagination parameters.],
    [System displays the paginated list (species name, common name, kingdom, source, dimension).],
    [Visitor scrolls or pages through the results.],
  ),
  alt-flows: [
    (2') Visitor applies filters → @uc:05 is triggered and the list refreshes with filtered results.
  ],
)

#use-case(
  name:           [Filter Matrices],
  description:    [The visitor narrows the matrix catalog by applying a free-text search and optional dropdown filters (kingdom, source type) to find matrices of interest.],
  actors:         [Visitor (primary).],
  trigger:        [The visitor types in the search box or selects a filter value in the Browse Matrices tab.],
  preconditions:  [The Browse Matrix Catalog view is open (@uc:04 is active).],
  postconditions: [The catalog list is refreshed to show only matrices that match all applied filter criteria.],
  normal-flow: (
    [Visitor types a species name or keyword in the search box, or selects a kingdom and/or source type from the filter controls.],
    [System sends a query to the API with the applied filter parameters.],
    [System updates the matrix list to show only matching results.],
    [System displays the number of results found.],
  ),
  alt-flows: [
    (3') No matrices match the criteria → system displays a "No results found" message and a suggestion to clear filters.
  ],
)

#use-case(
  name:           [View Matrix Detail],
  description:    [A visitor selects a matrix from the catalog to inspect its full metadata, projection matrices (A, U, F), stage names, and a rendered life-cycle network diagram.],
  actors:         [Visitor (primary).],
  trigger:        [The visitor clicks on a matrix entry in the catalog list.],
  preconditions:  [The selected matrix exists and is publicly accessible (or shared with the authenticated user).],
  postconditions: [A detail panel is shown with the full matrix record; the visitor can proceed to export or use the matrix in a simulation.],
  normal-flow: (
    [Visitor clicks a matrix entry in the catalog.],
    [System fetches the full matrix record from the API.],
    [System displays the A matrix as a labelled grid, stage names, and species metadata (kingdom, country, source).],
    [System renders the life-cycle network diagram.],
    [System shows "Export" and "Simulate with this matrix" controls.],
  ),
)

#use-case(
  name:           [Export Matrix],
  description:    [A visitor downloads a population matrix from the detail view as a structured JSON or CSV file for use in external tools.],
  actors:         [Visitor (primary).],
  trigger:        [The visitor clicks "Export as JSON" or "Export as CSV" in the matrix detail panel.],
  preconditions:  [A matrix detail view is open.],
  postconditions: [A file is downloaded to the visitor's device in the chosen format.],
  normal-flow: (
    [Visitor selects "Export as JSON" or "Export as CSV" in the matrix detail panel.],
    [System calls the export endpoint with the appropriate format parameter.],
    [System returns the file in the requested format.],
    [The browser downloads the file to the visitor's device.],
  ),
)

// ── Custom Matrices ────────────────────────────────────────────────────────────

#use-case(
  name:           [Create Custom Matrix],
  description:    [An authenticated user defines a new population projection matrix by providing its name, dimensions, stage names, and matrix values. The matrix is stored privately by default.],
  actors:         [Registered User (primary).],
  trigger:        [The user clicks "New Matrix" in the My Matrices tab.],
  preconditions:  [The user is authenticated.],
  postconditions: [A new custom matrix record is persisted with visibility "private"; it appears in the user's matrix list and is available for simulations.],
  normal-flow: (
    [User navigates to the "My Matrices" tab and clicks "New Matrix".],
    [System presents the matrix creation form.],
    [User enters the matrix name, number of stages, stage names, and the projection matrix A values.],
    [User optionally fills in the U (survival) and F (fertility) sub-matrices.],
    [User submits the form.],
    [System validates that all required fields are complete and that matrix values are non-negative.],
    [System persists the matrix with visibility set to "private" and the current user as owner.],
    [System displays the new matrix in the user's list.],
  ),
  alt-flows: [
    (7') User sets visibility to "shared" or "public" before submitting → @uc:11 is applied immediately on creation.
  ],
  exceptions: [
    (6') A required field is empty or a matrix value is negative → system highlights the invalid fields and blocks submission.
  ],
)

#use-case(
  name:           [Edit Custom Matrix],
  description:    [An authenticated user modifies the name, stage names, or matrix values of a custom matrix they own. Previously saved simulations are unaffected because they store a matrix snapshot.],
  actors:         [Registered User (primary).],
  trigger:        [The user clicks "Edit" on a matrix they own in the My Matrices tab.],
  preconditions:  [The user is authenticated; the selected matrix is owned by the user (source_type = "custom").],
  postconditions: [The matrix record is updated; all future simulations using it will use the new values; existing simulations retain their snapshot.],
  normal-flow: (
    [User clicks "Edit" on a custom matrix.],
    [System loads the current matrix values into the edit form.],
    [User modifies name, stage names, and/or matrix values.],
    [User submits the changes.],
    [System validates the updated values.],
    [System persists the changes and returns the updated matrix.],
    [System confirms the update and refreshes the detail view.],
  ),
  exceptions: [
    (5') Updated value is negative or a required field is empty → validation error per field. \
    (5'') User attempts to edit a COMPADRE matrix → system returns 403 Forbidden.
  ],
)

#use-case(
  name:           [Delete Custom Matrix],
  description:    [An authenticated user permanently removes one of their own custom matrices. Existing simulations that referenced the matrix are unaffected due to snapshot storage.],
  actors:         [Registered User (primary).],
  trigger:        [The user clicks "Delete" on a matrix they own.],
  preconditions:  [The user is authenticated; the selected matrix is owned by the user.],
  postconditions: [The matrix record is deleted; the matrix no longer appears in any catalog or list; existing simulation snapshots are preserved.],
  normal-flow: (
    [User clicks "Delete" on a custom matrix.],
    [System presents a confirmation dialog.],
    [User confirms the deletion.],
    [System deletes the matrix record.],
    [System removes the matrix from the user's list and refreshes the view.],
  ),
  alt-flows: [
    (3') User cancels the confirmation dialog → no changes are made.
  ],
  exceptions: [
    (4') User attempts to delete a COMPADRE matrix → system returns 403 Forbidden.
  ],
)

#use-case(
  name:           [Manage Matrix Visibility],
  description:    [An authenticated user changes the visibility level of one of their own custom matrices, controlling whether it is private, shared with specific users, or publicly listed in the catalog.],
  actors:         [Registered User (primary).],
  trigger:        [The user changes the visibility selector on a matrix they own.],
  preconditions:  [The user is authenticated; the matrix is owned by the user.],
  postconditions: [The matrix visibility is updated; public matrices appear in the public catalog; shared matrices are accessible only to explicitly listed users.],
  normal-flow: (
    [User opens a custom matrix in "My Matrices".],
    [User selects the target visibility level (private / shared / public) from the visibility control.],
    [System updates the matrix visibility field.],
    [System confirms the change.],
  ),
)

#use-case(
  name:           [Share Matrix with User],
  description:    [An authenticated user grants read access to one of their own custom matrices to another specific registered user, identified by username.],
  actors:         [Registered User (primary).],
  trigger:        [The user clicks "Share" on a custom matrix they own and enters a recipient username.],
  preconditions:  [The user is authenticated; the matrix is owned by the user; matrix visibility is set to "shared".],
  postconditions: [A MatrixShare record is created; the recipient can access the matrix in their browse view.],
  normal-flow: (
    [User opens a custom matrix and clicks "Share".],
    [System presents the share form.],
    [User enters the recipient's username.],
    [User submits the share request.],
    [System looks up the recipient by username.],
    [System creates a MatrixShare record linking the matrix and the recipient.],
    [System confirms the share with the recipient's username.],
  ),
  exceptions: [
    (5') Recipient username does not exist → system returns an error message. \
    (6') The matrix is already shared with this user → system shows an informational message.
  ],
)

#use-case(
  name:           [Import Matrices],
  description:    [An authenticated user bulk-imports one or more custom matrices from a JSON file or ZIP archive. The system processes each entry and reports the outcome per matrix.],
  actors:         [Registered User (primary).],
  trigger:        [The user clicks "Import" in the My Matrices tab and uploads a file.],
  preconditions:  [The user is authenticated; the file is a valid JSON array or a ZIP of JSON files.],
  postconditions: [Valid matrices are persisted under the user's account; a BatchImportResult is returned showing successful imports and any per-entry errors.],
  normal-flow: (
    [User clicks "Import" in the My Matrices tab.],
    [System presents the file upload control.],
    [User selects a JSON or ZIP file and submits.],
    [System validates the file format and parses matrix definitions.],
    [System creates a matrix record for each valid definition, setting the current user as owner.],
    [System returns a BatchImportResult listing the number of imported matrices and any skipped entries with reasons.],
    [System refreshes the user's matrix list.],
  ),
  exceptions: [
    (4') The file format is invalid or cannot be parsed → system returns a descriptive error; no matrices are imported. \
    (5') An individual matrix definition is malformed → that entry is skipped and reported in the result; valid entries are still imported.
  ],
)

// ── Simulations ────────────────────────────────────────────────────────────────

#use-case(
  name:           [Run Deterministic Simulation],
  description:    [The user selects a single population matrix and an initial population vector, then runs a deterministic simulation to project stage-structured population dynamics and obtain demographic analytics.],
  actors:         [Visitor (primary - ephemeral run); Registered User (primary - may also save the result).],
  trigger:        [User completes the simulation parameter form and clicks "Run".],
  preconditions:  [At least one matrix is accessible (public, shared, or owned by the user). The API is available.],
  postconditions: [A line plot of population size per stage over time is displayed; demographic analytics are computed and shown alongside the plot.],
  normal-flow: (
    [User selects a matrix from the catalog or from their own matrices.],
    [System retrieves the matrix and displays the stage names.],
    [User selects "Deterministic" simulation mode.],
    [User enters the initial population vector (one non-negative value per stage).],
    [User enters the number of time steps (1–1000).],
    [User clicks "Run".],
    [System validates input dimensions and value ranges.],
    [System computes the trajectory $bold(v)(t+1) = bold(A) dot.op bold(v)(t)$ for each step.],
    [System displays a line plot of population size per stage over time.],
    [System computes and displays: dominant eigenvalue $lambda_1$, stable stage distribution, reproductive values, sensitivity matrix, and elasticity matrix.],
  ),
  alt-flows: [
    (10') User clicks "Save" after reviewing the result → @uc:16 is triggered to persist the run.
  ],
  exceptions: [
    (4') Any component of the initial vector is negative → validation error; submission is blocked. \
    (5') Number of time steps is outside [1, 1000] → validation error; submission is blocked.
  ],
)

#use-case(
  name:           [Run Stochastic Simulation],
  description:    [The user selects two or more population matrices of the same dimension and runs a stochastic simulation consisting of N independent runs, each committing to one randomly-chosen matrix for the full time horizon, producing ensemble mean, variance, and min/max trajectories.],
  actors:         [Visitor (primary - ephemeral run); Registered User (primary - may also save the result).],
  trigger:        [User completes the stochastic simulation parameter form and clicks "Run".],
  preconditions:  [At least two matrices of identical dimension are accessible. The API is available.],
  postconditions: [The ensemble mean trajectory is plotted (one line per stage) with a shaded min/max band; stochastic analytics are displayed.],
  normal-flow: (
    [User selects two or more matrices.],
    [System validates that all selected matrices share the same dimension.],
    [User selects "Stochastic" simulation mode.],
    [User enters the initial population vector.],
    [User enters the number of time steps (1–1 000).],
    [User enters the number of runs (10–1 000; default 100).],
    [User optionally sets a random seed for reproducibility.],
    [User clicks "Run".],
    [System executes $N$ independent runs; each run commits to one matrix chosen uniformly at random (once per run) and projects $bold(v)(t+1) = bold(A)_i dot.op bold(v)(t)$ for all $T$ steps. Mean, variance, minimum, and maximum trajectories are computed across all runs.],
    [System displays the stochastic trajectory plot: mean trajectory (one line per stage) with a shaded min/max band representing the spread across runs.],
    [System computes and displays: stochastic long-run growth rate $lambda_s$, mean projection matrix, and elasticities of the mean.],
  ),
  alt-flows: [
    (11') User clicks "Save" → @uc:16 is triggered; random seed, number of runs, committed matrix index per run, and per-run statistics (variance, min/max histories) are stored for reproducibility.
  ],
  exceptions: [
    (2') Selected matrices have mismatched dimensions → system shows an error immediately and prevents the run. \
    (4') Any component of the initial vector is negative → validation error; submission is blocked.
  ],
)

#use-case(
  name:           [Save Simulation],
  description:    [An authenticated user persists the result of a completed simulation run to their account, storing a matrix snapshot so that the record is immune to future edits or deletions of the source matrices.],
  actors:         [Registered User (primary).],
  trigger:        [User clicks "Save" on a completed simulation result.],
  preconditions:  [User is authenticated; a simulation result is currently displayed (@uc:14 or @uc:15 has completed).],
  postconditions: [The simulation run is stored with its parameters, matrix snapshot, result history, and computed analytics; it appears in the user's saved simulations list.],
  normal-flow: (
    [User clicks "Save" in the simulation result view.],
    [System prompts the user for an optional run name.],
    [User enters a name or leaves it blank and confirms.],
    [System stores the run, capturing the matrix values at the time of saving (snapshot).],
    [System confirms the save and adds the run to the user's saved simulations list.],
  ),
)

#use-case(
  name:           [Browse Saved Simulations],
  description:    [An authenticated user views the list of their previously saved simulation runs and reopens any run to restore its parameters, trajectory plot, and analytics.],
  actors:         [Registered User (primary).],
  trigger:        [User opens the "Library" panel in the Simulate tab.],
  preconditions:  [User is authenticated.],
  postconditions: [The list of saved runs is displayed; the user can inspect or delete any run.],
  normal-flow: (
    [User opens the "Library" view in the Simulate tab.],
    [System fetches the user's saved runs from the API, ordered by creation date descending.],
    [System displays the list with run name, creation date, simulation mode (deterministic / stochastic), and matrix names.],
    [User clicks a run to reload it.],
    [System restores the simulation view: trajectory plot, analytics, and original parameters.],
  ),
  alt-flows: [
    (4') User clicks "Delete" on a run → system asks for confirmation, then removes the record and refreshes the list.
  ],
)

// ── Ecological Analytics ───────────────────────────────────────────────────────

#use-case(
  name:           [View Demographic Analytics],
  description:    [After any simulation is executed, the system automatically computes and displays ecological demographic analytics alongside the population trajectory plot, without requiring a separate navigation step.],
  actors:         [Visitor (primary - analytics are shown on ephemeral runs); Registered User (primary - also on saved runs).],
  trigger:        [A simulation run completes (this use case is included in @uc:14 and @uc:15).],
  preconditions:  [A simulation result is available.],
  postconditions: [Demographic analytics are displayed in the simulation result panel.],
  normal-flow: (
    [Simulation computation completes (@uc:14 or @uc:15).],
    [System computes analytics server-side from the run parameters and matrix.],
    [For a deterministic run: system displays $lambda_1$ (dominant eigenvalue), stable stage distribution, reproductive values, sensitivity matrix, and elasticity matrix.],
    [For a stochastic run: system displays $lambda_s$ (stochastic growth rate), mean projection matrix, and elasticities of the mean.],
    [All metrics are shown in the same view as the trajectory plot.],
  ),
)

// ── Quasi-Extinction ───────────────────────────────────────────────────────────

#use-case(
  name:           [Run Quasi-Extinction Analysis],
  description:    [An authenticated user submits an asynchronous Monte Carlo quasi-extinction job to estimate the cumulative probability that a stochastic population falls below a given threshold within a defined time horizon. The job runs in the background and its result is retrieved by polling.],
  actors:         [Registered User (primary).],
  trigger:        [User configures the analysis parameters and clicks "Run Analysis" in the Quasi-Extinction tab.],
  preconditions:  [User is authenticated; at least one matrix is selected; the API is available.],
  postconditions: [A background job is created; on completion, the system displays a cumulative quasi-extinction probability curve over time.],
  normal-flow: (
    [User opens the Quasi-Extinction tab.],
    [User selects one or more population matrices.],
    [User enters the initial population vector, global extinction threshold, and time horizon.],
    [User optionally configures stage-level settings (@uc:20).],
    [User clicks "Run Analysis".],
    [System submits the job and returns HTTP 202; job status is set to "pending".],
    [System displays a progress indicator.],
    [Background task runs the Monte Carlo simulation and updates job status to "running", then "completed".],
    [System stores the quasi-extinction probability result in the job record.],
    [System renders the cumulative quasi-extinction probability curve (probability vs. time step).],
  ),
  alt-flows: [
    (7') User navigates away from the tab - the job continues running in the background; the progress indicator is shown again when the user returns.
  ],
  exceptions: [
    (3') Extinction threshold is ≤ 0 or time horizon is ≤ 0 → validation error; submission is blocked. \
    (8') Job fails server-side → system sets job status to "failed" and displays an error message with a retry option.
  ],
)

#use-case(
  name:           [Configure Extinction Stages],
  description:    [Before running a quasi-extinction analysis, the user customises which population stages are included in the extinction threshold comparison and optionally sets per-stage threshold values.],
  actors:         [Registered User (primary).],
  trigger:        [User opens the stage configuration panel in the Quasi-Extinction tab.],
  preconditions:  [User is authenticated; at least one matrix is selected in the quasi-extinction form; @uc:19 has not yet been submitted.],
  postconditions: [Stage inclusion flags and per-stage thresholds are recorded in the job parameter object to be submitted with @uc:19.],
  normal-flow: (
    [User opens the stage configuration panel.],
    [System displays all stages derived from the selected matrices, each with an enable/disable toggle and a threshold field.],
    [User enables or disables individual stages and enters per-stage threshold values.],
    [User confirms the configuration.],
    [System records the stage settings in the pending job parameters.],
  ),
  alt-flows: [
    (4') User clicks "Reset to defaults" → all stages are enabled and the global threshold is restored.
  ],
)

// ── Internationalisation ───────────────────────────────────────────────────────

#use-case(
  name:           [Select Language],
  description:    [Any user selects the interface language from the six supported options (English, Spanish, Asturian, Galician, Basque, Catalan). The preference is applied immediately for the current session.],
  actors:         [Visitor (primary).],
  trigger:        [User clicks the language selector control.],
  preconditions:  [None.],
  postconditions: [The interface is rendered in the selected language for the current session.],
  normal-flow: (
    [User clicks the language selector.],
    [System displays the list of available languages: English (EN), Spanish (ES), Asturian (AS), Galician (GL), Basque (EU), Catalan (CA).],
    [User selects a language.],
    [System re-renders the interface text in the chosen language.],
  ),
)
