# Frontend: Component Decomposition + Path-Based Routing — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Split `simulate.py` and `my_matrices.py` into focused sub-packages, and add path-based routing so each tab is reachable at its own URL (`/matrices`, `/simulate`, `/my-matrices`).

**Architecture:** Component code is moved into sub-packages (`simulate/`, `my_matrices/`) with clear file-per-concern boundaries. Shared reactive state passes through the orchestrator (`server.py`) as function parameters. Routing uses a raw ASGI `SPAMiddleware` that rewrites known paths to `/`, combined with JS `history.pushState` to keep the browser URL in sync with the active tab.

**Tech Stack:** Python Shiny Core, Starlette ASGI, jQuery (bundled with Shiny), httpx

---

## File Map

### New files created

```
frontend/components/simulate/
  __init__.py         re-exports simulate_ui, simulate_server
  ui.py               simulate_ui(), _run_tab_ui(), _library_tab_ui()
  run_server.py       run_server(input, output, session, *, token, username, msg, refresh_library) → reset callable
  library_server.py   library_server(input, output, session, *, token, username, msg, lib_cache, refresh_library, reset_run)
  server.py           simulate_server() — creates shared state, calls run_server then library_server

frontend/components/my_matrices/
  __init__.py         re-exports my_matrices_ui, my_matrices_server
  ui.py               my_matrices_ui()
  create_form.py      create_form_server(input, output, session, *, token, on_created)
  edit_form.py        edit_form_server(input, output, session, *, token, on_modified)
  server.py           my_matrices_server() — creates shared state, composes create + edit, renders mm_view
```

### Files deleted

```
frontend/components/simulate.py
frontend/components/my_matrices.py
```

### Files modified

```
frontend/app.py     SPAMiddleware, routing JS, _apply_initial_route, _push_route
```

### Files unchanged

```
frontend/components/account.py
frontend/components/browse.py
frontend/components/utils.py
```

---

## Key design notes

**`run_server` returns a `reset` callable.** The library tab has a "New simulation" button that clears run-tab state (`_run_result`, `_in_sim`). Since those values live inside `run_server`, it returns a `reset()` callable. `server.py` calls `reset_run = run_server(...)` and passes `reset_run` into `library_server`.

**`_msg_div` is duplicated.** It's a 7-line private closure over the `msg` parameter. Both `run_server` and `library_server` define their own copy — DRY would require an awkward helper factory; duplication is cleaner here.

**`_on_auth_change` lives in `library_server`.** It primarily resets library state (`_lib_cache`, `_lib_selected_sim`, `_lib_rerun_result`) and switches sub-tabs. It is passed `username`, `refresh_library`, and has direct access to the lib-local reactive values.

**`_VIS_BADGE` moves to `edit_form.py`** — it is only used there.

**`/v1/simulations/run` is a pre-existing endpoint call.** Both `run_server._run_simulation` and `library_server._lib_rerun` call `api("POST", "/v1/simulations/run", ...)`. This endpoint is not listed in CLAUDE.md (which only lists `POST /v1/simulations` for run+store). This is carried over verbatim from the original `simulate.py` — do not change it. The smoke-test steps only verify the app starts and the UI renders; clicking "Run simulation" may fail at runtime if the endpoint doesn't exist, but that is a pre-existing issue outside the scope of this refactor.

**Broken intermediate state (Tasks 1–3 and 5–7):** Python resolves `components.simulate` and `components.my_matrices` to the sub-package directory as soon as `__init__.py` is created there — even before the `__init__.py` exports anything. This means `app.py` will fail to import `simulate_ui`/`simulate_server` (or `my_matrices_ui`/`my_matrices_server`) from the stub `__init__.py` between Tasks 1–3 and between Tasks 5–7. **Do not start the full Shiny app between Task 1 Step 1 and Task 4 Step 4, or between Task 5 Step 1 and Task 8 Step 4.** Each task's verification uses targeted import checks that bypass `app.py`.

**Verification strategy:** There is no meaningful unit test for these file moves. Each task's verification is: (1) a Python import check to catch syntax/import errors immediately, and (2) a full app start after the sub-package is complete. The routing task adds `curl` checks.

---

## Task 1 — Create `simulate/ui.py`

**Files:**
- Create: `frontend/components/simulate/__init__.py` (stub)
- Create: `frontend/components/simulate/ui.py`

- [ ] **Step 1: Create the package directory with a stub `__init__.py`**

Create `frontend/components/simulate/__init__.py`:
```python
# Re-exports filled in Task 4 — stub keeps the package importable during construction.
```

- [ ] **Step 2: Create `frontend/components/simulate/ui.py`**

Copy the three UI builder functions verbatim from `simulate.py` (lines 11–111):

```python
"""Simulate tab — UI builders for the Run and Library sub-tabs."""
from shiny import ui


def _run_tab_ui():
    return ui.layout_sidebar(
        ui.sidebar(
            ui.tags.div("1 · Matrix", class_="section-label"),
            ui.input_text("sim_species", None, placeholder="Species name"),
            ui.input_action_button("sim_search_btn", "Search",
                                   class_="btn-secondary btn-sm w-100 mt-1"),
            ui.output_ui("sim_matrix_select_out"),
            ui.tags.div("2 · Mode", class_="section-label mt-3"),
            ui.input_radio_buttons(
                "sim_mode", None,
                choices={"det": "Deterministic", "sto": "Stochastic"},
                selected="det",
            ),
            ui.tags.div("3 · In simulation", class_="section-label mt-3"),
            ui.output_ui("sim_in_sim_select_out"),
            ui.input_action_button("sim_add_btn", "Add ▼",
                                   class_="btn-outline-secondary btn-sm w-100 mt-1"),
            ui.input_action_button("sim_remove_btn", "Remove ▲",
                                   class_="btn-outline-danger btn-sm w-100 mt-1"),
            ui.tags.div("4 · Parameters", class_="section-label mt-3"),
            ui.input_text("sim_init_vec", "Initial vector",
                          placeholder="e.g. 100, 50, 10"),
            ui.input_numeric("sim_steps", "Time steps", value=20, min=1, max=1000),
            ui.panel_conditional(
                "input.sim_mode === 'sto'",
                ui.input_numeric("sim_seed", "Random seed (blank = random)", value=None),
            ),
            ui.input_action_button("sim_run_btn", "Run simulation",
                                   class_="btn btn-primary w-100 mt-2"),
            ui.output_ui("sim_run_msg"),
            ui.output_ui("sim_save_section"),
        ),
        ui.layout_columns(
            ui.card(
                ui.card_header(
                    ui.div(
                        ui.tags.span("Population dynamics"),
                        ui.download_button("sim_download_run", "Export",
                                           class_="btn-outline-secondary btn-sm ms-2"),
                        class_="d-flex align-items-center",
                    )
                ),
                ui.output_plot("sim_plot", height="350px"),
                full_screen=True,
            ),
            ui.card(
                ui.card_header("Final population"),
                ui.output_ui("sim_summary"),
            ),
            col_widths=[8, 4],
        ),
    )


def _library_tab_ui():
    return ui.layout_sidebar(
        ui.sidebar(
            ui.tags.div("Saved simulations", class_="section-label"),
            ui.output_ui("sim_saved_select_out"),
            ui.download_button("lib_download", "Export",
                               class_="btn-outline-secondary btn-sm w-100 mt-1"),
            ui.input_action_button("sim_delete_btn", "Delete",
                                   class_="btn-outline-danger btn-sm w-100 mt-1"),
            ui.hr(),
            ui.input_action_button("sim_new_btn", "New simulation",
                                   class_="btn-primary w-100"),
            ui.hr(),
            ui.h6("Import from file"),
            ui.input_file("sim_import_file", None, accept=[".json"]),
            ui.output_ui("sim_library_msg"),
        ),
        ui.card(
            ui.card_header(ui.output_ui("lib_sim_header")),
            ui.output_plot("lib_plot", height="300px"),
            ui.tags.div("Re-run with new parameters", class_="section-label mt-3"),
            ui.input_text("lib_init_vec", "Initial vector",
                          placeholder="e.g. 100, 50, 10"),
            ui.input_numeric("lib_steps", "Time steps", value=20, min=1, max=1000),
            ui.output_ui("lib_seed_section"),
            ui.input_action_button("lib_rerun_btn", "Re-run",
                                   class_="btn-primary mt-1"),
            ui.input_text("lib_save_name", "Save as name (optional)"),
            ui.input_action_button("lib_save_btn", "Save as new",
                                   class_="btn-success mt-1"),
            ui.output_ui("lib_summary"),
            ui.output_ui("lib_msg"),
            full_screen=True,
        ),
    )


def simulate_ui():
    return ui.nav_panel(
        "Simulate",
        ui.navset_tab(
            ui.nav_panel("▶ Run", _run_tab_ui()),
            ui.nav_panel("📁 Library", _library_tab_ui()),
            id="sim_subtab",
        ),
    )
```

