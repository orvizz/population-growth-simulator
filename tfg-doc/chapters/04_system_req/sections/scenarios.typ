// chapters/04_system_req/sections/scenarios.typ
#import "../../../template.typ": scenario

===== Authentication

#scenario(
  name: [Successful Registration],
  description: [A visitor creates a new account by providing a valid email address and a password that meets the minimum requirements.],
  actors: [Visitor],
  trigger: [Visitor submits the registration form with valid credentials.],
  preconditions: [The provided email address is not already registered in the system.],
  postconditions: [A new user account is created and stored in the database. The visitor is now a registered user.],
  sequence: (
    [Visitor navigates to the Account tab and selects "Register".],
    [Visitor enters email address and a password with at least 8 characters.],
    [Visitor clicks the "Register" button.],
    [System sends `POST /v1/auth/register` with the provided credentials.],
    [System validates the email format and password strength.],
    [System creates the user record in the database.],
    [System returns a 201 Created response with the new user's ID and email.],
    [UI displays a success message and transitions to the login view.],
  ),
)

#scenario(
  name: [Registration with Duplicate Email],
  description: [A visitor attempts to register with an email address already associated with an existing account.],
  actors: [Visitor],
  trigger: [Visitor submits the registration form with an email already in the system.],
  preconditions: [An account with the submitted email address already exists.],
  postconditions: [No new account is created. The visitor remains on the registration form.],
  sequence: (
    [Visitor navigates to the Account tab and selects "Register".],
    [Visitor enters an email address that belongs to an existing account.],
    [Visitor enters a valid password and clicks "Register".],
    [System sends `POST /v1/auth/register` with the provided data.],
    [System finds an existing user with the same email.],
    [System returns a 400 Bad Request response with message "Email already registered".],
    [UI displays the error message below the email field.],
  ),
)

#scenario(
  name: [Registration with Weak Password],
  description: [A visitor attempts to register with a password that does not meet the minimum length requirement.],
  actors: [Visitor],
  trigger: [Visitor submits the registration form with a password shorter than 8 characters.],
  preconditions: [The system is accessible and the registration form is open.],
  postconditions: [No account is created. The form remains active with the error highlighted.],
  sequence: (
    [Visitor opens the registration form.],
    [Visitor enters a valid email and a 4-character password.],
    [Visitor clicks "Register".],
    [System sends `POST /v1/auth/register` with the provided data.],
    [System validates the password and detects it is below the minimum length.],
    [System returns a 422 Unprocessable Entity response with a password validation error.],
    [UI displays "Password must be at least 8 characters" next to the password field.],
  ),
)

#scenario(
  name: [Successful Login],
  description: [A registered user authenticates with correct credentials and receives a JWT session token.],
  actors: [Registered User],
  trigger: [Registered user submits the login form with correct email and password.],
  preconditions: [An account with the provided email exists and the password is correct.],
  postconditions: [A JWT token is issued and stored client-side. The user can access protected features.],
  sequence: (
    [User navigates to the Account tab and selects "Log In".],
    [User enters their registered email and correct password.],
    [User clicks "Log In".],
    [System sends `POST /v1/auth/login` with OAuth2 password-form credentials.],
    [System validates the email and verifies the password hash.],
    [System generates a JWT token with a 7-day expiry and returns it in the response.],
    [UI stores the token in the session state.],
    [UI unlocks the Simulate, My Matrices, and Account-logout features.],
  ),
)

#scenario(
  name: [Login with Wrong Credentials],
  description: [A visitor attempts to log in with an incorrect password.],
  actors: [Visitor],
  trigger: [Visitor submits the login form with an incorrect password.],
  preconditions: [An account with the submitted email exists, but the password does not match.],
  postconditions: [No token is issued. The visitor remains unauthenticated.],
  sequence: (
    [Visitor opens the login form.],
    [Visitor enters a registered email and an incorrect password.],
    [Visitor clicks "Log In".],
    [System sends `POST /v1/auth/login`.],
    [System locates the user record but password hash comparison fails.],
    [System returns a 401 Unauthorized response with message "Invalid credentials".],
    [UI displays the error message and clears the password field.],
  ),
)

#scenario(
  name: [Successful Logout],
  description: [An authenticated user ends their session and returns to the unauthenticated state.],
  actors: [Registered User],
  trigger: [Authenticated user clicks "Log Out".],
  preconditions: [User holds a valid JWT token in the session state.],
  postconditions: [The session token is discarded client-side. The user can no longer access protected features.],
  sequence: (
    [Authenticated user navigates to the Account tab.],
    [User clicks the "Log Out" button.],
    [UI removes the JWT token from the session state.],
    [UI re-renders the Account tab showing the login/register form.],
    [Protected tabs (Simulate, My Matrices) revert to requiring authentication.],
  ),
)

