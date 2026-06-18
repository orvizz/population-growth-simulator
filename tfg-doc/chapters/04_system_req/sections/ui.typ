// chapters/04_system_req/sections/ui.typ

=== User Interface

The Population Growth Simulator is delivered as a *single-page application* (SPA) running
at #raw("http://localhost:8080"). The interface exposes four top-level sections -
*Browse Matrices*, *Simulate*, *Quasi-Extinction*, and *My Matrices* - accessible via a
persistent navigation header with a dark-green background. Session state (authentication
token and username) is persisted in the browser's #raw("localStorage"), so a page reload
does not require re-login.

*Authentication* is implemented through *modal dialogs* that overlay the current view.
There are no dedicated login or registration pages; the modals open on top of whatever tab
the user is on, allowing their context to be preserved after signing in.

The interface supports six languages selectable from a header dropdown: English, Spanish
(Español), Asturian (Asturianu), Galician (Galego), Basque (Euskara), and Catalan (Català).
The selected language is applied immediately and persisted across sessions.

==== Application Navigation

@tab:ui-nav summarises the navigability trace of the application. Unless noted otherwise,
transitions between main sections are performed by clicking the corresponding header tab.

#figure(
  {
    set text(size: 8pt)
    table(
      columns: (1.4fr, 1.5fr, 1.8fr, auto),
      stroke: 0.5pt + luma(160),
      align: (left + horizon, left + horizon, left + horizon, center + horizon),
      inset: (x: 6pt, y: 5pt),
      table.header(
        table.cell(fill: rgb("#1F4E79"))[#text(fill: white, weight: "bold")[Screen / View]],
        table.cell(fill: rgb("#1F4E79"))[#text(fill: white, weight: "bold")[Entry point]],
        table.cell(fill: rgb("#1F4E79"))[#text(fill: white, weight: "bold")[Exits to]],
        table.cell(fill: rgb("#1F4E79"))[#text(fill: white, weight: "bold")[Auth]],
      ),
      [Browse Matrices],
        [App start (default tab)],
        [Matrix Detail, Log-In modal, Sign-Up modal],
        [No],
      [Matrix Detail],
        [Click any row in Browse results],
        [Browse Matrices (back arrow)],
        [No],
      [Log-In modal],
        ["Log In" button in any tab header],
        [Dismisses in-place; user becomes authenticated],
        [-],
      [Sign-Up modal],
        ["Sign Up" button in any tab header],
        [Dismisses showing success message; then Log-In],
        [-],
      [Simulate - Run view],
        ["Simulate" tab or "New simulation" button],
        [Simulate - Library view (toggle)],
        [No#footnote[Saving a run requires login; running ephemerally does not.]],
      [Simulate - Library view],
        ["Library" toggle or click a saved run],
        [Simulate - Run view (re-run)],
        [Yes],
      [My Matrices],
        ["My Matrices" header tab],
        [Create/edit matrix form, import dialog],
        [Yes],
      [Quasi-Extinction],
        ["Quasi-Extinction" header tab],
        [New analysis form, past analyses],
        [Yes],
    )
  },
  caption: [Application navigability trace],
) <tab:ui-nav>

==== User-Story Traceability

@tab:ui-trace maps each user-facing user story to the UI screen that realises it. Stories
@us:08 (COMPADRE seeding) and @us:23 (CI pipeline) are back-end and infrastructure concerns
with no direct UI representation and are therefore omitted.

#figure(
  {
    set text(size: 8pt)
    table(
      columns: (auto, 1fr),
      stroke: 0.5pt + luma(160),
      align: (left + horizon, left + horizon),
      inset: (x: 6pt, y: 5pt),
      table.header(
        table.cell(fill: rgb("#1F4E79"))[#text(fill: white, weight: "bold")[User Story]],
        table.cell(fill: rgb("#1F4E79"))[#text(fill: white, weight: "bold")[UI Screen]],
      ),
      [@us:01 - Register],          [Sign-Up modal],
      [@us:02 - Log in],            [Log-In modal],
      [@us:03 - Log out],           ["Sign Out" link in account area (visible in all tabs after login)],
      [@us:04 - Browse catalog],    [Browse Matrices tab - results list],
      [@us:05 - Search and filter], [Browse Matrices tab - filter bar (Species, Kingdom, Source)],
      [@us:06 - View details],      [Browse Matrices → Matrix detail panel],
      [@us:07 - Export matrix],     [Browse Matrices → Matrix detail panel - Export JSON / Export CSV],
      [@us:09 - Filter metadata],   [Browse Matrices tab - Kingdom and Source dropdowns],
      [@us:10 - Create matrix],     [My Matrices tab - create matrix form],
      [@us:11 - Edit matrix],       [My Matrices tab - edit form],
      [@us:12 - Delete matrix],     [My Matrices tab - delete action with confirmation],
      [@us:13 - Visibility],        [My Matrices tab - visibility selector (private / shared / public)],
      [@us:14 - Share matrix],      [My Matrices tab - share with users by username],
      [@us:15 - Import matrices],   [My Matrices tab - import from JSON / ZIP file],
      [@us:16 - Deterministic sim.],[Simulate tab - step 2: Deterministic mode selected],
      [@us:17 - Stochastic sim.],   [Simulate tab - step 2: Stochastic mode; step 3: add matrices],
      [@us:18 - Save simulation],   [Simulate tab - "Save as new" button (step 4)],
      [@us:19 - Browse simulations],[Simulate tab - Library view (sidebar list)],
      [@us:20 - Analytics],         [Simulate tab - results panel (dynamics chart + analytics)],
      [@us:21 - QE job],            [Quasi-Extinction tab - new analysis form],
      [@us:22 - Stage config.],     [Quasi-Extinction tab - stage threshold configuration modal],
      [@us:24 - Language],          [Language selector (header dropdown, visible on every tab)],
    )
  },
  caption: [User-story to UI screen traceability],
) <tab:ui-trace>

==== Authentication

Authentication is accessible from any tab via the *"Log In"* and *"Sign Up"* buttons in the
header. The sign-up form (@us:01, @fig:ui-signup-form) collects username, email address, and
a password of at least eight characters. Duplicate usernames or emails produce an inline
error (@fig:ui-signup-fail) without exposing which value conflicts. On success the modal
shows a confirmation message (@fig:ui-signup-ok) and prompts the user to log in.

The log-in form (@us:02, @fig:ui-login-form) accepts username and password. Failed attempts
display a generic red-text error that does not reveal which field is wrong
(@fig:ui-login-fail). After a successful login (@fig:ui-login-ok) the header replaces the
auth buttons with the signed-in username and a *"Sign Out"* link (@us:03).

#grid(
  columns: (1fr, 1fr),
  gutter: 1em,
  [
    #figure(
      image("ui/SGUP-sign_up.png"),
      caption: [Sign-Up modal - empty form (@us:01)],
    ) <fig:ui-signup-form>
  ],
  [
    #figure(
      image("ui/SGUP-sign_up_failed_repeated_user.png"),
      caption: [Sign-Up - duplicate-credential error (@us:01)],
    ) <fig:ui-signup-fail>
  ],
)

#figure(
  image("ui/SGUP-sign_up_successful.png", width: 55%),
  caption: [Sign-Up - account created successfully (@us:01)],
) <fig:ui-signup-ok>

#grid(
  columns: (1fr, 1fr),
  gutter: 1em,
  [
    #figure(
      image("ui/LGIN-log_in.png"),
      caption: [Log-In modal - initial state (@us:02)],
    ) <fig:ui-login-form>
  ],
  [
    #figure(
      image("ui/LGIN-log_in_failed.png"),
      caption: [Log-In - invalid credentials error (@us:02)],
    ) <fig:ui-login-fail>
  ],
)