- [ ] **Step 3: Verify import**

```bash
cd "C:\UNI\cuarto curso\tfg\population-growth-simulator\frontend"
python -c "from components.simulate.ui import simulate_ui, _run_tab_ui, _library_tab_ui; print('OK')"
```

Expected: `OK`

- [ ] **Step 4: Commit**

```bash
git add frontend/components/simulate/
git commit -m "feat: add simulate/ sub-package with UI builders"
```

---

## Task 2 — Create `simulate/run_server.py`

**Files:**
- Create: `frontend/components/simulate/run_server.py`

- [ ] **Step 1: Create `frontend/components/simulate/run_server.py`**

```python
"""Simulate tab — Run sub-tab server logic."""
import json

from shiny import reactive, render, ui

from components.utils import api, render_population_plot


def run_server(input, output, session, *, token, username, msg, refresh_library):
    """Register all server-side logic for the Run sub-tab.

    Parameters
    ----------
    msg : reactive.Value[tuple[str, bool] | None]
        Shared message state (text, is_error). Owned by simulate/server.py.
    refresh_library : callable
        Refreshes the library cache. Defined in simulate/server.py.

    Returns
    -------
    reset : callable
        Clears run-tab state. Passed into library_server so the
        "New simulation" button can reset it.
    """
    _available  = reactive.value([])
    _in_sim     = reactive.value([])
    _run_result = reactive.value(None)

    # ---- Private helpers --------------------------------------------------

    def _msg_div():
        m = msg()
        if not m:
            return ui.div()
        text, is_err = m
        return ui.div(
            ui.tags.span(text, class_="text-danger" if is_err else "text-success"),
            class_="small mt-2",
        )

    def _matrix_select_widget(matrices, select_id):
        if not matrices:
            return ui.p("(empty)", class_="text-muted small")
        choices = {
            str(m["id"]): f"{m.get('species_accepted') or '?'} #{m['id']}"
            for m in matrices
        }
        return ui.input_select(select_id, None, choices=choices,
                               size=min(8, len(choices)))

    # ---- Matrix search / add / remove ------------------------------------

    @reactive.effect
    @reactive.event(input.sim_search_btn)
    def _search_matrices():
        params = {"limit": 100}
        species = getattr(input, "sim_species", lambda: "")()
        if species:
            params["species"] = species
        try:
            _available.set(api("GET", "/v1/matrices", params=params))
        except ValueError:
            _available.set([])

    @reactive.effect
    @reactive.event(input.sim_add_btn)
    def _add_matrix():
        sel = getattr(input, "sim_matrix_select", lambda: None)()
        if not sel:
            return
        avail = _available()
        current = _in_sim()
        current_ids = {m["id"] for m in current}
        to_add = [m for m in avail if str(m["id"]) == str(sel) and m["id"] not in current_ids]
        if to_add:
            _in_sim.set(current + to_add)

    @reactive.effect
    @reactive.event(input.sim_remove_btn)
    def _remove_matrix():
        sel = getattr(input, "sim_in_sim_select", lambda: None)()
        if not sel:
            return
        _in_sim.set([m for m in _in_sim() if str(m["id"]) != str(sel)])

    # ---- Run simulation --------------------------------------------------

    @reactive.effect
    @reactive.event(input.sim_run_btn)
    def _run_simulation():
        matrices = _in_sim()
        if not matrices:
            msg.set(("Add at least one matrix to the simulation.", True))
            return

        raw_vec = getattr(input, "sim_init_vec", lambda: "")().strip()
        if not raw_vec:
            msg.set(("Enter an initial vector.", True))
            return
        try:
            vec = [float(x.strip()) for x in raw_vec.split(",") if x.strip()]
        except ValueError:
            msg.set(("Invalid vector — use comma-separated numbers.", True))
            return

        mode = getattr(input, "sim_mode", lambda: "det")()
        body: dict = {
            "initial_vector": vec,
            "n_steps": int(getattr(input, "sim_steps", lambda: 20)()),
        }

        if mode == "det":
            body["matrix_id"] = matrices[0]["id"]
        else:
            if len(matrices) < 2:
                msg.set(("Add at least 2 matrices for stochastic mode.", True))
                return
            body["matrix_ids"] = [m["id"] for m in matrices]
            seed_val = getattr(input, "sim_seed", lambda: None)()
            if seed_val is not None:
                try:
                    body["random_seed"] = int(seed_val)
                except (TypeError, ValueError):
                    pass

        try:
            result = api("POST", "/v1/simulations/run", json=body)
            _run_result.set(result)
            msg.set((f"Done — {result['n_steps']} steps.", False))
        except ValueError as e:
            msg.set((str(e), True))

    # ---- Save simulation -------------------------------------------------

    @reactive.effect
    @reactive.event(input.sim_save_btn)
    def _save_simulation():
        result = _run_result()
        if result is None:
            msg.set(("Run a simulation first.", True))
            return
        t = token()
        if not t:
            msg.set(("Log in to save simulations.", True))
            return

        matrices = _in_sim()
        mode = getattr(input, "sim_mode", lambda: "det")()
        name = getattr(input, "sim_save_name", lambda: "")().strip() or None

        body: dict = {
            "initial_vector": result["initial_vector"],
            "n_steps": result["n_steps"],
        }
        if name:
            body["name"] = name
        if mode == "det":
            body["matrix_id"] = matrices[0]["id"]
        else:
            body["matrix_ids"] = [m["id"] for m in matrices]
            seed_val = getattr(input, "sim_seed", lambda: None)()
            if seed_val is not None:
                try:
                    body["random_seed"] = int(seed_val)
                except (TypeError, ValueError):
                    pass

        try:
            saved = api("POST", "/v1/simulations", token=t, json=body)
            msg.set((f"Saved as '{saved['name']}'.", False))
            refresh_library()
        except ValueError as e:
            msg.set((str(e), True))

    # ---- Import from file ------------------------------------------------

    @reactive.effect
    @reactive.event(input.sim_import_file)
    def _import_file():
        files = input.sim_import_file()
        if not files:
            return
        try:
            with open(files[0]["datapath"], "r") as f:
                data = json.load(f)
            t = token()
            if t:
                restored = api("POST", "/v1/simulations/import", token=t, json=data)
                msg.set((f"Imported: {restored['name']}", False))
                refresh_library()
            else:
                _run_result.set(data)
                msg.set(("Simulation loaded from file.", False))
                ui.update_navs("sim_subtab", selected="▶ Run")
        except Exception as e:
            msg.set((f"Import failed: {e}", True))

    # ---- Download --------------------------------------------------------

    @output
    @render.download(filename="simulation.json")
    def sim_download_run():
        result = _run_result()
        yield json.dumps(result if result is not None else {}, indent=2)

    # ---- Rendered UI outputs ---------------------------------------------

    @output
    @render.ui
    def sim_matrix_select_out():
        return _matrix_select_widget(_available(), "sim_matrix_select")

    @output
    @render.ui
    def sim_in_sim_select_out():
        return _matrix_select_widget(_in_sim(), "sim_in_sim_select")

    @output
    @render.ui
    def sim_run_msg():
        return _msg_div()

    @output
    @render.ui
    def sim_save_section():
        if not username():
            return ui.div()
        return ui.div(
            ui.hr(),
            ui.input_text("sim_save_name", "Name (optional)"),
            ui.input_action_button("sim_save_btn", "Save to library",
                                   class_="btn-success w-100 mt-1"),
        )

    @output
    @render.plot
    def sim_plot():
        result = _run_result()
        if result is None:
            return None
        history = result.get("result_history", [])
        if not history:
            return None
        stage_names = result.get("stage_names") or [f"Stage {i}" for i in range(len(history[0]))]
        mode = "Stochastic" if result.get("stochastic") else "Deterministic"
        return render_population_plot(
            history, stage_names,
            title=f"Population dynamics — {mode} ({result['n_steps']} steps)",
        )

    @output
    @render.ui
    def sim_summary():
        result = _run_result()
        if result is None:
            return None
        history = result.get("result_history", [])
        if not history:
            return None
        stage_names = result.get("stage_names") or [f"Stage {i}" for i in range(len(history[0]))]
        final         = history[-1]
        total_initial = sum(history[0])
        total_final   = sum(final)
        growth        = total_final / total_initial if total_initial else float("nan")

        rows = [
            ui.tags.tr(
                ui.tags.th(sname, class_="text-end pe-3 text-muted small fw-normal",
                           style="width:140px"),
                ui.tags.td(f"{val:,.4f}", class_="small"),
            )
            for sname, val in zip(stage_names, final)
        ]
        return ui.div(
            ui.hr(),
            ui.h6("Final population"),
            ui.tags.table(ui.tags.tbody(*rows), class_="table table-sm mb-2"),
            ui.tags.small(
                f"Total: {total_initial:,.2f} → {total_final:,.2f} (×{growth:.3f})",
                class_="text-muted",
            ),
        )

    # ---- Reset callback (returned to server.py) --------------------------

    def reset():
        """Clear run-tab state. Called by library's 'New simulation' button."""
        _run_result.set(None)
        _in_sim.set([])
        msg.set(None)

    return reset
```