===== Browse Matrices

#scenario(
  name: [Default Catalog View],
  description: [A visitor opens the Browse tab and sees the full list of available matrices without any active filters.],
  actors: [Visitor],
  trigger: [Visitor navigates to the Browse Matrices tab.],
  preconditions: [The API is running and the database contains at least one matrix record.],
  postconditions: [A paginated list of matrices is shown with name, species, and source type for each entry.],
  sequence: (
    [Visitor opens the application and clicks the "Browse Matrices" tab.],
    [UI sends `GET /v1/matrices` with no filter parameters.],
    [System queries the database for all visible matrices.],
    [System returns a JSON list of matrix summary records.],
    [UI renders the matrix list in a table with columns: Name, Species, Source, Dimension.],
  ),
)

#scenario(
  name: [Catalog View with Active Filter],
  description: [A visitor has already applied a species filter and the catalog shows only matching matrices.],
  actors: [Visitor],
  trigger: [Visitor applies a species filter after the catalog is already loaded.],
  preconditions: [The catalog is loaded (see @sc:07). The filter form is visible.],
  postconditions: [Only matrices matching the species filter are displayed. The filter input reflects the active query.],
  sequence: (
    [Visitor types "Loxodonta africana" into the species filter input.],
    [UI sends `GET /v1/matrices?species=Loxodonta+africana`.],
    [System queries the database filtering by species name.],
    [System returns the matching matrix records.],
    [UI replaces the current list with the filtered results.],
    [UI shows the number of results found (e.g., "3 matrices found").],
  ),
)

#scenario(
  name: [Filter Returns Results],
  description: [A visitor enters a species name into the filter and the system returns matching matrices.],
  actors: [Visitor],
  trigger: [Visitor submits a species filter that matches at least one matrix in the catalog.],
  preconditions: [The Browse Matrices tab is open. At least one matrix matching the filter exists.],
  postconditions: [The list shows only matrices matching the filter criteria.],
  sequence: (
    [Visitor opens the Filter panel in the Browse Matrices tab.],
    [Visitor types "Panthera leo" in the species field.],
    [UI sends `GET /v1/matrices?species=Panthera+leo`.],
    [System returns a non-empty list of matching matrices.],
    [UI renders the filtered list; the result count badge updates to reflect the number of matches.],
  ),
)

#scenario(
  name: [Filter Returns No Results],
  description: [A visitor enters a filter value that does not match any matrix in the catalog.],
  actors: [Visitor],
  trigger: [Visitor submits a filter that matches no matrix.],
  preconditions: [The Browse Matrices tab is open.],
  postconditions: [The matrix list is empty. A "No results found" message is displayed.],
  sequence: (
    [Visitor opens the Filter panel.],
    [Visitor types "ZZZUNKNOWN" in the species field.],
    [UI sends `GET /v1/matrices?species=ZZZUNKNOWN`.],
    [System finds no matching records and returns an empty list.],
    [UI hides the matrix table and displays "No matrices found matching your criteria."],
  ),
)

#scenario(
  name: [View Matrix Detail],
  description: [A visitor selects a matrix from the catalog to inspect its full metadata and coefficient values.],
  actors: [Visitor],
  trigger: [Visitor clicks on a matrix row in the catalog.],
  preconditions: [The Browse Matrices tab is loaded and at least one matrix is listed.],
  postconditions: [The detail panel shows the full matrix_a values, stage names, metadata, and source type.],
  sequence: (
    [Visitor clicks on a matrix row in the catalog list.],
    [UI sends `GET /v1/matrices/{id}` for the selected matrix.],
    [System retrieves the full matrix record including matrix_a, metadata, and stage names.],
    [UI renders the detail panel with the matrix coefficients in a grid, stage labels, species information, and lifecycle metadata.],
  ),
)

#scenario(
  name: [Export Matrix as JSON],
  description: [A visitor downloads a matrix as a JSON file for offline use or import into another system.],
  actors: [Visitor],
  trigger: [Visitor selects "Export as JSON" on a matrix detail view.],
  preconditions: [A matrix detail is open (see @sc:12).],
  postconditions: [A JSON file containing the matrix data is downloaded to the visitor's device.],
  sequence: (
    [Visitor clicks the "Export" button in the matrix detail panel.],
    [Visitor selects "JSON" from the format dropdown.],
    [UI sends `GET /v1/matrices/{id}/export`.],
    [System serialises the matrix record to JSON format.],
    [Browser downloads the file as `{matrix-name}.json`.],
  ),
)

