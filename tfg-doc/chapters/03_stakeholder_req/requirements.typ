// chapters/03_stakeholder_req/requirements.typ
#import "../../template.typ": req, req-group

=== Functional Requirements

#req-group("SR-F")

#req("Authentication", [
  The system shall provide mechanisms for users to register, access, and leave the
  system securely.
])

#req("User Registration", [
  The system shall allow new users to create an account.
], indent: 1)

#req("Registration Fields", [
  The system shall require a username, an email address, and a password to create an
  account.
], indent: 2)

#req("Username Uniqueness", [
  The system shall reject a registration attempt if the provided username is already
  associated with an existing account.
], indent: 2)

#req("Email Uniqueness", [
  The system shall reject a registration attempt if the provided email address is
  already associated with an existing account.
], indent: 2)

#req("Password Policy", [
  The system shall require a password of at least 8 characters to create an account.
], indent: 2)

#req("Secure Password Storage", [
  The system shall store user passwords in a secure, non-recoverable form. Plain-text
  passwords shall never be persisted.
], indent: 2)

#req("User Login", [
  The system shall allow registered users to authenticate and obtain access to
  protected resources.
], indent: 1)

#req("Login Credentials", [
  The system shall allow users to log in using either their username or their email
  address, combined with their password.
], indent: 2)

#req("Credential Validation", [
  The system shall reject login attempts where the provided credentials do not match
  any registered account.
], indent: 2)

#req("Session Credential", [
  Upon successful login, the system shall issue a session credential to the client for
  use in subsequent authenticated requests.
], indent: 2)

#req("Failed Login Feedback", [
  The system shall return a generic error message on failed login attempts without
  disclosing which credential was incorrect.
], indent: 2)

#req("Session Management", [
  The system shall maintain authenticated user sessions across page interactions.
], indent: 1)

#req("Session Persistence", [
  The system shall preserve the user's authenticated session across page reloads
  without requiring re-authentication.
], indent: 2)

#req("Session Expiry", [
  The system shall automatically expire sessions after a defined period of inactivity.
], indent: 2)

#req("Invalid Session Rejection", [
  The system shall deny access to protected resources when the session credential is
  absent, invalid, or expired.
], indent: 2)

#req("User Logout", [
  The system shall allow authenticated users to terminate their session.
], indent: 1)

#req("Session Termination", [
  Upon logout, the system shall revoke the user's active session so that it cannot be
  reused to access protected resources.
], indent: 2)

#req("Population Matrix Catalog", [
  The system shall provide a publicly accessible catalog of population projection
  matrices sourced from the COMPADRE Plant Matrix Database.
])

#req("Matrix Browsing", [
  The system shall display a list of available population projection matrices to any
  visitor without requiring authentication.
], indent: 1)

#req("Matrix Search and Filtering", [
  The system shall allow visitors to search and filter the matrix catalog by relevant
  attributes such as species name or taxonomic group.
], indent: 1)

#req("Matrix Detail View", [
  The system shall display the full details of a selected matrix, including its
  metadata and numerical values.
], indent: 1)

#req("Matrix Life Cycle Diagram", [
  The system shall display a life cycle diagram alongside the matrix detail view,
  representing life-history stages as nodes and transition values as directed,
  labelled edges.
], indent: 2)

#req("Matrix Management", [
  The system shall allow authenticated users to create, import, export, and manage
  their own population projection matrices.
])

#req("Matrix Creation", [
  The system shall allow an authenticated user to define a new population projection
  matrix by entering its numerical values and descriptive metadata.
], indent: 1)

#req("Matrix Import", [
  The system shall allow an authenticated user to load a population projection matrix
  from a local file.
], indent: 1)

#req("Matrix Export", [
  The system shall allow an authenticated user to download any matrix accessible to
  them as a local file.
], indent: 1)

#req("Matrix Persistence", [
  The system shall allow an authenticated user to save a matrix to their account so
  that it is stored in the application and accessible across sessions.
], indent: 1)

#req("Matrix Editing", [
  The system shall allow an authenticated user to modify the values and metadata of
  matrices they own.
], indent: 1)

#req("Matrix Visibility Control", [
  The system shall allow an authenticated user to set the visibility of any matrix
  they own.
], indent: 1)

#req("Public Visibility", [
  A matrix set to public shall be visible and accessible to all users of the
  application, including unauthenticated visitors.
], indent: 2)

#req("Private Visibility", [
  A matrix set to private shall be visible and accessible only to its owner.
], indent: 2)

#req("Shared Visibility", [
  A matrix set to shared shall be visible and accessible only to its owner and to the
  specific users with whom it has been shared.
], indent: 2)

#req("Matrix Sharing", [
  The system shall allow an authenticated user to share any matrix they own with one
  or more specific registered users.
], indent: 1)

#req("Population Simulation", [
  The system shall allow authenticated users to create, configure, run, manage, and
  export population growth simulations.
])

#req("Simulation Creation", [
  The system shall allow an authenticated user to create a new simulation by selecting
  one or more projection matrices, specifying an initial population vector, and
  choosing the number of time steps to run.
], indent: 1)