- [ ] **Step 2: Verify import**

```bash
cd "C:\UNI\cuarto curso\tfg\population-growth-simulator\frontend"
python -c "from components.simulate.run_server import run_server; print('OK')"
```

Expected: `OK`

- [ ] **Step 3: Commit**

```bash
git add frontend/components/simulate/run_server.py
git commit -m "feat: add simulate/run_server.py"
```

---

## Task 3 — Create `simulate/library_server.py`

**Files:**
- Create: `frontend/components/simulate/library_server.py`

- [ ] **Step 1: Create `frontend/components/simulate/library_server.py`**

```python
"""Simulate tab — Library sub-tab server logic."""
import json

from shiny import reactive, render, ui

from components.utils import api, render_population_plot


def library_server(input, output, session, *, token, username, msg,
                   lib_cache, refresh_library, reset_run):
    """Register all server-side logic for the Library sub-tab.

    Parameters
    ----------
    msg : reactive.Value[tuple[str, bool] | None]
        Shared message state. Owned by simulate/server.py.
    lib_cache : reactive.Value[list]
        List of saved simulation summaries. Owned by simulate/server.py.
    refresh_library : callable
        Repopulates lib_cache from the API. Defined in simulate/server.py.
    reset_run : callable
        Clears run-tab state. Returned by run_server().
    """
    _lib_selected_sim = reactive.value(None)
    _lib_rerun_result = reactive.value(None)

    # ---- Private helpers --------------------------------------------------

    def _msg_div():
        m = msg()
        if not m:
            return ui.div()
        text, is_err = m
        return ui.div(
            ui.tags.span(text, class_="text-danger" if is_err else "text-success"),
            class_="small mt-2",
        )

    # ---- Auth change: refresh library or clear it ------------------------

    @reactive.effect
    def _on_auth_change():
        if username():
            refresh_library()
            ui.update_navs("sim_subtab", selected="📁 Library")
        else:
            ui.update_navs("sim_subtab", selected="▶ Run")
            lib_cache.set([])
            _lib_selected_sim.set(None)
            _lib_rerun_result.set(None)

    # ---- Load selected simulation ----------------------------------------

    @reactive.effect
    @reactive.event(input.sim_saved_select)
    def _load_lib_selected():
        sid = input.sim_saved_select()
        if not sid:
            return
        try:
            detail = api("GET", f"/v1/simulations/{sid}", token=token())
            _lib_selected_sim.set(detail)
            _lib_rerun_result.set(None)
            msg.set(None)
            history = detail.get("result_history", [])
            if history:
                init_vec = ", ".join(str(v) for v in history[0])
                ui.update_text("lib_init_vec", value=init_vec)
            ui.update_numeric("lib_steps", value=detail.get("n_steps", 20))
        except ValueError as e:
            msg.set((str(e), True))

    # ---- Delete ----------------------------------------------------------

    @reactive.effect
    @reactive.event(input.sim_delete_btn)
    def _delete_sim():
        try:
            sid = input.sim_saved_select()
        except Exception:
            sid = None
        if not sid:
            sim = _lib_selected_sim()
            sid = sim["id"] if sim else None
        if not sid:
            return
        try:
            api("DELETE", f"/v1/simulations/{sid}", token=token())
            _lib_selected_sim.set(None)
            _lib_rerun_result.set(None)
            msg.set(("Simulation deleted.", False))
            refresh_library()
        except ValueError as e:
            msg.set((str(e), True))

    # ---- New simulation button -------------------------------------------

    @reactive.effect
    @reactive.event(input.sim_new_btn)
    def _go_run_tab():
        reset_run()
        ui.update_navs("sim_subtab", selected="▶ Run")

    # ---- Re-run ----------------------------------------------------------

    @reactive.effect
    @reactive.event(input.lib_rerun_btn)
    def _lib_rerun():
        sim = _lib_selected_sim()
        if not sim:
            return

        raw_vec = getattr(input, "lib_init_vec", lambda: "")().strip()
        if not raw_vec:
            msg.set(("Enter an initial vector.", True))
            return
        try:
            vec = [float(x.strip()) for x in raw_vec.split(",") if x.strip()]
        except ValueError:
            msg.set(("Invalid vector — use comma-separated numbers.", True))
            return

        body: dict = {
            "initial_vector": vec,
            "n_steps": int(getattr(input, "lib_steps", lambda: sim.get("n_steps", 20))()),
        }

        if sim.get("stochastic"):
            body["matrix_ids"] = sim.get("matrix_ids", [])
            seed_val = getattr(input, "lib_seed", lambda: None)()
            if seed_val is not None:
                try:
                    body["random_seed"] = int(seed_val)
                except (TypeError, ValueError):
                    pass
        else:
            body["matrix_id"] = sim.get("matrix_id")

        try:
            result = api("POST", "/v1/simulations/run", json=body)
            _lib_rerun_result.set(result)
            msg.set((f"Re-run complete — {result['n_steps']} steps.", False))
        except ValueError as e:
            msg.set((str(e), True))

    # ---- Save as new -----------------------------------------------------

    @reactive.effect
    @reactive.event(input.lib_save_btn)
    def _lib_save_new():
        sim = _lib_selected_sim()
        result = _lib_rerun_result()
        if not sim:
            return
        effective = result if result else sim
        t = token()
        if not t:
            msg.set(("Log in to save simulations.", True))
            return

        name = getattr(input, "lib_save_name", lambda: "")().strip() or None
        body: dict = {
            "initial_vector": effective.get("result_history", [[]])[0],
            "n_steps": effective.get("n_steps", sim.get("n_steps", 20)),
        }
        if name:
            body["name"] = name
        if sim.get("stochastic"):
            body["matrix_ids"] = sim.get("matrix_ids", [])
            seed = effective.get("random_seed")
            if seed is not None:
                body["random_seed"] = seed
        else:
            body["matrix_id"] = sim.get("matrix_id")

        try:
            saved = api("POST", "/v1/simulations", token=t, json=body)
            msg.set((f"Saved as '{saved['name']}'.", False))
            refresh_library()
        except ValueError as e:
            msg.set((str(e), True))

    # ---- Download --------------------------------------------------------

    @output
    @render.download(filename="simulation_saved.json")
    def lib_download():
        result = _lib_rerun_result()
        sim = _lib_selected_sim()
        data = result if result is not None else sim
        yield json.dumps(data if data is not None else {}, indent=2)

    # ---- Rendered outputs ------------------------------------------------

    @output
    @render.ui
    def sim_saved_select_out():
        sims = lib_cache()
        if not sims:
            return ui.p("No saved simulations yet.", class_="text-muted small")
        choices = {str(s["id"]): s.get("name") or f"Sim #{s['id']}" for s in sims}
        return ui.input_select("sim_saved_select", None, choices=choices,
                               size=min(10, len(choices)))

    @output
    @render.ui
    def lib_sim_header():
        sim = _lib_selected_sim()
        if not sim:
            return ui.tags.span("Select a simulation from the library",
                                class_="text-muted")
        name = sim.get("name") or f"Simulation #{sim.get('id', '?')}"
        mode = "Stochastic" if sim.get("stochastic") else "Deterministic"
        badge_class = "badge bg-warning text-dark" if sim.get("stochastic") else "badge bg-info text-dark"
        return ui.div(
            ui.tags.span(name, class_="fw-bold me-2"),
            ui.tags.span(mode, class_=badge_class),
        )

    @output
    @render.plot
    def lib_plot():
        result = _lib_rerun_result()
        sim = _lib_selected_sim()
        data = result if result is not None else sim
        if data is None:
            return None
        history = data.get("result_history", [])
        if not history:
            return None
        stage_names = (
            data.get("stage_names")
            or (sim.get("stage_names") if sim else None)
            or [f"Stage {i}" for i in range(len(history[0]))]
        )
        is_sto = data.get("stochastic", False) or (sim or {}).get("stochastic", False)
        name = (sim or {}).get("name", "Simulation")
        return render_population_plot(
            history, stage_names,
            title=f"{name} — {'Stochastic' if is_sto else 'Deterministic'}",
        )

    @output
    @render.ui
    def lib_summary():
        result = _lib_rerun_result()
        sim = _lib_selected_sim()
        data = result if result is not None else sim
        if data is None:
            return None
        history = data.get("result_history", [])
        if not history:
            return None
        stage_names = (
            data.get("stage_names")
            or (sim.get("stage_names") if sim else None)
            or [f"Stage {i}" for i in range(len(history[0]))]
        )
        final         = history[-1]
        total_initial = sum(history[0])
        total_final   = sum(final)
        growth        = total_final / total_initial if total_initial else float("nan")

        rows = [
            ui.tags.tr(
                ui.tags.th(sname, class_="text-end pe-3 text-muted small fw-normal",
                           style="width:140px"),
                ui.tags.td(f"{val:,.4f}", class_="small"),
            )
            for sname, val in zip(stage_names, final)
        ]
        return ui.div(
            ui.hr(),
            ui.tags.table(ui.tags.tbody(*rows), class_="table table-sm mb-2"),
            ui.tags.small(
                f"Total: {total_initial:,.2f} → {total_final:,.2f} (×{growth:.3f})",
                class_="text-muted",
            ),
        )

    @output
    @render.ui
    def lib_msg():
        return _msg_div()

    @output
    @render.ui
    def sim_library_msg():
        return _msg_div()

    @output
    @render.ui
    def lib_seed_section():
        sim = _lib_selected_sim()
        if not sim or not sim.get("stochastic"):
            return ui.div()
        return ui.input_numeric("lib_seed", "Random seed (blank = random)",
                                value=sim.get("random_seed"))
```