#scenario(
  name: [Export Matrix as CSV],
  description: [A visitor downloads the matrix coefficients as a CSV file for analysis in a spreadsheet application.],
  actors: [Visitor],
  trigger: [Visitor selects "Export as CSV" on a matrix detail view.],
  preconditions: [A matrix detail is open (see @sc:12).],
  postconditions: [A CSV file containing the matrix_a values is downloaded to the visitor's device.],
  sequence: (
    [Visitor clicks the "Export" button in the matrix detail panel.],
    [Visitor selects "CSV" from the format dropdown.],
    [UI sends `GET /v1/matrices/{id}/export?format=csv`.],
    [System serialises the matrix_a values to CSV with stage names as column headers.],
    [Browser downloads the file as `{matrix-name}.csv`.],
  ),
)

===== Custom Matrices

#scenario(
  name: [Create Custom Matrix - Valid Input],
  description: [A registered user creates a new custom population matrix by filling in the matrix editor form with valid data.],
  actors: [Registered User],
  trigger: [User submits the Create Matrix form with a valid name, stage names, and a square matrix of coefficients.],
  preconditions: [User is authenticated. The My Matrices tab is open.],
  postconditions: [A new custom matrix record is persisted in the database. The matrix appears in the user's matrix list and in the public catalog.],
  sequence: (
    [User navigates to the My Matrices tab and clicks "Create New Matrix".],
    [User enters the matrix name "Test Population 3x3".],
    [User defines 3 stage names: "Juvenile", "Subadult", "Adult".],
    [User fills in 9 coefficient values forming a valid 3×3 matrix.],
    [User clicks "Save".],
    [UI sends `POST /v1/matrices` with the matrix data and Authorization header.],
    [System validates the matrix dimensions and value types.],
    [System persists the matrix record with `source_type = "custom"`.],
    [System returns the created matrix record with its new ID.],
    [UI adds the matrix to the My Matrices list and shows a success toast.],
  ),
)

#scenario(
  name: [Create Custom Matrix - Validation Error],
  description: [A registered user submits the Create Matrix form with inconsistent data (stage count does not match matrix dimensions).],
  actors: [Registered User],
  trigger: [User submits a matrix form where the number of declared stages does not match the coefficient grid dimensions.],
  preconditions: [User is authenticated. The Create Matrix form is open.],
  postconditions: [No matrix is created. The form is retained with the error highlighted.],
  sequence: (
    [User opens the Create Matrix form.],
    [User declares 3 stages but fills in only a 2×2 grid of coefficients.],
    [User clicks "Save".],
    [UI detects the mismatch between stage count (3) and matrix dimension (2).],
    [UI displays an inline error: "Matrix dimensions must match the number of stages (3×3 required)".],
    [No API call is made. The form remains active.],
  ),
)

#scenario(
  name: [Edit Own Custom Matrix],
  description: [A registered user modifies a coefficient in one of their own custom matrices.],
  actors: [Registered User],
  trigger: [User submits a matrix edit form for a matrix they own.],
  preconditions: [User is authenticated and owns at least one custom matrix. The matrix detail is open in edit mode.],
  postconditions: [The matrix record is updated in the database. The new coefficient value is reflected in the UI.],
  sequence: (
    [User navigates to My Matrices and selects one of their matrices.],
    [User clicks "Edit".],
    [User changes the (1,2) coefficient from 0.3 to 0.45.],
    [User clicks "Save Changes".],
    [UI sends `PATCH /v1/matrices/{id}` with the updated matrix_a values and Authorization header.],
    [System verifies the user owns the matrix and the source_type is "custom".],
    [System updates the matrix record.],
    [System returns the updated matrix record.],
    [UI shows a success toast and refreshes the matrix detail.],
  ),
)

#scenario(
  name: [Attempt Edit on COMPADRE Matrix],
  description: [A registered user tries to edit a read-only COMPADRE matrix and the system blocks the operation.],
  actors: [Registered User],
  trigger: [User attempts to save changes to a matrix with `source_type = "compadre"`.],
  preconditions: [User is authenticated. A COMPADRE matrix detail is open.],
  postconditions: [The matrix is not modified. An error message is shown to the user.],
  sequence: (
    [User selects a COMPADRE matrix from the catalog.],
    [User attempts to activate edit mode (Edit button is disabled for COMPADRE matrices in the UI).],
    [UI displays a tooltip: "COMPADRE matrices are read-only and cannot be edited."],
    [If a direct API call is attempted, the system returns 403 Forbidden.],
    [No change is applied to the matrix record.],
  ),
)

