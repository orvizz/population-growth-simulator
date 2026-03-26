# Testing

The test suite uses **pytest** with FastAPI's built-in `TestClient` for integration tests and **Playwright** (Firefox) for end-to-end tests. Integration tests run against a dedicated PostgreSQL database (`matrix_db_test`) created automatically at the start of each run and dropped at the end. No test data ever touches the production `matrix_db`.

---

## Prerequisites

- PostgreSQL container running: `docker compose up -d db`
- Dev dependencies installed:

```bash
pip install -r requirements-dev.txt
```

For E2E tests, Firefox must be installed via Playwright:

```bash
playwright install firefox
```

---

## Running the tests

### Unit tests only (no DB needed)

```bash
python -m pytest tests/unit/ -v
```

### Integration tests (requires DB)

```bash
python -m pytest tests/ --ignore=tests/e2e -v
```

### E2E tests (mock mode — no DB or running stack needed)

```bash
python -m pytest tests/e2e/ -v
```

E2E tests default to **mock mode**: a lightweight FastAPI mock server starts on port 8001 and the Shiny frontend on port 8082. No real API or database is required.

To run against the real stack (`docker compose up -d` first):

```bash
RUN_MODE=real python -m pytest tests/e2e/ -v
```

### Full suite (unit + integration + e2e)

```bash
python -m pytest tests/ -v
```

### Single file

```bash
python -m pytest tests/test_matrices.py -v
```

### Single test

```bash
python -m pytest tests/test_matrices.py::test_patch_compadre_blocked -v
```

### Stop on first failure

```bash
python -m pytest tests/ -x
```

### With short summary (no verbose)

```bash
python -m pytest tests/
```

The browser used for E2E tests is configured in `pytest.ini` (`--browser firefox`).

---

## Test structure

```
tests/
├── conftest.py              # DB setup, shared fixtures (integration)
├── test_health.py           # /health endpoint
├── test_auth.py             # /v1/auth/register and /v1/auth/login
├── test_matrices.py         # /v1/matrices CRUD and access guards
├── test_simulations.py      # /v1/simulations endpoints
├── test_matrix_visibility.py
├── unit/
│   ├── test_schemas.py          # Pydantic input validation (no DB)
│   ├── test_matrix_service.py   # MatrixService with mocked repo
│   ├── test_auth_service.py     # AuthService with mocked repo
│   └── test_simulation_service.py
└── e2e/
    ├── conftest.py          # Mock API server + Shiny subprocess fixtures
    ├── mock_api.py          # Minimal FastAPI stand-in (canned fixture data)
    ├── test_navigation.py   # Page load and tab switching
    ├── test_auth.py         # Login/logout/register modals
    ├── test_browse.py       # Browse matrices tab
    ├── test_my_matrices.py  # My matrices tab (create flow)
    └── test_simulate.py     # Simulate tab (search, queue, run)
```

### Integration `conftest.py` — how isolation works

| Fixture | Scope | What it does |
|---|---|---|
| `test_database` | session | Creates `matrix_db_test`, builds all tables, drops DB on teardown |
| `client` | function | Truncates all tables, injects test DB into FastAPI DI, returns `TestClient` |
| `alice` | function | Registers a user and returns auth headers |
| `bob` | function | Second user — used to test ownership guards |
| `compadre_matrix_id` | function | Inserts a COMPADRE-style matrix directly (bypasses API) |
| `alice_matrix` | function | Creates a custom matrix owned by alice via the API |

Every test gets a completely empty database. Fixtures compose so a test can declare `(client, alice, compadre_matrix_id)` and get all three without writing any setup code.

### E2E `conftest.py` — how isolation works

| Fixture | Scope | What it does |
|---|---|---|
| `mock_server` | session | Starts the mock FastAPI server on port 8001 (mock mode only) |
| `shiny_proc` | session | Launches the Shiny frontend subprocess on port 8082 |
| `shiny_page` | function | Fresh browser page navigated to the app, waits for ready state |
| `logged_in_page` | function | `shiny_page` with a completed login flow (mock accepts any credentials) |

---

## What is tested

### `test_health.py` (1 test)

| Test | Verifies |
|---|---|
| `test_health` | `GET /health` returns `200 {"status": "ok"}` |

### `test_auth.py` (8 tests)

| Test | Verifies |
|---|---|
| `test_register_success` | 201, returns user fields, password never exposed |
| `test_register_duplicate_username` | 409 with "username" in detail |
| `test_register_duplicate_email` | 409 with "email" in detail |
| `test_register_password_too_short` | 422 from Pydantic validation |
| `test_register_invalid_email` | 422 from Pydantic email validation |
| `test_login_success` | 200, returns `access_token` and `token_type` |
| `test_login_wrong_password` | 401 |
| `test_login_nonexistent_user` | 401 |

### `test_matrices.py` (22 tests)

#### List `GET /v1/matrices`

| Test | Verifies |
|---|---|
| `test_list_empty` | Empty DB returns `[]` |
| `test_list_returns_created_matrix` | Created matrix appears in list |
| `test_list_filter_by_species` | `?species=` partial match works |
| `test_list_filter_by_kingdom` | `?kingdom=` exact match works |
| `test_list_filter_by_source_type` | `?source_type=compadre/custom` separates correctly |
| `test_list_pagination` | `skip` and `limit` work correctly |
| `test_list_no_matrix_data_in_summary` | List response omits `matrix_a`/`matrix_u` (summary only) |

#### Retrieve `GET /v1/matrices/{id}`