- [ ] **Step 2: Verify import**

```bash
cd "C:\UNI\cuarto curso\tfg\population-growth-simulator\frontend"
python -c "from components.simulate.library_server import library_server; print('OK')"
```

Expected: `OK`

- [ ] **Step 3: Commit**

```bash
git add frontend/components/simulate/library_server.py
git commit -m "feat: add simulate/library_server.py"
```

---

## Task 4 — Wire `simulate/server.py` + `__init__.py`, delete old file

**Files:**
- Create: `frontend/components/simulate/server.py`
- Overwrite: `frontend/components/simulate/__init__.py`
- Delete: `frontend/components/simulate.py`

- [ ] **Step 1: Create `frontend/components/simulate/server.py`**

```python
"""Simulate tab — orchestrator: creates shared state, wires run + library."""
from shiny import reactive

from components.utils import api
from .library_server import library_server
from .run_server import run_server


def simulate_server(input, output, session, *, token, username):
    # ---- Shared state ----------------------------------------------------
    _lib_cache = reactive.value([])
    _msg       = reactive.value(None)

    def _refresh_library():
        t = token()
        if not t:
            _lib_cache.set([])
            return
        try:
            _lib_cache.set(api("GET", "/v1/simulations", token=t))
        except ValueError:
            _lib_cache.set([])

    # ---- Wire sub-servers ------------------------------------------------
    # run_server must be called first — it returns the reset callable that
    # library_server needs for the "New simulation" button.
    reset_run = run_server(
        input, output, session,
        token=token, username=username,
        msg=_msg, refresh_library=_refresh_library,
    )
    library_server(
        input, output, session,
        token=token, username=username,
        msg=_msg, lib_cache=_lib_cache,
        refresh_library=_refresh_library,
        reset_run=reset_run,
    )
```