#figure(
  image("ui/LGIN-log_in_successful.png", width: 100%),
  caption: [Browse Matrices after successful login - username visible in header, Sign Out link available (@us:02, @us:03)],
) <fig:ui-login-ok>

==== Browse Matrices

The Browse Matrices tab (@fig:ui-browse) is the application's default landing view and
requires no authentication (@us:04). It displays a paginated list of population matrices from
the COMPADRE plant database, the COMADRE animal database, and any public custom matrices
created by registered users - 15 783 entries in the default view. Each row shows species
name, taxonomic kingdom, data source, and country of origin.

The filter bar (@us:05, @us:09) provides a free-text species search and two dropdowns:
*Kingdom* and *Source*. When multiple filters are active they combine as AND conditions.
Results update on each filter change.

Clicking any row navigates to the *Matrix detail panel* (@us:06, @fig:ui-detail), which shows:
the projection matrix *A*, survival matrix *U*, and fecundity matrix *F* as grids with stage
names as headers; a *life-cycle network diagram* that renders transitions as an interactive
directed graph with physics simulation; and full species metadata. Two export buttons allow
downloading the matrix as JSON or CSV (@us:07).

#figure(
  image("ui/MB-matrix_browse_not_logged.png", width: 100%),
  caption: [Browse Matrices tab - unauthenticated view with 15 783 results and filter controls (@us:04, @us:05, @us:09)],
) <fig:ui-browse>