#scenario(
  name: [Delete Custom Matrix - Confirmed],
  description: [A registered user permanently deletes one of their own custom matrices after confirming the action.],
  actors: [Registered User],
  trigger: [User confirms the deletion dialog for one of their matrices.],
  preconditions: [User is authenticated and owns the matrix to be deleted. The matrix is not referenced by any stored simulation.],
  postconditions: [The matrix record is removed from the database. It no longer appears in the catalog or the user's list.],
  sequence: (
    [User navigates to My Matrices and selects a matrix to delete.],
    [User clicks "Delete".],
    [UI shows a confirmation dialog: "Are you sure? This cannot be undone."],
    [User clicks "Confirm Delete".],
    [UI sends `DELETE /v1/matrices/{id}` with Authorization header.],
    [System verifies ownership, then deletes the record.],
    [System returns 204 No Content.],
    [UI removes the matrix from the list and shows a success toast.],
  ),
)

#scenario(
  name: [Delete Custom Matrix - Cancelled],
  description: [A registered user initiates the delete flow but cancels before confirming, leaving the matrix intact.],
  actors: [Registered User],
  trigger: [User clicks "Delete" on a matrix but then dismisses the confirmation dialog.],
  preconditions: [User is authenticated and the matrix detail or list is open.],
  postconditions: [No API call is made. The matrix record remains unchanged.],
  sequence: (
    [User clicks "Delete" next to one of their matrices.],
    [UI shows a confirmation dialog.],
    [User clicks "Cancel".],
    [UI closes the dialog. No HTTP request is sent.],
    [The matrix remains in the list unchanged.],
  ),
)

#scenario(
  name: [Change Matrix Visibility to Public],
  description: [A registered user changes one of their private custom matrices to publicly visible so that all users can browse it.],
  actors: [Registered User],
  trigger: [User sets the visibility of their matrix to "Public" and saves.],
  preconditions: [User is authenticated and owns the matrix. The matrix has `visibility = "private"`.],
  postconditions: [The matrix visibility is updated to "public". Any visitor can now see it in the catalog.],
  sequence: (
    [User opens the detail or edit view of their matrix in My Matrices.],
    [User opens the Visibility selector and changes the value from "Private" to "Public".],
    [User clicks "Save".],
    [UI sends `PATCH /v1/matrices/{id}` with `{"visibility": "public"}` and Authorization header.],
    [System updates the visibility field in the database.],
    [System returns the updated matrix record.],
    [UI reflects the new visibility status in the matrix detail header.],
  ),
)

#scenario(
  name: [Share Matrix with Existing User],
  description: [A registered user grants access to one of their private matrices to another registered user by entering their email.],
  actors: [Registered User],
  trigger: [User submits the share form with the email of a registered user.],
  preconditions: [User is authenticated and owns the matrix. The target email belongs to a registered user.],
  postconditions: [The target user can access the matrix even though it is not fully public.],
  sequence: (
    [User opens their matrix detail and navigates to the "Share" section.],
    [User enters "user\@example.com" in the share input and clicks "Share".],
    [UI sends `PATCH /v1/matrices/{id}` with the share target data and Authorization header.],
    [System looks up the user by email and confirms they exist.],
    [System adds the target user to the matrix's shared-with list.],
    [System returns the updated matrix record.],
    [UI shows a success message: "Matrix shared with user\@example.com".],
  ),
)

#scenario(
  name: [Share Matrix with Unknown User],
  description: [A registered user attempts to share a matrix with an email that does not belong to any registered user.],
  actors: [Registered User],
  trigger: [User submits the share form with an unregistered email address.],
  preconditions: [User is authenticated and owns the matrix. The target email is not in the system.],
  postconditions: [The matrix sharing is not performed. An error is shown.],
  sequence: (
    [User opens their matrix detail and navigates to the "Share" section.],
    [User enters "unknown\@nowhere.xyz" in the share input and clicks "Share".],
    [UI sends `PATCH /v1/matrices/{id}` with the share target data.],
    [System searches for the user by email and finds no match.],
    [System returns 404 Not Found with message "User not found".],
    [UI displays the error: "No registered user found with that email address".],
  ),
)

#scenario(
  name: [Import Matrices - All Valid],
  description: [A registered user uploads a ZIP file containing multiple valid matrix JSON files. All matrices are imported successfully.],
  actors: [Registered User],
  trigger: [User uploads a ZIP archive containing 3 valid matrix JSON files.],
  preconditions: [User is authenticated. Each JSON file in the archive conforms to the matrix schema.],
  postconditions: [3 new custom matrix records are created. The import summary shows 3 successes and 0 errors.],
  sequence: (
    [User navigates to My Matrices and clicks "Import".],
    [User selects a ZIP file containing `matrix1.json`, `matrix2.json`, and `matrix3.json`.],
    [UI sends `POST /v1/matrices/import` with the ZIP file as multipart/form-data.],
    [System unpacks the ZIP and validates each JSON file against the matrix schema.],
    [System creates 3 matrix records and returns a `BatchImportResult` with 3 created entries.],
    [UI displays the summary: "3 matrices imported successfully (0 errors)".],
    [The 3 new matrices appear in the My Matrices list.],
  ),
)