- [ ] **Step 2: Overwrite `frontend/components/simulate/__init__.py`**

```python
from .server import simulate_server
from .ui import simulate_ui

__all__ = ["simulate_ui", "simulate_server"]
```

- [ ] **Step 3: Verify the package imports correctly**

```bash
cd "C:\UNI\cuarto curso\tfg\population-growth-simulator\frontend"
python -c "from components.simulate import simulate_ui, simulate_server; print('OK')"
```

Expected: `OK`

- [ ] **Step 4: Delete the old monolithic file**

```bash
rm "C:\UNI\cuarto curso\tfg\population-growth-simulator\frontend\components\simulate.py"
```

- [ ] **Step 5: Start the app and verify it loads without errors**

```bash
cd "C:\UNI\cuarto curso\tfg\population-growth-simulator\frontend"
python -m shiny run app.py --port 8080
```

Open `http://localhost:8080` in a browser. The Simulate tab should render and function normally. Stop with Ctrl+C when done.

- [ ] **Step 6: Commit**

```bash
git add frontend/components/simulate/
git rm frontend/components/simulate.py
git commit -m "feat: split simulate.py into simulate/ sub-package"
```

---

## Task 5 — Create `my_matrices/ui.py`

**Files:**
- Create: `frontend/components/my_matrices/__init__.py` (stub)
- Create: `frontend/components/my_matrices/ui.py`

- [ ] **Step 1: Create stub `frontend/components/my_matrices/__init__.py`**

```python
# Re-exports filled in Task 8 — stub keeps the package importable during construction.
```

- [ ] **Step 2: Create `frontend/components/my_matrices/ui.py`**

```python
"""My matrices tab — top-level nav panel UI."""
from shiny import ui


def my_matrices_ui():
    return ui.nav_panel(
        "My matrices",
        ui.output_ui("mm_view"),
    )
```

- [ ] **Step 3: Verify import**

```bash
cd "C:\UNI\cuarto curso\tfg\population-growth-simulator\frontend"
python -c "from components.my_matrices.ui import my_matrices_ui; print('OK')"
```

Expected: `OK`

- [ ] **Step 4: Commit**

```bash
git add frontend/components/my_matrices/
git commit -m "feat: add my_matrices/ sub-package with UI"
```

---

## Task 6 — Create `my_matrices/create_form.py`

**Files:**
- Create: `frontend/components/my_matrices/create_form.py`

- [ ] **Step 1: Create `frontend/components/my_matrices/create_form.py`**

```python
"""My matrices tab — Create form server logic.

Handles stage builder, matrix grid, and the create action.
"""
from shiny import reactive, render, req, ui

from components.utils import api


def create_form_server(input, output, session, *, token, on_created):
    """Register server logic for the Create matrix form.

    Parameters
    ----------
    on_created : callable
        Called after a matrix is successfully created. Triggers
        my_matrices_server to refresh the matrix list.
    """
    _stages     = reactive.value([])
    _create_msg = reactive.value(None)

    # ---- Create action ---------------------------------------------------

    @reactive.effect
    @reactive.event(input.mm_create_btn)
    def _do_create():
        req(token())
        stages = _stages()
        n = len(stages)
        if not stages:
            _create_msg.set("Please add at least one stage.")
            return
        rows = [[float(input[f"mm_cell_{i}_{j}"]() or 0) for j in range(n)] for i in range(n)]

        try:
            api("POST", "/v1/matrices", token=token(), json={
                "species_accepted": getattr(input, "mm_species", lambda: "")() or None,
                "common_name":      getattr(input, "mm_common",  lambda: "")() or None,
                "kingdom":          getattr(input, "mm_kingdom", lambda: "")() or None,
                "country_code":     getattr(input, "mm_country", lambda: "")() or None,
                "matrix_a":         rows,
                "stage_names":      stages,
                "visibility":       "private",
            })
            _create_msg.set("Matrix created.")
            _stages.set([])
            on_created()
        except ValueError as e:
            _create_msg.set(str(e))

    # ---- Stage builder ---------------------------------------------------

    @reactive.effect
    @reactive.event(input.mm_add_stage)
    def _add_stage():
        name = input.mm_new_stage().strip()
        if name and name not in _stages():
            _stages.set(_stages() + [name])
            ui.update_text("mm_new_stage", value="")

    @output
    @render.ui
    def mm_stage_tags():
        stages = _stages()
        if not stages:
            return ui.tags.p("No stages added yet.", class_="text-muted small")
        tags = []
        for i, s in enumerate(stages):
            tags.append(
                ui.tags.span(
                    s,
                    ui.input_action_button(
                        f"mm_remove_stage_{i}", "×",
                        class_="btn btn-sm p-0 ms-1",
                        style="font-size:10px;line-height:1;vertical-align:middle;"
                    ),
                    class_="badge bg-secondary me-1 mb-1",
                    style="font-size:11px;"
                )
            )
        return ui.tags.div(*tags)

    _remove_btn_seen = reactive.value({})

    @reactive.effect
    def _remove_stage():
        stages = _stages()
        seen = dict(_remove_btn_seen())
        changed = False
        remove_idx = None
        for i in range(len(stages)):
            btn_id = f"mm_remove_stage_{i}"
            try:
                count = input[btn_id]()
            except Exception:
                continue
            prev = seen.get(btn_id, 0)
            if count > prev:
                seen[btn_id] = count
                remove_idx = i
                changed = True
                break
        if changed:
            _remove_btn_seen.set(seen)
        if remove_idx is not None:
            _stages.set([s for j, s in enumerate(stages) if j != remove_idx])

    # ---- Matrix grid -----------------------------------------------------

    @output
    @render.ui
    def mm_matrix_grid():
        stages = _stages()
        n = len(stages)
        if n == 0:
            return ui.tags.p("Add stages above to define the matrix dimensions.",
                             class_="text-muted small")
        header_cells = [ui.tags.th("", class_="corner")]
        for s in stages:
            header_cells.append(ui.tags.th(s))
        header = ui.tags.tr(*header_cells)
        rows = []
        for i, row_name in enumerate(stages):
            cells = [ui.tags.th(row_name)]
            for j in range(n):
                cells.append(
                    ui.tags.td(
                        ui.input_numeric(
                            f"mm_cell_{i}_{j}",
                            label=None,
                            value=0,
                            step=0.001,
                            width="72px",
                        )
                    )
                )
            rows.append(ui.tags.tr(*cells))
        return ui.tags.div(
            ui.tags.table(
                ui.tags.thead(header),
                ui.tags.tbody(*rows),
                class_="matrix-grid-input",
            ),
            ui.tags.div(
                "Tab between cells · Enter to confirm",
                class_="text-muted small mt-1",
            ),
        )

    @output
    @render.ui
    def mm_matrix_validation():
        stages = _stages()
        n = len(stages)
        if n == 0:
            return ui.tags.span()
        try:
            for i in range(n):
                for j in range(n):
                    val = input[f"mm_cell_{i}_{j}"]()
                    if val is None:
                        raise ValueError()
            return ui.tags.div(
                f"✓ Valid {n}×{n} matrix",
                style="color:#2d5a27;font-size:11px;font-weight:600;margin-top:4px;"
            )
        except Exception:
            return ui.tags.div(
                "Some cells have invalid values.",
                class_="text-danger small mt-1"
            )

    @output
    @render.ui
    def mm_create_result():
        input.mm_create_btn()
        msg = _create_msg()
        if not msg:
            return None
        color = "success" if "created" in msg.lower() else "danger"
        return ui.div(ui.tags.span(msg, class_=f"text-{color} small"), class_="mt-2")
```

