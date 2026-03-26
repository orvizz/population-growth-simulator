# Frontend: Component Decomposition + Path-Based Routing

**Date:** 2026-03-18
**Branch:** component-decouple
**Scope:** `frontend/` only — no API, DB, or test changes

---

## Problem

Two component files have grown large and mix multiple concerns:

- `simulate.py` — 657 lines, contains both the Run sub-tab and the Library sub-tab
- `my_matrices.py` — 439 lines, contains both the Create form and the Edit/shares form

The app also has no URL routing. All tabs live at `http://localhost:8080/`; there is no way to deep-link to a specific tab.

---

## Goals

1. Split `simulate.py` and `my_matrices.py` into smaller, focused files.
2. Add path-based routing so each tab has its own URL (`/matrices`, `/simulate`, `/my-matrices`), with full deep-linking support (direct navigation works).

---

## Non-Goals

- No changes to `account.py` (239 lines, already focused) or `browse.py` (125 lines).
- No changes to the API, DB, migrations, or tests.
- No switch to Shiny Express — stays on Shiny Core.

---

## Component Decomposition

### `simulate/`

`simulate.py` is split into a sub-package. The two natural concerns are the Run tab and the Library tab. They share reactive state (`_msg`, `_lib_cache`, `_refresh_library`), which lives in the orchestrating `server.py` and is passed down as parameters.

```
components/simulate/
  __init__.py         # re-exports simulate_ui, simulate_server
  ui.py               # simulate_ui(), _run_tab_ui(), _library_tab_ui()
  run_server.py       # matrix search, add/remove, run, save, download, import
  library_server.py   # load selected, delete, re-run, save-as-new, download
  server.py           # simulate_server() — creates shared state, wires run + library
```

**Reactive state ownership:**

| Reactive value | Owner | Passed to |
|---|---|---|
| `_lib_cache` | `server.py` | `library_server` only |
| `_msg` | `server.py` | both `run_server` and `library_server` |
| `_refresh_library` | `server.py` | both (run calls it after save; library populates it) |
| `_available` | `run_server.py` | local — never shared |
| `_in_sim` | `run_server.py` | local — never shared |
| `_run_result` | `run_server.py` | local — never shared |
| `_lib_selected_sim` | `library_server.py` | local — never shared |
| `_lib_rerun_result` | `library_server.py` | local — never shared |

**Shared state interface** — `server.py` creates the shared reactive values and passes them to `run_server` and `library_server` as keyword arguments:

```python
# server.py (sketch)
def simulate_server(input, output, session, *, token, username):
    _lib_cache     = reactive.value([])
    _msg           = reactive.value(None)

    def _refresh_library():
        t = token()
        if not t:
            _lib_cache.set([])
            return
        try:
            _lib_cache.set(api("GET", "/v1/simulations", token=t))
        except ValueError:
            _lib_cache.set([])

    run_server(input, output, session,
               token=token, username=username,
               msg=_msg, refresh_library=_refresh_library)
    library_server(input, output, session,
                   token=token, username=username,
                   msg=_msg, lib_cache=_lib_cache,
                   refresh_library=_refresh_library)
```

### `my_matrices/`

`my_matrices.py` is split into a sub-package. The two concerns are the Create form (stage builder + matrix grid) and the Edit form (metadata, visibility, share management, delete). They share `_version` and `_my_matrices()`, which live in `server.py`.

```
components/my_matrices/
  __init__.py         # re-exports my_matrices_ui, my_matrices_server
  ui.py               # my_matrices_ui()
  create_form.py      # stage builder outputs, matrix grid, create action server logic
  edit_form.py        # edit metadata, visibility, shares, delete server logic
  server.py           # my_matrices_server() — composes both, holds shared state
```

### Unchanged files

```
components/account.py   # unchanged
components/browse.py    # unchanged
components/utils.py     # unchanged
```

### Public surface

`app.py` imports remain identical:

```python
from components.simulate import simulate_ui, simulate_server
from components.my_matrices import my_matrices_ui, my_matrices_server
```

---

## Path-Based Routing

### Route map

| URL path       | Tab label       | Shiny nav ID        |
|----------------|-----------------|---------------------|
| `/`            | Browse matrices | `"Browse matrices"` |
| `/matrices`    | Browse matrices | `"Browse matrices"` |
| `/simulate`    | Simulate        | `"Simulate"`        |
| `/my-matrices` | My matrices     | `"My matrices"`     |

### Server side — `SPAMiddleware`

A raw ASGI middleware class added in `app.py`. On every incoming HTTP GET request it checks whether the path matches a known route. If so, it rewrites `scope["path"]` to `"/"` before forwarding to Shiny. Shiny sees only `/` and serves normally.

