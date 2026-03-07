# Frontend Design Decisions & Changelog

This file tracks UI/UX decisions and notable changes made to the frontend.
Update it as decisions are made so the documentation chapters can be kept in sync.

---

## [2026-03-07] Auth UI — Profile tab redesign

### Decision
Replace the flat "Account" tab (which showed login + register forms side-by-side always) with a proper auth flow integrated into the navbar.

### Desired behavior
- **Unauthenticated state:** top-right of navbar shows **Log In** and **Sign Up** buttons.
  - **Log In** → navigates to a dedicated login page (`_login` hidden panel).
  - **Sign Up** → navigates to a dedicated register page (`_register` hidden panel).
- **Login page:** username + password fields, "Log In" button, and a link _"Don't have an account yet? Register here"_ that cross-navigates to the register page. On success, redirects to "Browse matrices".
- **Register page:** username + email + password fields, "Sign Up" button, and a link _"Already have an account? Log in here"_. On success, shows a confirmation message with a link to log in.
- **Authenticated state:** Log In and Sign Up buttons are replaced by a single **Sign Out** button. Clicking it clears the token and username, returning the navbar to unauthenticated state.

### Rationale
- Old Account tab was always visible and always showed both forms regardless of auth state — confusing UX.
- Moving auth controls to the navbar top-right is a standard pattern that frees tab space and makes session state immediately visible.
- Using `ui.nav_hidden` + `ui.update_navs` keeps login/register as proper routable pages without cluttering the main nav.

### Implementation notes
- `ui.nav_hidden` does not exist in this version of Shiny for Python — modals (`ui.modal_show` / `ui.modal_remove`) are used instead. This is actually cleaner UX for auth flows.
- `frontend/components/account.py` — `account_server()` handles all auth logic; `_login_modal()` and `_register_modal()` are internal helpers.
- `frontend/app.py` — `page_navbar` has `id="main_nav"`, uses `ui.nav_control(ui.output_ui("navbar_auth_buttons"))` for dynamic top-right buttons.
- The old `account_ui()` function and "Account" nav tab were removed.

### Status
- [x] Done.

---

## [2026-03-07] Simulation project workspace

### Decision
Saved simulations can be "opened" as a project workspace, not just previewed. The library now has two actions per simulation: **Preview** (quick plot in the detail panel) and **Open** (enters the project workspace).

### Project workspace features
- Shows the saved plot and final-population summary on load.
- **Re-run panel:** pre-filled initial vector (from the saved run's first step), editable time steps and random seed (stochastic only). Calls `POST /v1/simulations/run` without saving.
- **Save as new:** saves the current result as a new library entry (`POST /v1/simulations`). No PATCH endpoint exists for simulations so in-place update is not supported.
- **Download JSON** of the current result.
- **Delete** the simulation from inside the workspace (navigates back to library on success).
- **← Library** button returns to the library without losing the list.

### View state machine
```
editor  ←→  library  →  project  →  library
```
`_view` reactive value drives which UI is rendered inside `ui.output_ui("sim_view")`.

### Implementation notes
- New reactive values: `_project_sim` (loaded record), `_project_result` (saved or re-run result).
- `_project_result` starts as the saved simulation so the plot is immediately visible on open.
- Seed input is only rendered for stochastic simulations (Python-side conditional, not `panel_conditional`).
- File: `frontend/components/simulate.py`.

### Status
- [x] Done.

---

<!-- Add new entries at the top, newest first -->