#scenario(
  name: [Import Matrices - Partial Errors],
  description: [A registered user uploads a ZIP file where one JSON file is malformed. The valid files are imported and the invalid one is reported.],
  actors: [Registered User],
  trigger: [User uploads a ZIP archive containing 2 valid and 1 invalid matrix JSON files.],
  preconditions: [User is authenticated. One of the JSON files has a missing required field.],
  postconditions: [2 matrices are created. The import summary lists 1 error entry identifying the invalid file.],
  sequence: (
    [User selects a ZIP file containing `matrix1.json` (valid), `matrix2.json` (valid), and `bad.json` (missing `matrix_a` field).],
    [UI sends `POST /v1/matrices/import` with the ZIP.],
    [System validates each file; `bad.json` fails validation.],
    [System creates 2 matrix records for the valid files.],
    [System returns a `BatchImportResult` with 2 created and 1 error entry (filename `bad.json`, reason "matrix_a is required").],
    [UI displays: "2 matrices imported. 1 error: bad.json - matrix_a is required".],
  ),
)

===== Simulations

#scenario(
  name: [Ephemeral Deterministic Simulation],
  description: [A visitor runs a deterministic simulation without saving the result. The trajectory and analytics are displayed only for the current session.],
  actors: [Visitor],
  trigger: [Visitor submits the simulation form (not authenticated, or does not save).],
  preconditions: [At least one matrix is available in the catalog.],
  postconditions: [The population trajectory plot and analytics panel are rendered. No simulation record is persisted in the database.],
  sequence: (
    [Visitor navigates to the Simulate tab and selects "Deterministic".],
    [Visitor selects a 3×3 COMPADRE matrix from the matrix selector.],
    [Visitor enters initial vector: Juvenile=100, Subadult=50, Adult=10.],
    [Visitor sets n_steps=50.],
    [Visitor clicks "Run Simulation".],
    [UI sends `POST /v1/simulations/run` with `matrix_id`, `initial_vector`, and `n_steps`.],
    [System computes `v(t+1) = A·v(t)` for 50 steps.],
    [System returns the full trajectory and analytics (λ₁, stable distribution, sensitivities, elasticities).],
    [UI renders a line plot of population per stage over time.],
    [UI renders the analytics panel below the plot.],
  ),
)

#scenario(
  name: [Deterministic Simulation Saved to Database],
  description: [An authenticated user runs a deterministic simulation and saves the result for future reference.],
  actors: [Registered User],
  trigger: [Authenticated user submits the simulation form via the save endpoint.],
  preconditions: [User is authenticated. A matrix is selected. The initial vector and n_steps are valid.],
  postconditions: [A `SimulationRun` record is persisted with the trajectory, analytics, and a snapshot of the matrix at run time.],
  sequence: (
    [Authenticated user opens the Simulate tab and selects "Deterministic".],
    [User selects a matrix, enters initial vector and n_steps=100.],
    [User clicks "Run and Save".],
    [UI sends `POST /v1/simulations` with `matrix_id`, `initial_vector`, `n_steps`, and Authorization header.],
    [System runs the simulation and computes the full trajectory.],
    [System persists the `SimulationRun` record including `matrices_snapshot`.],
    [System returns the simulation record with its new ID.],
    [UI renders the plot and analytics panel.],
    [UI shows a success toast: "Simulation saved. View it in My Simulations."],
  ),
)

#scenario(
  name: [Deterministic Simulation - Negative Vector Value],
  description: [A visitor submits a simulation with a negative value in the initial population vector, which is rejected by the API.],
  actors: [Visitor],
  trigger: [Visitor enters a negative number in one of the initial vector fields.],
  preconditions: [The Simulate tab is open with a matrix selected.],
  postconditions: [No simulation is run. A validation error is displayed.],
  sequence: (
    [Visitor selects a matrix and sets n_steps=50.],
    [Visitor enters initial vector: Juvenile=-10, Subadult=50, Adult=10.],
    [Visitor clicks "Run Simulation".],
    [UI sends `POST /v1/simulations/run` with the invalid vector.],
    [System validates the initial vector and finds a negative value.],
    [System returns 422 Unprocessable Entity: "initial_vector values must be non-negative".],
    [UI displays the validation error next to the vector input field.],
  ),
)