#figure(
  image("ui/MB-matrix_detail.png", width: 100%),
  caption: [Matrix detail panel - A/U/F matrix tabs, life-cycle network diagram, and export buttons (@us:06, @us:07)],
) <fig:ui-detail>

==== Simulate

The Simulate tab is the core analytical workspace (@fig:ui-sim-noauth through @fig:ui-saved-2).
Unauthenticated users may run ephemeral (unsaved) simulations; saving results requires login.
The tab offers two views switched by a *Run / Library* toggle.

The *Run view* is built around a four-step sidebar:
+ *Matrix* - species search field and scrollable results list to select the simulation input.
+ *Mode* - radio button for *Deterministic* (one matrix, @us:16) or *Stochastic* (multiple matrices, @us:17).
+ *In Simulation* - list of currently selected matrices; additional matrices can be appended for stochastic runs.
+ *Parameters* - initial population vector (one value per life-history stage), number of time steps (1-1000), optional random seed for reproducibility, and an optional run name (@us:18).

Submitting the form computes the trajectory and renders a population-dynamics line chart (one
line per stage) alongside the ecological analytics panel (@us:20).

The *Library view* lists all saved simulation runs in the sidebar (@us:19). Opening a run
restores the population-dynamics chart and a final-population summary table. A *Re-run with
new parameters* section replays the same matrix with updated inputs.

#figure(
  image("ui/SIM-simulation_not_logged.png", width: 100%),
  caption: [Simulate tab - unauthenticated state showing Run / Library toggle and Import from file option],
) <fig:ui-sim-noauth>

#grid(
  columns: (1fr, 1fr),
  gutter: 1em,
  [
    #figure(
      image("ui/SIM-run_simulation_1.png"),
      caption: [Simulate - steps 1-3: matrix search, stochastic mode, matrix list (@us:16, @us:17)],
    ) <fig:ui-sim-run1>
  ],
  [
    #figure(
      image("ui/SIM-run_simulation_2.png"),
      caption: [Simulate - step 4: initial vector, time steps, seed, and save controls (@us:18)],
    ) <fig:ui-sim-run2>
  ],
)

#grid(
  columns: (1fr, 1fr),
  gutter: 1em,
  [
    #figure(
      image("ui/SIM-simulation_see_saved_1.png"),
      caption: [Library view - saved run with population-dynamics chart and deterministic badge (@us:19, @us:20)],
    ) <fig:ui-saved-1>
  ],
  [
    #figure(
      image("ui/SIM-simulation_see_saved_2.png"),
      caption: [Library view - re-run controls and final-population summary table (@us:19)],
    ) <fig:ui-saved-2>
  ],
)

==== My Matrices

The My Matrices tab (@fig:ui-mym) provides lifecycle management of custom population matrices
and is restricted to authenticated users. Visitors see a login prompt. Once signed in, users
can: create a new matrix by specifying dimension, stage names, and cell values for A, U, and
F (@us:10); edit any matrix they own (@us:11); delete matrices with a confirmation step to
prevent accidental loss (@us:12); set visibility to private, shared, or public (@us:13); share
a matrix with specific users by entering their username (@us:14); and import matrices from a
JSON file or a ZIP archive containing multiple JSON files (@us:15).