- [ ] **Step 2: Verify import**

```bash
cd "C:\UNI\cuarto curso\tfg\population-growth-simulator\frontend"
python -c "from components.my_matrices.create_form import create_form_server; print('OK')"
```

Expected: `OK`

- [ ] **Step 3: Commit**

```bash
git add frontend/components/my_matrices/create_form.py
git commit -m "feat: add my_matrices/create_form.py"
```

---

## Task 7 — Create `my_matrices/edit_form.py`

**Files:**
- Create: `frontend/components/my_matrices/edit_form.py`

- [ ] **Step 1: Create `frontend/components/my_matrices/edit_form.py`**

```python
"""My matrices tab — Edit form server logic.

Handles metadata editing, visibility, share management, and delete.
"""
from shiny import reactive, render, req, ui

from components.utils import api

_VIS_BADGE = {
    "private": ("Private", "secondary"),
    "shared":  ("Shared",  "primary"),
    "public":  ("Public",  "success"),
}


def edit_form_server(input, output, session, *, token, on_modified):
    """Register server logic for the Edit matrix form.

    Parameters
    ----------
    on_modified : callable
        Called after any mutation (save, delete, visibility change, share change).
        Triggers my_matrices_server to refresh the matrix list and re-render.
    """
    _edit_msg      = reactive.value(None)
    _shares_version = reactive.value(0)

    def _invalidate_shares():
        _shares_version.set(_shares_version() + 1)

    # ---- Save metadata ---------------------------------------------------

    @reactive.effect
    @reactive.event(input.mm_save_btn)
    def _do_save():
        req(token())
        mid = getattr(input, "mm_my_select", lambda: None)()
        req(mid)
        try:
            api("PATCH", f"/v1/matrices/{mid}", token=token(), json={
                "common_name":  getattr(input, "mm_edit_common",   lambda: "")() or None,
                "country_code": getattr(input, "mm_edit_country",  lambda: "")() or None,
            })
            _edit_msg.set("Changes saved.")
            on_modified()
        except ValueError as e:
            _edit_msg.set(str(e))

    # ---- Change visibility -----------------------------------------------

    @reactive.effect
    @reactive.event(input.mm_vis_btn)
    def _do_change_visibility():
        req(token())
        mid = getattr(input, "mm_my_select", lambda: None)()
        req(mid)
        new_vis = getattr(input, "mm_vis_select", lambda: None)()
        if not new_vis:
            return
        try:
            api("PATCH", f"/v1/matrices/{mid}", token=token(), json={"visibility": new_vis})
            _edit_msg.set(f"Visibility set to '{new_vis}'.")
            _invalidate_shares()
        except ValueError as e:
            _edit_msg.set(str(e))

    # ---- Delete ----------------------------------------------------------

    @reactive.effect
    @reactive.event(input.mm_delete_btn)
    def _do_delete():
        req(token())
        mid = getattr(input, "mm_my_select", lambda: None)()
        req(mid)
        try:
            api("DELETE", f"/v1/matrices/{mid}", token=token())
            _edit_msg.set("Matrix deleted.")
            on_modified()
        except ValueError as e:
            _edit_msg.set(str(e))

    # ---- Share management ------------------------------------------------

    @reactive.effect
    @reactive.event(input.mm_share_btn)
    def _do_add_share():
        req(token())
        mid = getattr(input, "mm_my_select", lambda: None)()
        req(mid)
        target = getattr(input, "mm_share_username", lambda: "")().strip()
        if not target:
            _edit_msg.set("Enter a username to share with.")
            return
        try:
            api("POST", f"/v1/matrices/{mid}/shares", token=token(),
                json={"username": target})
            _edit_msg.set(f"Shared with '{target}'.")
            _invalidate_shares()
        except ValueError as e:
            _edit_msg.set(str(e))

    @reactive.effect
    @reactive.event(input.mm_unshare_btn)
    def _do_remove_share():
        req(token())
        mid = getattr(input, "mm_my_select", lambda: None)()
        req(mid)
        sel_uid = getattr(input, "mm_shares_select", lambda: None)()
        if not sel_uid:
            _edit_msg.set("Select a user to remove.")
            return
        try:
            api("DELETE", f"/v1/matrices/{mid}/shares/{sel_uid}", token=token())
            _edit_msg.set("Share removed.")
            _invalidate_shares()
        except ValueError as e:
            _edit_msg.set(str(e))

    # ---- Rendered outputs ------------------------------------------------

    @output
    @render.ui
    def mm_edit_form():
        _shares_version()   # re-render when shares change
        mid = getattr(input, "mm_my_select", lambda: None)()
        if not mid:
            return ui.p("Select a matrix from the list to edit it.", class_="text-muted")
        try:
            m = api("GET", f"/v1/matrices/{mid}", token=token())
        except ValueError as e:
            return ui.p(str(e), class_="text-danger")

        vis = m.get("visibility", "private")
        vis_label, vis_color = _VIS_BADGE.get(vis, ("Unknown", "secondary"))

        shares_section = ui.div()
        if vis == "shared":
            try:
                shares = api("GET", f"/v1/matrices/{mid}/shares", token=token())
            except ValueError:
                shares = []

            share_choices = {str(s["shared_with_user_id"]): s["shared_with_username"]
                             for s in shares}

            shares_section = ui.div(
                ui.hr(),
                ui.h6("Shared with"),
                (
                    ui.div(
                        ui.input_select("mm_shares_select", None,
                                        choices=share_choices,
                                        size=min(5, len(share_choices))),
                        ui.input_action_button("mm_unshare_btn", "Remove selected",
                                               class_="btn-outline-danger btn-sm w-100 mt-1"),
                    )
                    if share_choices
                    else ui.p("No users yet.", class_="text-muted small")
                ),
                ui.hr(),
                ui.h6("Add user"),
                ui.input_text("mm_share_username", None, placeholder="Username"),
                ui.input_action_button("mm_share_btn", "Share",
                                       class_="btn-outline-primary btn-sm w-100 mt-1"),
            )

        return ui.div(
            ui.div(
                ui.p(ui.tags.b("Editing: "), m.get("species_accepted") or f"Matrix #{mid}",
                     class_="mb-1"),
                ui.tags.span(vis_label, class_=f"badge text-bg-{vis_color} mb-3"),
            ),
            ui.input_text("mm_edit_common", "Common name",
                          value=m.get("common_name") or ""),
            ui.input_text("mm_edit_country", "Country code",
                          value=m.get("country_code") or ""),
            ui.input_action_button("mm_save_btn", "Save changes",
                                   class_="btn-warning w-100 mt-2"),
            ui.hr(),
            ui.h6("Visibility"),
            ui.div(
                ui.input_select(
                    "mm_vis_select", None,
                    choices={"private": "Private (only me)",
                             "shared":  "Shared (specific users)",
                             "public":  "Public (everyone)"},
                    selected=vis,
                ),
                ui.input_action_button("mm_vis_btn", "Change",
                                       class_="btn-outline-secondary btn-sm mt-1 w-100"),
            ),
            shares_section,
            ui.hr(),
            ui.input_action_button("mm_delete_btn", "Delete matrix",
                                   class_="btn-outline-danger btn-sm w-100"),
            ui.output_ui("mm_edit_result"),
        )

    @output
    @render.ui
    def mm_edit_result():
        getattr(input, "mm_save_btn",    lambda: None)()
        getattr(input, "mm_delete_btn",  lambda: None)()
        getattr(input, "mm_vis_btn",     lambda: None)()
        getattr(input, "mm_share_btn",   lambda: None)()
        getattr(input, "mm_unshare_btn", lambda: None)()
        msg = _edit_msg()
        if not msg:
            return None
        ok = any(w in msg.lower() for w in ("saved", "deleted", "shared", "set", "removed"))
        return ui.div(ui.tags.span(msg, class_=f"text-{'success' if ok else 'danger'} small"),
                      class_="mt-2")
```