#scenario(
  name: [Deterministic Simulation - Invalid n_steps],
  description: [A visitor submits a simulation with n_steps set to 0, which falls outside the valid range of [1, 1000].],
  actors: [Visitor],
  trigger: [Visitor enters 0 in the n_steps field.],
  preconditions: [The Simulate tab is open with a matrix selected and valid initial vector.],
  postconditions: [No simulation is run. A validation error is displayed.],
  sequence: (
    [Visitor selects a matrix and enters a valid initial vector.],
    [Visitor sets n_steps=0.],
    [Visitor clicks "Run Simulation".],
    [UI sends `POST /v1/simulations/run` with `n_steps=0`.],
    [System validates the input and finds n_steps is out of the allowed range.],
    [System returns 422 Unprocessable Entity: "n_steps must be between 1 and 1000".],
    [UI highlights the n_steps input with the error message.],
  ),
)

#scenario(
  name: [Stochastic Simulation with Random Seed],
  description: [An authenticated user runs a stochastic simulation using two matrices of the same dimension and a fixed random seed for reproducibility.],
  actors: [Registered User],
  trigger: [User submits the stochastic simulation form with two compatible matrices and a random seed.],
  preconditions: [User is authenticated. Two matrices of the same dimension exist in the system. The Simulate tab is open in stochastic mode.],
  postconditions: [A stochastic simulation trajectory is produced. The result is reproducible using the same seed.],
  sequence: (
    [User selects "Stochastic" mode in the Simulate tab.],
    [User selects two 3×3 matrices from the matrix selector.],
    [User sets random seed to 42 and n_steps to 100.],
    [User enters initial vector: [100, 50, 10].],
    [User clicks "Run Simulation".],
    [UI sends `POST /v1/simulations/run` with `matrix_ids=[id1, id2]`, `random_seed=42`, `initial_vector`, `n_steps=100`.],
    [System picks matrices uniformly at random at each step using seed 42 and computes the trajectory.],
    [System returns the trajectory and stochastic analytics (λ_s, mean matrix, elasticities of the mean).],
    [UI renders the stochastic population plot and the analytics panel.],
  ),
)

#scenario(
  name: [Stochastic Simulation - Dimension Mismatch],
  description: [A user selects two matrices with incompatible dimensions for a stochastic simulation, which the system rejects.],
  actors: [Registered User],
  trigger: [User submits the stochastic simulation form with matrices of different dimensions.],
  preconditions: [User is authenticated. The two selected matrices have different numbers of stages.],
  postconditions: [No simulation is run. An error is shown explaining the dimension incompatibility.],
  sequence: (
    [User selects "Stochastic" mode.],
    [User selects a 3×3 matrix and a 4×4 matrix.],
    [User enters a valid initial vector and clicks "Run Simulation".],
    [UI sends `POST /v1/simulations/run` with `matrix_ids=[id1, id2]`.],
    [System validates the selected matrices and finds incompatible dimensions (3×3 vs 4×4).],
    [System returns 400 Bad Request: "All matrices must have the same dimension".],
    [UI displays the error above the matrix selector.],
  ),
)

#scenario(
  name: [Save Stochastic Simulation],
  description: [An authenticated user saves the result of a stochastic simulation run including the random seed for reproducibility.],
  actors: [Registered User],
  trigger: [User runs a successful stochastic simulation and saves it via the persistent endpoint.],
  preconditions: [User is authenticated. Two compatible matrices are selected. Initial vector and n_steps are valid.],
  postconditions: [A `SimulationRun` record is stored with `stochastic=true`, `matrix_ids`, `random_seed`, and a snapshot of both matrices.],
  sequence: (
    [User selects "Stochastic" mode, picks 2 matrices, sets seed=99, n_steps=200.],
    [User clicks "Run and Save".],
    [UI sends `POST /v1/simulations` with `matrix_ids`, `random_seed=99`, `initial_vector`, `n_steps`, and Authorization header.],
    [System runs the stochastic simulation and records the matrix sequence chosen at each step.],
    [System persists the `SimulationRun` with `matrices_snapshot` for both matrices.],
    [System returns the run record.],
    [UI shows the results plot and a success toast.],
  ),
)

#scenario(
  name: [Save Simulation Result],
  description: [An authenticated user explicitly saves a simulation result immediately after running it.],
  actors: [Registered User],
  trigger: [Authenticated user confirms saving after a simulation is completed.],
  preconditions: [User is authenticated and a simulation result is currently displayed in the UI.],
  postconditions: [The simulation is persisted in the database and accessible from My Simulations.],
  sequence: (
    [User has just completed a simulation run (see @sc:25 or @sc:29).],
    [User clicks "Save Simulation".],
    [UI sends `POST /v1/simulations` with the same parameters used in the run.],
    [System executes the simulation again server-side and stores the result.],
    [System returns the created `SimulationRun` record with its ID.],
    [UI shows "Simulation saved" toast with a link to My Simulations.],
  ),
)