| Test | Verifies |
|---|---|
| `test_get_matrix` | 200, full data including `matrix_a` |
| `test_get_matrix_not_found` | 404 for non-existent id |
| `test_get_compadre_matrix` | COMPADRE matrices are publicly readable |
| `test_get_matrix_no_auth_required` | Read is public — no token needed |

#### Create `POST /v1/matrices`

| Test | Verifies |
|---|---|
| `test_create_matrix` | 201, `source_type=custom`, `owner_id` set |
| `test_create_sets_caller_as_owner` | Alice and Bob get different `owner_id` values |
| `test_create_requires_auth` | 401 without token |
| `test_create_requires_matrix_a` | 422 if `matrix_a` missing |
| `test_create_invalid_token` | 401 for malformed token |

#### Update `PATCH /v1/matrices/{id}`

| Test | Verifies |
|---|---|
| `test_patch_matrix` | 200, updated fields reflect new values |
| `test_patch_only_sent_fields_change` | Omitted fields are not nulled out |
| `test_patch_requires_auth` | 401 without token |
| `test_patch_requires_ownership` | Bob gets 403 on Alice's matrix |
| `test_patch_compadre_blocked` | Any user gets 403 with "read-only" in detail |
| `test_patch_not_found` | 404 for non-existent id |

---

## E2E tests (25 tests, Firefox)

E2E tests use Playwright against a Shiny frontend subprocess. By default they run in **mock mode**: the mock API at `tests/e2e/mock_api.py` returns canned fixture data (one COMPADRE matrix, one custom matrix, one simulation result) so tests are fully self-contained and safe to run in CI.

### `test_navigation.py` (2 tests)

| Test | Verifies |
|---|---|
| `test_page_loads` | All three navbar tabs are visible; no Shiny error notifications |
| `test_tab_switching` | Cycling through all tabs produces no errors |

### `test_auth.py` (5 tests)

| Test | Verifies |
|---|---|
| `test_login_modal_opens_and_submits` | Login modal opens; valid credentials replace buttons with avatar |
| `test_login_failure_shows_error` | Username "FAIL" triggers 401; error message shown, modal stays open |
| `test_logout_works` | Avatar dropdown → Sign Out reverts navbar to unauthenticated state |
| `test_register_modal_opens_and_switches` | Sign Up modal opens; "Log in here" link switches to login modal |
| `test_register_success_shows_confirmation` | Valid registration shows "Account created" confirmation |

### `test_browse.py` (8 tests)

| Test | Verifies |
|---|---|
| `test_search_returns_results` | Species search populates result list with mock entry (Abies alba) |
| `test_matrix_detail_loads` | Selecting a result shows species name and metadata |
| `test_browse_detail_shows_stage_names` | Detail panel lists stage names from the matrix record |
| `test_browse_detail_shows_dimension` | Detail panel shows matrix dimension (3×3) |
| `test_browse_detail_shows_matrix_a_section` | Detail panel renders the "Matrix A — projection" section |
| `test_browse_filter_by_kingdom` | Kingdom filter applied before search still returns mock result |
| `test_browse_filter_by_source` | Source=COMPADRE filter still returns mock result |
| `test_browse_detail_shows_compadre_badge` | Detail panel shows the "compadre" source badge |

### `test_my_matrices.py` (4 tests)

| Test | Verifies |
|---|---|
| `test_my_matrices_requires_auth` | Unauthenticated visit shows login prompt |
| `test_my_matrices_shows_create_form_after_login` | After login the Create button is visible |
| `test_my_matrices_add_stage_appears_as_badge` | Adding a stage name renders it as a badge |
| `test_my_matrices_create_matrix` | Full create flow (2 stages → submit) shows "Matrix created." |

### `test_simulate.py` (6 tests)

| Test | Verifies |
|---|---|
| `test_simulate_run_tab_visible` | Simulate tab shows the Run sub-tab |
| `test_simulate_search_populates_list` | Species search populates the matrix selection list |
| `test_simulate_add_matrix_to_queue` | Adding a matrix moves it to the "In simulation" list |
| `test_simulate_run_without_matrix_shows_error` | Run without matrix shows "Add at least one matrix" |
| `test_simulate_run_without_vector_shows_error` | Run without initial vector shows "Enter an initial vector" |
| `test_simulate_full_deterministic_run` | Full happy-path: search → add → fill vector → Run shows "Done" |

---

## Known warnings

- `DeprecationWarning: datetime.datetime.utcnow()` — from SQLAlchemy internals on Python 3.12+. Does not affect results; will be resolved in a future SQLAlchemy release.
- `DeprecationWarning: websockets.legacy` — from the websockets library used by Shiny/uvicorn. Does not affect results.

---

## Troubleshooting

| Problem | Cause | Fix |
|---|---|---|
| `connection refused` | PostgreSQL not running | `docker compose up -d db` |
| `database "matrix_db_test" already exists` | Previous run crashed before teardown | `docker compose exec db psql -U postgres -c "DROP DATABASE matrix_db_test;"` |
| `ModuleNotFoundError: api` | Not running from project root | `cd` to project root before running pytest |
| `ModuleNotFoundError: networkx` | Missing dependency | `pip install networkx` |
| `Service at http://localhost:8082 did not become ready` | Shiny app failed to start | Check for import errors by running `python -m shiny run frontend/app.py --port 8082` manually |
| Tests slow (>60s) | First run builds the test DB or starts Shiny cold | Normal — subsequent runs are faster |