#figure(
  image("ui/MYM-my_matrices_not_logged.png", width: 75%),
  caption: [My Matrices tab - unauthenticated state requiring login (@us:10 through @us:15)],
) <fig:ui-mym>

#figure(
  image("ui/MYM-my_matrices_logged.png", width: 100%),
  caption: [My Matrices tab - authenticated view with matrix list and management controls (@us:10 through @us:15)],
) <fig:ui-mym-logged>

#figure(
  image("ui/MYM-my-matrices-stage-configuration.png", width: 75%),
  caption: [My Matrices - stage-name configuration step during matrix creation or editing (@us:10, @us:11)],
) <fig:ui-mym-stages>

==== Quasi-Extinction Analysis

The Quasi-Extinction tab (@fig:ui-qe) provides asynchronous Monte-Carlo probability analysis
and requires authentication. The left sidebar lists past analyses and offers a *New analysis*
button. The main panel presents the configuration form: matrix selection (same multi-matrix
interface as stochastic simulation), initial population vector, extinction threshold, and time
horizon. An optional stage-configuration modal (@us:22) allows setting per-stage minimum
thresholds and excluding specific stages from the extinction check - useful when juvenile
stages naturally fluctuate near zero. Once submitted (@us:21), the job runs in the background
and the user can navigate away; polling updates the status indicator. On completion, the panel
renders the cumulative quasi-extinction probability curve over time.

#figure(
  image("ui/QE-quasi-extinction_not_logged.png", width: 100%),
  caption: [Quasi-Extinction tab - unauthenticated state showing sidebar and main-panel login prompt (@us:21, @us:22)],
) <fig:ui-qe>

#figure(
  image("ui/QE-quasi-extinction-logged-1.png", width: 100%),
  caption: [Quasi-Extinction tab - authenticated state: sidebar with past analyses and "New analysis" button (@us:21)],
) <fig:ui-qe-logged-1>

#grid(
  columns: (1fr, 1fr),
  gutter: 1em,
  [
    #figure(
      image("ui/QE-quasi-extinction-new-analysis.png"),
      caption: [New analysis form - initial configuration (@us:21)],
    ) <fig:ui-qe-form>
  ],
  [
    #figure(
      image("ui/QE-quasi-extinction-matrices-used.png"),
      caption: [New analysis - matrices selected for the run (@us:21)],
    ) <fig:ui-qe-matrices>
  ],
)

#grid(
  columns: (1fr, 1fr),
  gutter: 1em,
  [
    #figure(
      image("ui/QE-quasi-extinction-new-analysis-configure-stages.png"),
      caption: [Stage-threshold configuration modal (@us:22)],
    ) <fig:ui-qe-stages>
  ],
  [
    #figure(
      image("ui/QE-quasei-extinction-new-run-all-configured.png"),
      caption: [Analysis fully configured - ready to submit (@us:21, @us:22)],
    ) <fig:ui-qe-configured>
  ],
)

#grid(
  columns: (1fr, 1fr),
  gutter: 1em,
  [
    #figure(
      image("ui/QE-quasi-extinction-logged-2.png"),
      caption: [Quasi-extinction job in progress (@us:21)],
    ) <fig:ui-qe-logged-2>
  ],
  [
    #figure(
      image("ui/QE-quasi-extinction-logged-3.png"),
      caption: [Quasi-extinction results - probability curve over time (@us:21)],
    ) <fig:ui-qe-logged-3>
  ],
)

==== Language Selection

The language selector (@fig:ui-lang, @us:24) is available in the application header on every
tab. Clicking it opens a dropdown with six options. The choice takes effect immediately across
all labels, buttons, and messages, and is persisted so that the selected language is restored
on the next visit. The six supported locales are: English, Spanish (Español), Asturian
(Asturianu), Galician (Galego), Basque (Euskara), and Catalan (Català), reflecting the
linguistic diversity of the Spanish academic community that forms a key stakeholder group.

#figure(
  image("ui/LANG-language_selector.png", width: 85%),
  caption: [Language selector dropdown - six supported locales available from any tab (@us:24)],
) <fig:ui-lang>

#pagebreak(weak: true)