#scenario(
  name: [View Saved Simulation],
  description: [An authenticated user browses their list of saved simulations and opens one to review the results.],
  actors: [Registered User],
  trigger: [User navigates to My Simulations and clicks on a saved run.],
  preconditions: [User is authenticated and has at least one saved simulation.],
  postconditions: [The full simulation detail is shown including trajectory, analytics, and the matrix snapshot used at run time.],
  sequence: (
    [User navigates to the My Simulations section.],
    [UI sends `GET /v1/simulations` with Authorization header.],
    [System returns a list of the user's simulation runs.],
    [UI renders the list with run date, matrix name, and type (deterministic/stochastic).],
    [User clicks on a specific run.],
    [UI sends `GET /v1/simulations/{id}`.],
    [System returns the full run record including history, analytics, and matrices_snapshot.],
    [UI renders the population plot, stage history, and analytics panel for the selected run.],
  ),
)

#scenario(
  name: [Delete Saved Simulation],
  description: [An authenticated user deletes one of their saved simulations from the database.],
  actors: [Registered User],
  trigger: [User clicks "Delete" on a saved simulation and confirms.],
  preconditions: [User is authenticated and owns the simulation to be deleted.],
  postconditions: [The simulation record is removed from the database.],
  sequence: (
    [User opens My Simulations.],
    [User clicks "Delete" next to a saved run.],
    [UI sends `DELETE /v1/simulations/{id}` with Authorization header.],
    [System verifies ownership and removes the record.],
    [System returns 204 No Content.],
    [UI removes the entry from the list and shows a deletion confirmation toast.],
  ),
)

#scenario(
  name: [View Deterministic Demographic Analytics],
  description: [After running a deterministic simulation, the system automatically computes and displays all ecological analytics.],
  actors: [Visitor],
  trigger: [A deterministic simulation run completes (ephemeral or saved).],
  preconditions: [A deterministic simulation result has been received from the API.],
  postconditions: [The analytics panel shows λ₁, stable stage distribution, reproductive values, sensitivity matrix, and elasticity matrix.],
  sequence: (
    [Visitor completes a deterministic simulation run (see @sc:25).],
    [System returns the simulation result including the `analytics` field.],
    [UI extracts λ₁ (dominant eigenvalue) and displays it as the projected population growth rate.],
    [UI renders the stable stage distribution as a bar chart.],
    [UI renders the reproductive value vector.],
    [UI renders the sensitivity matrix as a colour-coded grid.],
    [UI renders the elasticity matrix as a colour-coded grid.],
  ),
)

#scenario(
  name: [View Stochastic Demographic Analytics],
  description: [After running a stochastic simulation, the system displays the stochastic growth rate and mean-matrix elasticities.],
  actors: [Visitor],
  trigger: [A stochastic simulation run completes.],
  preconditions: [A stochastic simulation result has been received from the API.],
  postconditions: [The analytics panel shows λ_s, the mean matrix, and the elasticities of the mean matrix.],
  sequence: (
    [Visitor completes a stochastic simulation run (see @sc:29).],
    [System returns the simulation result including the stochastic `analytics` field.],
    [UI displays λ_s (stochastic growth rate) as the long-run projected growth rate.],
    [UI renders the mean matrix as a coefficient grid.],
    [UI renders the elasticities of the mean matrix as a colour-coded grid.],
  ),
)

===== Quasi-Extinction Analysis

#scenario(
  name: [Quasi-Extinction Job Completes Successfully],
  description: [A registered user submits a quasi-extinction analysis job, polls for completion, and views the resulting probability curve.],
  actors: [Registered User],
  trigger: [User selects a matrix, optionally configures stage thresholds, and submits the quasi-extinction form.],
  preconditions: [User is authenticated. At least one matrix is available. Stage thresholds are set (or defaults are used).],
  postconditions: [A quasi-extinction probability curve is displayed. The job record is stored with status "completed".],
  sequence: (
    [User navigates to the Quasi-Extinction section.],
    [User selects a matrix and sets the extinction threshold to a total population of 10 individuals.],
    [User clicks "Run Analysis".],
    [UI sends `POST /v1/jobs/quasi-extinction` with the configuration and Authorization header.],
    [System creates a job record with status "pending" and returns 202 Accepted with `job_id`.],
    [UI starts polling `GET /v1/jobs/{job_id}` every 2 seconds.],
    [System begins the Monte Carlo simulation task; job status changes to "running".],
    [System completes the computation; job status changes to "completed" with results.],
    [UI receives the completed job on the next poll.],
    [UI renders the quasi-extinction probability curve (probability of extinction vs. time).],
  ),
)