- [ ] **Step 2: Verify import**

```bash
cd "C:\UNI\cuarto curso\tfg\population-growth-simulator\frontend"
python -c "from components.my_matrices.edit_form import edit_form_server; print('OK')"
```

Expected: `OK`

- [ ] **Step 3: Commit**

```bash
git add frontend/components/my_matrices/edit_form.py
git commit -m "feat: add my_matrices/edit_form.py"
```

---

## Task 8 — Wire `my_matrices/server.py` + `__init__.py`, delete old file

**Files:**
- Create: `frontend/components/my_matrices/server.py`
- Overwrite: `frontend/components/my_matrices/__init__.py`
- Delete: `frontend/components/my_matrices.py`

- [ ] **Step 1: Create `frontend/components/my_matrices/server.py`**

```python
"""My matrices tab — orchestrator: shared state, mm_view render, composes create + edit."""
from shiny import reactive, render, ui

from components.utils import api
from .create_form import create_form_server
from .edit_form import edit_form_server


def my_matrices_server(input, output, session, *, token, username):
    # ---- Shared state ----------------------------------------------------
    _version = reactive.value(0)

    def _invalidate():
        _version.set(_version() + 1)

    @reactive.calc
    def _my_matrices():
        _version()
        t = token()
        if not t:
            return []
        try:
            return api("GET", "/v1/matrices", params={"source_type": "custom"}, token=t)
        except ValueError:
            return []

    # ---- Wire sub-servers ------------------------------------------------
    create_form_server(input, output, session, token=token, on_created=_invalidate)
    edit_form_server(input, output, session, token=token, on_modified=_invalidate)

    # ---- Top-level view (login wall or full layout) ----------------------

    @output
    @render.ui
    def mm_view():
        if not username():
            return ui.card(
                ui.card_header("My matrices"),
                ui.p("Please log in to manage your matrices.", class_="text-muted p-3"),
            )

        matrices = _my_matrices()
        choices = {str(m["id"]): (m.get("species_accepted") or f"Matrix #{m['id']}") for m in matrices}

        return ui.layout_sidebar(
            ui.sidebar(
                ui.h6("Your matrices"),
                ui.input_select("mm_my_select", None, choices=choices, size=12)
                if choices else ui.p("No custom matrices yet.", class_="text-muted small"),
            ),
            ui.layout_columns(
                ui.card(
                    ui.card_header("Create matrix"),
                    ui.input_text("mm_species", "Species name"),
                    ui.input_text("mm_common", "Common name (optional)"),
                    ui.input_select(
                        "mm_kingdom", "Kingdom",
                        choices={"": "—", "Plantae": "Plantae", "Animalia": "Animalia",
                                 "Fungi": "Fungi", "Chromista": "Chromista"},
                    ),
                    ui.input_text("mm_country", "Country code", placeholder="ESP"),
                    ui.tags.div("Stages", class_="section-label"),
                    ui.layout_columns(
                        ui.input_text("mm_new_stage", label=None, placeholder="Add stage name..."),
                        ui.input_action_button("mm_add_stage", "+ Add",
                                               class_="btn btn-outline-primary btn-sm"),
                        col_widths=[8, 4],
                    ),
                    ui.output_ui("mm_stage_tags"),
                    ui.tags.div("Matrix A", class_="section-label"),
                    ui.output_ui("mm_matrix_grid"),
                    ui.output_ui("mm_matrix_validation"),
                    ui.input_action_button("mm_create_btn", "Create",
                                           class_="btn-success w-100 mt-2"),
                    ui.output_ui("mm_create_result"),
                ),
                ui.card(
                    ui.card_header("Edit selected matrix"),
                    ui.output_ui("mm_edit_form"),
                ),
                col_widths=[6, 6],
            ),
        )
```