**Important:** `BaseHTTPMiddleware` must NOT be used here — it cannot forward WebSocket connections through `call_next`, which would break Shiny's entire reactive engine (Shiny runs over WebSocket at `/_shiny/session/{id}/websocket`). Instead, a raw ASGI middleware checks `scope["type"]` and passes WebSocket scopes straight through without any rewriting.

```python
_ROUTES = {"/", "/matrices", "/simulate", "/my-matrices"}

class SPAMiddleware:
    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        if scope["type"] == "http" and scope.get("method") == "GET" \
                and scope.get("path") in _ROUTES:
            scope["path"] = "/"
        await self.app(scope, receive, send)

app = App(app_ui, server)
app = SPAMiddleware(app)
```

### Client side — JavaScript

Two additions to `_SESSION_JS` in `app.py`:

**1. Initial path → active tab (on page load)**

Reads `window.location.pathname`, maps it to a tab label, and sets `input.route_path`:

```javascript
$(document).on('shiny:sessioninitialized', function () {
  var pathMap = {
    '/matrices':    'Browse matrices',
    '/simulate':    'Simulate',
    '/my-matrices': 'My matrices',
  };
  var tab = pathMap[window.location.pathname];
  if (tab) {
    Shiny.setInputValue('route_path', tab, { priority: 'event' });
  }
  // ... existing session restore logic ...
});
```

**2. Server → URL sync (on tab change)**

A custom message handler that calls `history.pushState` when the server sends a route update:

```javascript
Shiny.addCustomMessageHandler('push_route', function(path) {
  history.pushState(null, '', path);
});
```

### Server side — `server()` in `app.py`

Two additions to the main `server` function:

**1. Activate tab on initial load**

```python
@reactive.effect
@reactive.event(input.route_path)
def _apply_initial_route():
    ui.update_navs("main_nav", selected=input.route_path())
```

**2. Push route on tab change**

```python
@reactive.effect
@reactive.event(input.main_nav)
async def _push_route():
    tab_to_path = {
        "Browse matrices": "/matrices",
        "Simulate":        "/simulate",
        "My matrices":     "/my-matrices",
    }
    path = tab_to_path.get(input.main_nav(), "/")
    await session.send_custom_message("push_route", path)
```

---

## Edge Cases

| Scenario | Behaviour |
|---|---|
| Unknown path (e.g. `/foo`) | `SPAMiddleware` does not rewrite; Shiny returns its default 404 |
| JS blocked / slow | `route_path` never fires; app loads on default tab (`Browse matrices`) — graceful degradation |
| Tab-initiated `update_navs` (e.g. login → library) | Existing component calls stay unchanged; `_push_route` effect fires automatically because `input.main_nav` changes |
| `_apply_initial_route` triggers `_push_route` | When the server switches tabs on load via `update_navs`, `input.main_nav` changes and `_push_route` fires — it pushes the same path JS already set. Redundant but harmless. |
| Direct navigation to `/` | No `pathMap` match; no `setInputValue` call; default tab loads |

---

## Testing

No new test files. Verify manually:

```bash
# Should return 200 and serve the Shiny app HTML
curl -I http://localhost:8080/matrices
curl -I http://localhost:8080/simulate
curl -I http://localhost:8080/my-matrices

# Should still return 404
curl -I http://localhost:8080/unknown
```

Existing E2E Playwright tests can be extended to navigate directly to `/simulate` and assert the correct tab is active.

---

## File Change Summary

| File | Change |
|---|---|
| `frontend/app.py` | Add `SPAMiddleware`, routing JS, `_apply_initial_route`, `_push_route` |
| `frontend/components/simulate.py` | Delete — replaced by `simulate/` sub-package |
| `frontend/components/simulate/__init__.py` | New — re-exports |
| `frontend/components/simulate/ui.py` | New — UI builders |
| `frontend/components/simulate/run_server.py` | New — run tab server |
| `frontend/components/simulate/library_server.py` | New — library tab server |
| `frontend/components/simulate/server.py` | New — orchestrator |
| `frontend/components/my_matrices.py` | Delete — replaced by `my_matrices/` sub-package |
| `frontend/components/my_matrices/__init__.py` | New — re-exports |
| `frontend/components/my_matrices/ui.py` | New — `my_matrices_ui()` |
| `frontend/components/my_matrices/create_form.py` | New — create form server |
| `frontend/components/my_matrices/edit_form.py` | New — edit form server |
| `frontend/components/my_matrices/server.py` | New — orchestrator |
| `frontend/components/account.py` | Unchanged |
| `frontend/components/browse.py` | Unchanged |
| `frontend/components/utils.py` | Unchanged |