#scenario(
  name: [User Navigates Away and Returns During Job],
  description: [A registered user submits a quasi-extinction job but navigates to another tab before it finishes. When they return, the result is already available.],
  actors: [Registered User],
  trigger: [User returns to the Quasi-Extinction tab after navigating away while a job was running.],
  preconditions: [A quasi-extinction job was submitted and reached "completed" status while the user was on another tab.],
  postconditions: [The completed result is loaded and the probability curve is displayed upon return.],
  sequence: (
    [User submits a quasi-extinction job (see @sc:37, steps 1–5).],
    [UI starts polling the job status.],
    [User navigates to the Browse Matrices tab.],
    [In the background, the job completes on the server.],
    [User returns to the Quasi-Extinction tab.],
    [UI sends `GET /v1/jobs/{job_id}` to check the current status.],
    [System returns job status "completed" with results.],
    [UI renders the quasi-extinction probability curve.],
  ),
)

#scenario(
  name: [Quasi-Extinction Job Fails],
  description: [A server-side error occurs during the Monte Carlo computation, causing the job to transition to the "failed" state.],
  actors: [Registered User],
  trigger: [An unhandled exception occurs inside the background Monte Carlo task.],
  preconditions: [User submitted a quasi-extinction job that is running. An error occurs during computation.],
  postconditions: [Job status is "failed". The error message is stored and displayed to the user. The user can delete the failed job.],
  sequence: (
    [User submits a quasi-extinction job.],
    [System creates the job with status "pending" and starts the background task.],
    [An exception occurs during the Monte Carlo computation.],
    [System catches the exception and updates the job record: `status = "failed"`, `error_message` = exception details.],
    [UI polls `GET /v1/jobs/{job_id}` and receives status "failed".],
    [UI displays an error panel: "Analysis failed. Reason: {error_message}".],
    [UI shows a "Delete Job" button so the user can clear the failed record.],
    [User clicks "Delete Job"; UI sends `DELETE /v1/jobs/{job_id}`.],
    [System removes the job record and returns 204.],
    [UI resets the quasi-extinction form for a new attempt.],
  ),
)

#scenario(
  name: [Configure Custom Stage Thresholds],
  description: [Before submitting a quasi-extinction job, a registered user customises the extinction threshold for individual life stages.],
  actors: [Registered User],
  trigger: [User opens the stage configuration panel and sets a per-stage threshold.],
  preconditions: [User is authenticated. The quasi-extinction form is open with a matrix selected.],
  postconditions: [The custom thresholds are included in the job submission request.],
  sequence: (
    [User opens the Quasi-Extinction section and selects a matrix.],
    [User clicks "Configure Stage Thresholds".],
    [UI displays a threshold input for each stage (Juvenile, Subadult, Adult).],
    [User sets Juvenile threshold to 5 individuals, leaving others at 0.],
    [User clicks "Save Configuration".],
    [UI stores the threshold vector `[5, 0, 0]` in the form state.],
    [User clicks "Run Analysis".],
    [UI sends `POST /v1/jobs/quasi-extinction` with the custom thresholds included in the request body.],
    [System creates the job with the custom configuration and returns 202.],
  ),
)

#scenario(
  name: [Reset Stage Thresholds to Defaults],
  description: [A registered user had set custom thresholds but decides to reset them to the system defaults before running the analysis.],
  actors: [Registered User],
  trigger: [User clicks "Reset to Defaults" in the stage configuration panel.],
  preconditions: [User has previously set custom thresholds and the configuration panel is open.],
  postconditions: [All stage threshold values return to the system default (total population reaching 0). No API call is made by the reset action itself.],
  sequence: (
    [User has custom thresholds set (see @sc:40).],
    [User clicks "Configure Stage Thresholds" again.],
    [UI shows the configuration panel with the previously set values.],
    [User clicks "Reset to Defaults".],
    [UI resets all threshold inputs to 0 (default: extinction = total population = 0).],
    [User clicks "Save Configuration".],
    [UI updates the form state with the default thresholds.],
  ),
)

===== Internationalisation

#scenario(
  name: [Select Application Language],
  description: [A visitor changes the UI language from the default (English) to another available language.],
  actors: [Visitor],
  trigger: [Visitor selects a language from the language selector widget.],
  preconditions: [The application is loaded. The language selector is visible in the navigation area.],
  postconditions: [All UI labels, buttons, and headings re-render in the selected language. The selection is persisted for future visits.],
  sequence: (
    [Visitor locates the language selector in the top navigation bar.],
    [Visitor opens the selector dropdown showing available languages (e.g., English, Spanish).],
    [Visitor clicks "Español".],
    [UI updates the active locale state to Spanish.],
    [All translatable UI strings are replaced with their Spanish equivalents.],
    [The selected language is stored in the browser's local storage.],
    [On the next visit, the UI loads directly in Spanish.],
  ),
)
