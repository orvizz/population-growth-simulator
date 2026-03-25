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