#req("Deterministic Simulation", [
  The system shall allow the user to run a deterministic simulation using a single
  projection matrix, computing the population vector at each time step by multiplying
  the current vector by the selected matrix.
], indent: 2)

#req("Stochastic Simulation", [
  The system shall allow the user to run a stochastic simulation by selecting two or
  more projection matrices of matching dimensions and species; at each time step the
  system shall select one of the matrices at random to advance the population vector.
], indent: 2)

#req("Matrix Selection for Simulation", [
  The system shall allow the user to select multiple matrices for a stochastic
  simulation and shall only permit matrices of the same dimensions to be combined in a
  single simulation run.
], indent: 1)

#req("Results Visualization", [
  The system shall display the results of a completed simulation as a chart showing
  the population size per stage across all simulated time steps.
], indent: 1)

#req("Demographic Analysis", [
  The system shall compute and display key demographic metrics derived from the
  projection matrix used in a deterministic simulation, or from a mean matrix when
  working in a stochastic context.
], indent: 1)

#req("Dominant Growth Rate", [
  The system shall compute and display the dominant eigenvalue (λ) of the projection
  matrix, representing the asymptotic per-capita population growth rate.
], indent: 2)

#req("Stable Stage Distribution", [
  The system shall compute and display the stable stage distribution, derived from
  the right eigenvector associated with the dominant eigenvalue, representing the
  proportional composition of each life-history stage at demographic equilibrium.
], indent: 2)

#req("Reproductive Values", [
  The system shall compute and display the reproductive value for each stage, derived
  from the left eigenvector associated with the dominant eigenvalue, representing the
  relative contribution of each stage to future population growth.
], indent: 2)

#req("Sensitivity Analysis", [
  The system shall compute and display the sensitivity matrix, quantifying how an
  absolute change in each matrix element affects the dominant eigenvalue.
], indent: 2)

#req("Elasticity Analysis", [
  The system shall compute and display the elasticity matrix, quantifying the
  proportional contribution of each matrix element to the dominant eigenvalue.
], indent: 2)

#req("Stochastic Analysis", [
  The system shall compute and display additional demographic statistics when the
  user runs a stochastic simulation.
], indent: 1)

#req("Stochastic Population Summary", [
  The system shall display summary statistics of the stage population sizes at the
  final time step across all replicate simulation runs, including the median and
  confidence intervals for each stage.
], indent: 2)

#req("Stochastic Growth Rate", [
  The system shall estimate and display the stochastic population growth rate
  (log λ_s), reporting the theoretical approximation (Tuljapurkar's method), the
  simulated rate, and confidence intervals for the simulated rate.
], indent: 2)

#req("Quasi-Extinction Probability", [
  The system shall compute and display a quasi-extinction probability curve showing
  the cumulative probability that the total population size falls below a
  user-defined threshold at or before each simulated time step, across all replicate
  runs.
], indent: 2)

#req("Simulation Persistence", [
  The system shall allow an authenticated user to save a simulation to their account
  so that its parameters and results are stored in the application.
], indent: 1)

#req("Simulation Modification", [
  The system shall allow an authenticated user to modify the parameters of a saved
  simulation and re-run it.
], indent: 1)

#req("Simulation Export", [
  The system shall allow an authenticated user to download the parameters and results
  of any of their simulations as a local file.
], indent: 1)

#req("Simulation Import", [
  The system shall allow an authenticated user to load a previously exported
  simulation from a local file and restore its parameters and results.
], indent: 1)

#req("Simulation History", [
  The system shall maintain a history of the authenticated user's saved simulations
  and allow them to review and manage past runs.
], indent: 1)

#req("History List", [
  The system shall present the authenticated user with a list of their saved
  simulations.
], indent: 2)

#req("History Detail", [
  The system shall allow the user to view the full parameters and results of any
  saved simulation.
], indent: 2)

#req("Simulation Deletion", [
  The system shall allow the authenticated user to permanently delete any of their
  own saved simulations.
], indent: 2)

=== Non-Functional Requirements

#req-group("SR-NF")

#req("Performance", [
  The system shall respond to any user interaction within 3 seconds under normal load
  conditions (100 concurrent users).
])

#req("Availability", [
  The system shall be available at least 99.5% of the time, measured on a monthly
  basis, excluding scheduled maintenance windows.
])

#req("Security", [
  The system shall restrict access to authenticated-only functionalities to registered
  and logged-in users.
])

#req("Maintainability", [
  The system shall be designed in a modular way so that any individual component can
  be updated or replaced with minimal impact on the rest of the system.
])

#req("Usability", [
  A new user with basic computer skills shall be able to complete the main tasks
  without prior training in less than 5 minutes.
])

#req("Portability", [
  The system shall operate correctly on the following web browsers: Chrome, Firefox, Opera, Safari.
  No client-side installation shall be required beyond a standard web browser.
])

#req("Legal & Regulatory Compliance", [
  The system shall comply with applicable regulations, including GDPR / LOPD-GDD for
  personal data protection, the LPI and the LSSICE.
])