- [ ] **Step 2: Overwrite `frontend/components/my_matrices/__init__.py`**

```python
from .server import my_matrices_server
from .ui import my_matrices_ui

__all__ = ["my_matrices_ui", "my_matrices_server"]
```

- [ ] **Step 3: Verify the package imports correctly**

```bash
cd "C:\UNI\cuarto curso\tfg\population-growth-simulator\frontend"
python -c "from components.my_matrices import my_matrices_ui, my_matrices_server; print('OK')"
```

Expected: `OK`

- [ ] **Step 4: Delete the old monolithic file**

```bash
rm "C:\UNI\cuarto curso\tfg\population-growth-simulator\frontend\components\my_matrices.py"
```

- [ ] **Step 5: Start the app and verify it loads without errors**

```bash
cd "C:\UNI\cuarto curso\tfg\population-growth-simulator\frontend"
python -m shiny run app.py --port 8080
```

Open `http://localhost:8080`. Click through all four tabs — Browse, Simulate, My matrices, and confirm no errors in the terminal. Stop with Ctrl+C.

- [ ] **Step 6: Commit**

```bash
git add frontend/components/my_matrices/
git rm frontend/components/my_matrices.py
git commit -m "feat: split my_matrices.py into my_matrices/ sub-package"
```

---

## Task 9 — Add path-based routing to `app.py`

**Files:**
- Modify: `frontend/app.py`

- [ ] **Step 1: Replace the contents of `frontend/app.py`**

The full new `app.py` — changes from the original are: `SPAMiddleware` class, expanded `_SESSION_JS`, and two new reactive effects in `server()`.

```python
"""
Population Growth Simulator — Shiny frontend entry point.

Run with:
    cd frontend
    python -m shiny run app.py --reload --port 8080
"""
from shiny import App, reactive, ui

from components.account import account_server
from components.browse import browse_server, browse_ui
from components.my_matrices import my_matrices_server, my_matrices_ui
from components.simulate import simulate_server, simulate_ui

# ---- SPA Middleware -------------------------------------------------------
# Rewrites known tab paths to "/" so Shiny always serves from root.
# Uses raw ASGI (not BaseHTTPMiddleware) to avoid breaking WebSocket upgrades.

_ROUTES = {"/", "/matrices", "/simulate", "/my-matrices"}


class SPAMiddleware:
    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        if (scope["type"] == "http"
                and scope.get("method") == "GET"
                and scope.get("path") in _ROUTES):
            scope["path"] = "/"
        await self.app(scope, receive, send)


# ---- Client-side JS -------------------------------------------------------

_SESSION_JS = """
$(document).on('shiny:sessioninitialized', function () {
  // ---- Routing: activate the tab that matches the current URL path ----
  var pathMap = {
    '/matrices':    'Browse matrices',
    '/simulate':    'Simulate',
    '/my-matrices': 'My matrices',
  };
  var tab = pathMap[window.location.pathname];
  if (tab) {
    Shiny.setInputValue('route_path', tab, { priority: 'event' });
  }

  // ---- Session restore: re-hydrate auth token from localStorage --------
  var token    = localStorage.getItem('pgs_auth_token');
  var username = localStorage.getItem('pgs_auth_username');
  if (token && username) {
    Shiny.setInputValue(
      'restored_session',
      { token: token, username: username },
      { priority: 'event' }
    );
  }
});

// ---- URL sync: update the browser URL when the server switches tabs ----
Shiny.addCustomMessageHandler('push_route', function (path) {
  history.pushState(null, '', path);
});

Shiny.addCustomMessageHandler('save_session', function (data) {
  if (data && data.token) {
    localStorage.setItem('pgs_auth_token',    data.token);
    localStorage.setItem('pgs_auth_username', data.username);
  } else {
    localStorage.removeItem('pgs_auth_token');
    localStorage.removeItem('pgs_auth_username');
  }
});
"""

# ---- App UI --------------------------------------------------------------

app_ui = ui.page_navbar(
    browse_ui(),
    my_matrices_ui(),
    simulate_ui(),
    ui.nav_spacer(),
    ui.nav_control(ui.output_ui("navbar_auth_buttons")),
    ui.head_content(
        ui.include_css("static/custom.css"),
        ui.tags.script(ui.HTML(_SESSION_JS)),
    ),
    id="main_nav",
    title="Population Growth Simulator",
    bg="#1a2e1a",
    inverse=True,
)


# ---- Server --------------------------------------------------------------

def server(input, output, session):
    token    = reactive.value(None)
    username = reactive.value(None)

    account_server(input, output, session, token=token, username=username)
    browse_server(input, output, session, token=token)
    my_matrices_server(input, output, session, token=token, username=username)
    simulate_server(input, output, session, token=token, username=username)

    # ---- Routing effects -------------------------------------------------

    @reactive.effect
    @reactive.event(input.route_path)
    def _apply_initial_route():
        """On page load: activate the tab matching the URL path."""
        ui.update_navs("main_nav", selected=input.route_path())

    @reactive.effect
    @reactive.event(input.main_nav)
    async def _push_route():
        """On tab change: push the corresponding path to the browser URL."""
        tab_to_path = {
            "Browse matrices": "/matrices",
            "Simulate":        "/simulate",
            "My matrices":     "/my-matrices",
        }
        path = tab_to_path.get(input.main_nav(), "/")
        await session.send_custom_message("push_route", path)


# ---- ASGI app (wrapped with SPA middleware) ------------------------------

app = App(app_ui, server)
app = SPAMiddleware(app)
```

- [ ] **Step 2: Verify import**

```bash
cd "C:\UNI\cuarto curso\tfg\population-growth-simulator\frontend"
python -c "import app; print('OK')"
```

Expected: `OK`

- [ ] **Step 3: Start the app**

```bash
python -m shiny run app.py --port 8080
```

- [ ] **Step 4: Verify routing with curl (in a second terminal)**

```bash
# Each should return HTTP 200 and HTML containing "Population Growth Simulator"
curl -s http://localhost:8080/matrices   | grep -o "Population Growth Simulator"
curl -s http://localhost:8080/simulate   | grep -o "Population Growth Simulator"
curl -s http://localhost:8080/my-matrices | grep -o "Population Growth Simulator"

# Unknown path — should return a non-200 status or Shiny's 404
curl -I http://localhost:8080/unknown
```

Expected for first three: `Population Growth Simulator`
Expected for `/unknown`: non-200 status code

- [ ] **Step 5: Verify deep-linking in browser**

1. Navigate directly to `http://localhost:8080/simulate` — the Simulate tab should be active on load.
2. Navigate directly to `http://localhost:8080/my-matrices` — the My matrices tab should be active.
3. Click between tabs — the URL bar should update (`/matrices`, `/simulate`, `/my-matrices`).

- [ ] **Step 6: Commit**

```bash
git add frontend/app.py
git commit -m "feat: add path-based routing via SPAMiddleware and JS history.pushState"
```
