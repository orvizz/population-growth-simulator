"""Simulate tab — run simulations and manage simulation library."""
import json

from shiny import reactive, render, ui

from .utils import api, render_population_plot


# ---- Static UI helpers (called at module level, not inside server) -----------

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


def simulate_server(input, output, session, *, token, username):

    # ---- Reactive state ---------------------------------------------------
    _available      = reactive.value([])   # matrix summaries from species search
    _in_sim         = reactive.value([])   # matrices added to the current simulation
    _run_result     = reactive.value(None) # ephemeral run result (run tab)
    _lib_cache      = reactive.value([])   # saved simulation summaries
    _lib_selected_sim  = reactive.value(None)  # full record of the selected library simulation
    _lib_rerun_result  = reactive.value(None)  # re-run result inside library tab
    _msg            = reactive.value(None) # (str, is_error: bool)

    # ---- Library helpers --------------------------------------------------

    def _refresh_library():
        t = token()
        if not t:
            _lib_cache.set([])
            return
        try:
            _lib_cache.set(api("GET", "/v1/simulations", token=t))
        except ValueError:
            _lib_cache.set([])

    @reactive.effect
    def _on_auth_change():
        if username():
            _refresh_library()
            ui.update_navs("sim_subtab", selected="📁 Library")
        else:
            ui.update_navs("sim_subtab", selected="▶ Run")
            _lib_cache.set([])
            _lib_selected_sim.set(None)
            _lib_rerun_result.set(None)

    # ---- Library: load selected simulation --------------------------------

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
            _msg.set(None)
            # Pre-fill re-run fields from saved simulation
            history = detail.get("result_history", [])
            if history:
                init_vec = ", ".join(str(v) for v in history[0])
                ui.update_text("lib_init_vec", value=init_vec)
            ui.update_numeric("lib_steps", value=detail.get("n_steps", 20))
        except ValueError as e:
            _msg.set((str(e), True))

    # ---- Library: delete --------------------------------------------------

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
            _msg.set(("Simulation deleted.", False))
            _refresh_library()
        except ValueError as e:
            _msg.set((str(e), True))

    # ---- Library: new simulation button -----------------------------------

    @reactive.effect
    @reactive.event(input.sim_new_btn)
    def _go_run_tab():
        _run_result.set(None)
        _in_sim.set([])
        _msg.set(None)
        ui.update_navs("sim_subtab", selected="▶ Run")

    # ---- Library: re-run --------------------------------------------------

    @reactive.effect
    @reactive.event(input.lib_rerun_btn)
    def _lib_rerun():
        sim = _lib_selected_sim()
        if not sim:
            return

        raw_vec = getattr(input, "lib_init_vec", lambda: "")().strip()
        if not raw_vec:
            _msg.set(("Enter an initial vector.", True))
            return
        try:
            vec = [float(x.strip()) for x in raw_vec.split(",") if x.strip()]
        except ValueError:
            _msg.set(("Invalid vector — use comma-separated numbers.", True))
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
            _msg.set((f"Re-run complete — {result['n_steps']} steps.", False))
        except ValueError as e:
            _msg.set((str(e), True))

    # ---- Library: save as new ---------------------------------------------

    @reactive.effect
    @reactive.event(input.lib_save_btn)
    def _lib_save_new():
        sim = _lib_selected_sim()
        result = _lib_rerun_result()
        if not sim:
            return
        # Use re-run result if available, otherwise use the saved sim data
        effective = result if result else sim
        t = token()
        if not t:
            _msg.set(("Log in to save simulations.", True))
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
            _msg.set((f"Saved as '{saved['name']}'.", False))
            _refresh_library()
        except ValueError as e:
            _msg.set((str(e), True))

    # ---- Library: download ------------------------------------------------

    @output
    @render.download(filename="simulation_saved.json")
    def lib_download():
        result = _lib_rerun_result()
        sim = _lib_selected_sim()
        data = result if result is not None else sim
        yield json.dumps(data if data is not None else {}, indent=2)

    # ---- Library: rendered outputs ----------------------------------------

    @output
    @render.ui
    def sim_saved_select_out():
        sims = _lib_cache()
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

    # ---- Matrix manager (run tab) -----------------------------------------

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

    # ---- Run simulation (run tab) -----------------------------------------

    @reactive.effect
    @reactive.event(input.sim_run_btn)
    def _run_simulation():
        matrices = _in_sim()
        if not matrices:
            _msg.set(("Add at least one matrix to the simulation.", True))
            return

        raw_vec = getattr(input, "sim_init_vec", lambda: "")().strip()
        if not raw_vec:
            _msg.set(("Enter an initial vector.", True))
            return
        try:
            vec = [float(x.strip()) for x in raw_vec.split(",") if x.strip()]
        except ValueError:
            _msg.set(("Invalid vector — use comma-separated numbers.", True))
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
                _msg.set(("Add at least 2 matrices for stochastic mode.", True))
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
            _msg.set((f"Done — {result['n_steps']} steps.", False))
        except ValueError as e:
            _msg.set((str(e), True))

    # ---- Save simulation (run tab) ----------------------------------------

    @reactive.effect
    @reactive.event(input.sim_save_btn)
    def _save_simulation():
        result = _run_result()
        if result is None:
            _msg.set(("Run a simulation first.", True))
            return
        t = token()
        if not t:
            _msg.set(("Log in to save simulations.", True))
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
            _msg.set((f"Saved as '{saved['name']}'.", False))
        except ValueError as e:
            _msg.set((str(e), True))

    # ---- Import / load from file ------------------------------------------

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
                _msg.set((f"Imported: {restored['name']}", False))
                _refresh_library()
            else:
                _run_result.set(data)
                _msg.set(("Simulation loaded from file.", False))
                ui.update_navs("sim_subtab", selected="▶ Run")
        except Exception as e:
            _msg.set((f"Import failed: {e}", True))


    # ---- Downloads (run tab) ----------------------------------------------

    @output
    @render.download(filename="simulation.json")
    def sim_download_run():
        result = _run_result()
        yield json.dumps(result if result is not None else {}, indent=2)

    # ---- UI helpers -------------------------------------------------------

    def _msg_div():
        msg = _msg()
        if not msg:
            return ui.div()
        text, is_err = msg
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

    # ---- Run tab: rendered UI outputs -------------------------------------

    @output
    @render.ui
    def sim_matrix_select_out():
        avail = _available()
        return _matrix_select_widget(avail, "sim_matrix_select")

    @output
    @render.ui
    def sim_in_sim_select_out():
        in_sim = _in_sim()
        return _matrix_select_widget(in_sim, "sim_in_sim_select")

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

