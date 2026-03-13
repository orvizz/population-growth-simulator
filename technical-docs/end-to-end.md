# End-to-End Testing

End-to-end tests drive a real browser against the running Shiny frontend,
exercising the full UI flow from tab navigation to login and matrix search.

---

## Technology

| Tool | Role |
|---|---|
| **Playwright for Python** (`pytest-playwright`) | Browser automation — controls Firefox headlessly |
| **pytest** | Test runner — same as unit/integration tests |
| **Minimal FastAPI mock server** | Stands in for the real API in CI; returns canned fixture data |

`pytest-playwright` integrates with pytest via fixtures (`page`, `browser`,
`browser_context`) and runs Chromium headlessly by default. No Node.js
dependency is required.

The mock server is a small FastAPI app defined in `tests/e2e/mock_api.py`.
It is started automatically in a background thread when `RUN_MODE=mock`
(the default). This means E2E tests pass in CI without Docker or a live
database.

---

## Run modes

| `RUN_MODE` | What starts automatically | Requirements |
|---|---|---|
| `mock` *(default)* | Mock API on port 8001 · Shiny on port 8082 | Nothing extra |
| `real` | Shiny on port 8082 | Full stack: `docker compose up -d` + API running on port 8000 |

---

## Prerequisites

### Install dependencies

```bash
pip install -r requirements-dev.txt
```

### Install the Playwright browser

This is a one-time step that downloads Firefox (~110 MB):

```bash
python -m playwright install firefox
```

---

## Running the tests

### All E2E tests (mock mode, default)

```bash
python -m pytest tests/e2e/ -v
```

### Single test file

```bash
python -m pytest tests/e2e/test_browse.py -v
```

### Single test

```bash
python -m pytest tests/e2e/test_auth.py::test_login_modal_opens_and_submits -v
```

### Real-stack mode

```bash
docker compose up -d
RUN_MODE=real python -m pytest tests/e2e/ -v
```

### Headed mode (watch the browser)

```bash
python -m pytest tests/e2e/ -v --headed
```

### Slow motion (useful for debugging)

```bash
python -m pytest tests/e2e/ -v --headed --slowmo=500
```

---

## Excluding E2E from the standard test run

The regular integration test command does not run E2E tests by default.
If you run the full suite without `--ignore`, add it explicitly:

```bash
python -m pytest tests/ --ignore=tests/e2e/ -v
```

---

## Test structure

```
tests/e2e/
├── conftest.py          # Session fixtures: mock server, Shiny subprocess, page
├── mock_api.py          # Minimal FastAPI app returning fixture data
├── test_navigation.py   # Page load, tab switching, error regression
├── test_auth.py         # Login modal, register modal, cross-link
└── test_browse.py       # Search, results list, matrix detail panel
```

---

## What is tested

### `test_navigation.py` (2 tests)

| Test | Verifies |
|---|---|
| `test_page_loads` | All three navbar tabs visible; no Shiny error notifications on load |
| `test_tab_switching` | Cycling Browse → My matrices → Simulate → Browse produces no `shiny-notification-error` (regression guard for "Shared input/output ID") |

### `test_auth.py` (2 tests)

| Test | Verifies |
|---|---|
| `test_login_modal_opens_and_submits` | "Log In" button opens modal; submitting replaces auth buttons with user avatar |
| `test_register_modal_opens_and_switches` | "Sign Up" opens registration modal; "Log in here" switches to login modal |

### `test_browse.py` (2 tests)

| Test | Verifies |
|---|---|
| `test_search_returns_results` | Searching populates the results list with the mock matrix |
| `test_matrix_detail_loads` | Selecting a result renders species metadata in the detail panel |

---

## How the mock server works

`tests/e2e/mock_api.py` is a minimal FastAPI app with one canned fixture:
a single COMPADRE matrix (*Abies alba*, 3×3) and a test user. It responds
to the same paths the real API exposes:

| Endpoint | Mock response |
|---|---|
| `GET /health` | `{"status": "ok"}` |
| `POST /v1/auth/login` | `{"access_token": "mock-token-e2e", "token_type": "bearer"}` |
| `POST /v1/auth/register` | `{"id": 1, "username": "testuser", "email": "test@example.com"}` |
| `GET /v1/matrices` | List with one matrix summary (Abies alba) |
| `GET /v1/matrices/{id}` | Full matrix detail with 3×3 matrices |
| `GET /v1/simulations` | Empty list `[]` |

The mock accepts any credentials for login — it never validates the
username or password. This keeps auth tests fast and deterministic.

In `conftest.py`, the mock server is started in a daemon thread using
`uvicorn.Server`. The Shiny frontend subprocess is launched with
`API_BASE_URL=http://127.0.0.1:8001`, so all `httpx` calls the frontend
makes are handled by the mock instead of the real API.

---

## Ports used by E2E tests

| Service | Port |
|---|---|
| Mock API | 8001 |
| Shiny frontend (under test) | 8082 |

These are separate from the development ports (API: 8000, Shiny: 8080) so
you can run E2E tests alongside a running dev stack without conflicts.

---

## Writing new tests

Every test that needs the browser receives a `shiny_page` fixture — a
`playwright.sync_api.Page` already navigated to the app and ready to use:

```python
from playwright.sync_api import Page, expect

def test_my_feature(shiny_page: Page):
    shiny_page.get_by_role("tab", name="Simulate").click()
    expect(shiny_page.get_by_role("button", name="Run simulation")).to_be_visible()
```

**Key patterns:**

- Use `expect(...).to_be_visible(timeout=5_000)` to wait for Shiny's
  reactive updates to settle.
- Prefer stable Shiny input IDs (`#sim_run_btn`) over fragile CSS selectors.
- Use `locator.select_option(label="...")` for `input_select` widgets.
- Check for the absence of `.shiny-notification-error` as a sanity guard
  at the end of any multi-step flow.

---

## Troubleshooting

| Problem | Cause | Fix |
|---|---|---|
| `playwright install` missing | Browser not downloaded | Run `playwright install chromium` |
| `port 8082 already in use` | Previous test run didn't clean up | Kill leftover Python process: `taskkill /F /IM python.exe` (Windows) or `pkill -f shiny` (Unix) |
| `port 8001 already in use` | Another service on that port | Change `MOCK_API_PORT` in `conftest.py` |
| Tests time out in mock mode | Mock server slow to start | Increase `timeout` in `_wait_for_url` call in `conftest.py` |
| Tests fail in real mode | API/DB not running | `docker compose up -d`, then wait for migrations |
| `ModuleNotFoundError: tests.e2e` | Not running from project root | Run `python -m pytest` from the project root directory |
