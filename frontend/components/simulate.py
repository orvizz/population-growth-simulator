"""Simulate tab — run simulations and manage simulation library."""
import json

from shiny import reactive, render, ui

from .utils import api, render_population_plot


def simulate_ui():
    return ui.nav_panel(
        "Simulate",
        ui.output_ui("sim_view"),
    )


def simulate_server(input, output, session, *, token, username):

    # ---- Reactive state ---------------------------------------------------
    _view          = reactive.value("editor")   # "library" | "editor" | "project"
    _available     = reactive.value([])          # matrix summaries from species search
    _in_sim        = reactive.value([])          # matrices added to the current simulation
    _run_result    = reactive.value(None)        # ephemeral run result (editor)
    _lib_cache     = reactive.value([])          # saved simulation summaries
    _detail        = reactive.value(None)        # full record shown in library preview
    _project_sim   = reactive.value(None)        # full record of the open project
    _project_result = reactive.value(None)       # current result inside project (saved or re-run)
    _msg           = reactive.value(None)        # (str, is_error: bool)

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
            _view.set("library")
        else:
            _view.set("editor")
            _lib_cache.set([])
            _detail.set(None)
            _project_sim.set(None)
            _project_result.set(None)

    # ---- Library navigation -----------------------------------------------

    @reactive.effect
    @reactive.event(input.sim_new_btn)
    def _go_editor():
        _run_result.set(None)
        _in_sim.set([])
        _msg.set(None)
        _view.set("editor")

    @reactive.effect
    @reactive.event(input.sim_back_btn)
    def _go_library():
        _refresh_library()
        _view.set("library")

    @reactive.effect
    @reactive.event(input.sim_view_btn)
    def _view_detail():
        sid = getattr(input, "sim_lib_select", lambda: None)()
        if not sid:
            return
        try:
            _detail.set(api("GET", f"/v1/simulations/{sid}", token=token()))
            _msg.set(None)
        except ValueError as e:
            _msg.set((str(e), True))

    @reactive.effect
    @reactive.event(input.sim_open_btn)
    def _open_project():
        sid = getattr(input, "sim_lib_select", lambda: None)()
        if not sid:
            return
        try:
            detail = api("GET", f"/v1/simulations/{sid}", token=token())
            _project_sim.set(detail)
            _project_result.set(detail)   # initial result = the saved run
            _msg.set(None)
            _view.set("project")
        except ValueError as e:
            _msg.set((str(e), True))

    @reactive.effect
    @reactive.event(input.sim_delete_btn)
    def _delete_sim():
        sid = getattr(input, "sim_lib_select", lambda: None)()
        if not sid:
            return
        try:
            api("DELETE", f"/v1/simulations/{sid}", token=token())
            _detail.set(None)
            _msg.set(("Simulation deleted.", False))
            _refresh_library()
        except ValueError as e:
            _msg.set((str(e), True))

    # ---- Project: navigation ----------------------------------------------

    @reactive.effect
    @reactive.event(input.proj_back_btn)
    def _project_back():
        _project_sim.set(None)
        _project_result.set(None)
        _refresh_library()
        _view.set("library")

    # ---- Project: delete --------------------------------------------------

    @reactive.effect
    @reactive.event(input.proj_delete_btn)
    def _project_delete():
        sim = _project_sim()
        if not sim:
            return
        try:
            api("DELETE", f"/v1/simulations/{sim['id']}", token=token())
            _project_sim.set(None)
            _project_result.set(None)
            _refresh_library()
            _view.set("library")
        except ValueError as e:
            _msg.set((str(e), True))

    # ---- Project: re-run --------------------------------------------------

    @reactive.effect
    @reactive.event(input.proj_run_btn)
    def _project_rerun():
        sim = _project_sim()
        if not sim:
            return

        raw_vec = getattr(input, "proj_init_vec", lambda: "")().strip()
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
            "n_steps": int(getattr(input, "proj_n_steps", lambda: sim.get("n_steps", 20))()),
        }

        if sim.get("stochastic"):
            body["matrix_ids"] = sim.get("matrix_ids", [])
            seed_val = getattr(input, "proj_seed", lambda: None)()
            if seed_val is not None:
                try:
                    body["random_seed"] = int(seed_val)
                except (TypeError, ValueError):
                    pass
        else:
            body["matrix_id"] = sim.get("matrix_id")

        try:
            result = api("POST", "/v1/simulations/run", json=body)
            _project_result.set(result)
            _msg.set((f"Re-run complete — {result['n_steps']} steps.", False))
        except ValueError as e:
            _msg.set((str(e), True))

    # ---- Project: save as new ---------------------------------------------

    @reactive.effect
    @reactive.event(input.proj_save_new_btn)
    def _project_save_new():
        sim = _project_sim()
        result = _project_result()
        if not sim or not result:
            return
        t = token()
        if not t:
            _msg.set(("Log in to save simulations.", True))
            return

        name = getattr(input, "proj_save_name", lambda: "")().strip() or None
        body: dict = {
            "initial_vector": result.get("result_history", [[]])[0],
            "n_steps": result.get("n_steps", sim.get("n_steps", 20)),
        }
        if name:
            body["name"] = name
        if sim.get("stochastic"):
            body["matrix_ids"] = sim.get("matrix_ids", [])
            seed = result.get("random_seed")
            if seed is not None:
                body["random_seed"] = seed
        else:
            body["matrix_id"] = sim.get("matrix_id")

        try:
            saved = api("POST", "/v1/simulations", token=t, json=body)
            _msg.set((f"Saved as '{saved['name']}'.", False))
        except ValueError as e:
            _msg.set((str(e), True))

    # ---- Matrix manager (editor) ------------------------------------------

    @reactive.effect
    @reactive.event(input.sim_species_btn)
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
        sel = getattr(input, "sim_avail_select", lambda: None)()
        if not sel:
            return
        avail = _available()
        current = _in_sim()
        current_ids = {m["id"] for m in current}
        to_add = [m for m in avail if str(m["id"]) == str(sel) and m["id"] not in current_ids]
        if to_add:
            _in_sim.set(current + to_add)

    @reactive.effect
    @reactive.event(input.sim_rm_btn)
    def _remove_matrix():
        sel = getattr(input, "sim_insim_select", lambda: None)()
        if not sel:
            return
        _in_sim.set([m for m in _in_sim() if str(m["id"]) != str(sel)])

    # ---- Run simulation (editor) ------------------------------------------

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
            "n_steps": int(getattr(input, "sim_n_steps", lambda: 20)()),
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

    # ---- Save simulation (editor) -----------------------------------------

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
                _view.set("editor")
        except Exception as e:
            _msg.set((f"Import failed: {e}", True))

    @reactive.effect
    @reactive.event(input.sim_load_file)
    def _load_file():
        files = input.sim_load_file()
        if not files:
            return
        try:
            with open(files[0]["datapath"], "r") as f:
                data = json.load(f)
            t = token()
            if t:
                restored = api("POST", "/v1/simulations/import", token=t, json=data)
                _msg.set((f"Imported into library: {restored['name']}", False))
                _refresh_library()
            else:
                _run_result.set(data)
                _msg.set(("Simulation loaded from file.", False))
        except Exception as e:
            _msg.set((f"Load failed: {e}", True))

    # ---- Downloads --------------------------------------------------------

    @output
    @render.download(filename="simulation.json")
    def sim_download_run():
        result = _run_result()
        yield json.dumps(result if result is not None else {}, indent=2)

    @output
    @render.download(filename="simulation_saved.json")
    def sim_download_saved():
        detail = _detail()
        yield json.dumps(detail if detail is not None else {}, indent=2)

    @output
    @render.download(filename="simulation_project.json")
    def proj_download():
        result = _project_result()
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

    def _matrix_select(matrices, select_id):
        if not matrices:
            return ui.p("(empty)", class_="text-muted small")
        choices = {
            str(m["id"]): f"{m.get('species_accepted') or '?'} #{m['id']}"
            for m in matrices
        }
        return ui.input_select(select_id, None, choices=choices,
                               size=min(8, len(choices)))

    # ---- Main output ------------------------------------------------------

    @output
    @render.ui
    def sim_view():
        v = _view()
        if v == "project" and username():
            return _project_ui()
        if v == "library" and username():
            return _library_ui()
        return _editor_ui()

    # ---- Library view -----------------------------------------------------

    def _library_ui():
        sims = _lib_cache()
        choices = {str(s["id"]): s.get("name") or f"Sim #{s['id']}" for s in sims}
        detail = _detail()

        return ui.layout_sidebar(
            ui.sidebar(
                ui.h6("Your simulations"),
                ui.input_select("sim_lib_select", None, choices=choices, size=12)
                if choices else ui.p("No saved simulations yet.", class_="text-muted small"),
                ui.input_action_button("sim_open_btn", "Open",
                                       class_="btn-primary btn-sm w-100 mt-2"),
                ui.input_action_button("sim_view_btn", "Preview",
                                       class_="btn-outline-secondary btn-sm w-100 mt-1"),
                ui.input_action_button("sim_delete_btn", "Delete",
                                       class_="btn-outline-danger btn-sm w-100 mt-1"),
                ui.hr(),
                ui.input_action_button("sim_new_btn", "New simulation",
                                       class_="btn-success w-100"),
                ui.hr(),
                ui.h6("Import from file"),
                ui.input_file("sim_import_file", None, accept=[".json"]),
                _msg_div(),
            ),
            ui.card(
                ui.card_header("Preview"),
                _detail_panel(detail) if detail else
                ui.p("Select a simulation and click Preview, or Open to work on it.",
                     class_="text-muted"),
                full_screen=True,
            ),
        )

    def _detail_panel(detail):
        mode = "Stochastic" if detail.get("stochastic") else "Deterministic"
        n_steps = detail.get("n_steps", "?")
        name = detail.get("name") or f"Simulation #{detail.get('id', '?')}"
        return ui.div(
            ui.h5(name),
            ui.tags.small(f"{mode} · {n_steps} steps · ID {detail.get('id')}",
                          class_="text-muted"),
            ui.output_plot("sim_lib_plot", height="300px"),
            ui.download_button("sim_download_saved", "Download JSON",
                                class_="btn-outline-secondary btn-sm mt-2"),
        )

    @output
    @render.plot
    def sim_lib_plot():
        detail = _detail()
        if detail is None:
            return None
        history = detail.get("result_history", [])
        if not history:
            return None
        stage_names = detail.get("stage_names") or [f"Stage {i}" for i in range(len(history[0]))]
        mode = "Stochastic" if detail.get("stochastic") else "Deterministic"
        return render_population_plot(
            history, stage_names,
            title=f"{detail.get('name', 'Simulation')} — {mode}",
        )

    # ---- Project view -----------------------------------------------------

    def _project_ui():
        sim = _project_sim()
        if not sim:
            return ui.p("No simulation loaded.", class_="text-muted")

        mode_label = "Stochastic" if sim.get("stochastic") else "Deterministic"
        name       = sim.get("name") or f"Simulation #{sim.get('id', '?')}"
        n_steps    = sim.get("n_steps", 20)

        # Pre-fill initial vector from the saved run's first step
        history     = sim.get("result_history", [[]])
        init_vec_str = ", ".join(str(v) for v in history[0]) if history and history[0] else ""

        # Matrix badge(s)
        if sim.get("stochastic"):
            mat_ids   = sim.get("matrix_ids", [])
            mat_label = "Matrices: " + ", ".join(f"#{i}" for i in mat_ids)
        else:
            mat_label = f"Matrix: #{sim.get('matrix_id', '?')}"

        seed_input = (
            ui.input_numeric("proj_seed", "Random seed (blank = random)",
                             value=sim.get("random_seed"))
            if sim.get("stochastic") else ui.div()
        )

        sidebar = ui.sidebar(
            ui.input_action_button(
                "proj_back_btn", "← Library",
                class_="btn-outline-secondary btn-sm w-100 mb-3",
            ),
            ui.h6("Simulation info"),
            ui.tags.p(ui.tags.b(mode_label), f" · ID {sim.get('id')}",
                      class_="small mb-1"),
            ui.tags.p(mat_label, class_="small text-muted mb-0"),
            ui.hr(),
            ui.h6("Re-run"),
            ui.input_text("proj_init_vec", "Initial vector",
                          value=init_vec_str, placeholder="e.g. 100, 50, 10"),
            ui.input_numeric("proj_n_steps", "Time steps",
                             value=n_steps, min=1, max=1000),
            seed_input,
            ui.input_action_button("proj_run_btn", "Re-run",
                                   class_="btn-primary w-100 mt-1"),
            _msg_div(),
            ui.hr(),
            ui.h6("Save as new"),
            ui.input_text("proj_save_name", "Name (optional)"),
            ui.input_action_button("proj_save_new_btn", "Save to library",
                                   class_="btn-success w-100 mt-1"),
            ui.hr(),
            ui.download_button("proj_download", "Download JSON",
                                class_="btn-outline-secondary w-100"),
            ui.hr(),
            ui.input_action_button("proj_delete_btn", "Delete simulation",
                                   class_="btn-outline-danger w-100"),
        )

        main = ui.card(
            ui.card_header(
                ui.div(
                    ui.h5(name, class_="mb-0"),
                    ui.tags.small(f"{mode_label} · {n_steps} steps",
                                  class_="text-muted"),
                    class_="d-flex flex-column",
                )
            ),
            ui.output_plot("proj_plot", height="380px"),
            ui.output_ui("proj_summary"),
            full_screen=True,
        )

        return ui.layout_sidebar(sidebar, main)

    @output
    @render.plot
    def proj_plot():
        result = _project_result()
        if result is None:
            return None
        history = result.get("result_history", [])
        if not history:
            return None
        sim = _project_sim()
        stage_names = (
            result.get("stage_names")
            or (sim.get("stage_names") if sim else None)
            or [f"Stage {i}" for i in range(len(history[0]))]
        )
        is_sto = (result if result else sim or {}).get("stochastic", False)
        name   = (sim or {}).get("name", "Simulation")
        return render_population_plot(
            history, stage_names,
            title=f"{name} — {'Stochastic' if is_sto else 'Deterministic'}",
        )

    @output
    @render.ui
    def proj_summary():
        result = _project_result()
        if result is None:
            return None
        history = result.get("result_history", [])
        if not history:
            return None
        sim = _project_sim()
        stage_names = (
            result.get("stage_names")
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
            ui.h6("Final population"),
            ui.tags.table(ui.tags.tbody(*rows), class_="table table-sm mb-2"),
            ui.tags.small(
                f"Total: {total_initial:,.2f} → {total_final:,.2f} (×{growth:.3f})",
                class_="text-muted",
            ),
        )

    # ---- Editor view ------------------------------------------------------

    def _editor_ui():
        avail  = _available()
        in_sim = _in_sim()
        logged = bool(username())

        back_btn = (
            ui.input_action_button("sim_back_btn", "← Library",
                                   class_="btn-outline-secondary btn-sm w-100 mb-2")
            if logged else ui.div()
        )

        save_section = (
            ui.div(
                ui.hr(),
                ui.h6("Save to library"),
                ui.input_text("sim_save_name", "Name (optional)"),
                ui.input_action_button("sim_save_btn", "Save",
                                       class_="btn-success w-100 mt-1"),
            )
            if logged else ui.div()
        )

        params_card = ui.card(
            ui.card_header("Parameters"),
            ui.output_ui("sim_dim_hint"),
            ui.input_text("sim_init_vec", "Initial vector",
                          placeholder="e.g. 100, 50, 10"),
            ui.input_numeric("sim_n_steps", "Time steps", value=20, min=1, max=1000),
            ui.panel_conditional(
                "input.sim_mode === 'sto'",
                ui.input_numeric("sim_seed", "Random seed (blank = random)", value=None),
            ),
            ui.input_action_button("sim_run_btn", "Run simulation",
                                   class_="btn-primary w-100 mt-3"),
            ui.output_ui("sim_msg_ui"),
            save_section,
            ui.hr(),
            ui.download_button("sim_download_run", "Download current run",
                                class_="btn-outline-secondary w-100"),
            ui.hr(),
            ui.h6("Load from file"),
            ui.input_file("sim_load_file", None, accept=[".json"]),
        )

        results_card = ui.card(
            ui.card_header("Results"),
            ui.output_plot("sim_run_plot", height="350px"),
            ui.output_ui("sim_summary"),
            full_screen=True,
        )

        return ui.layout_sidebar(
            ui.sidebar(
                back_btn,
                ui.h6("1. Find matrices"),
                ui.input_text("sim_species", "Species", placeholder="e.g. Abies"),
                ui.input_action_button("sim_species_btn", "Search",
                                       class_="btn-secondary btn-sm w-100 mt-1"),
                ui.hr(),
                ui.h6("2. Mode"),
                ui.input_radio_buttons(
                    "sim_mode", None,
                    choices={"det": "Deterministic (one matrix)",
                             "sto": "Stochastic (multiple)"},
                    selected="det",
                ),
                ui.hr(),
                ui.h6("3. Available matrices"),
                _matrix_select(avail, "sim_avail_select"),
                ui.input_action_button("sim_add_btn", "Add ▼",
                                       class_="btn-outline-secondary btn-sm w-100 mt-1"),
                ui.hr(),
                ui.h6("In simulation"),
                _matrix_select(in_sim, "sim_insim_select"),
                ui.input_action_button("sim_rm_btn", "Remove ▲",
                                       class_="btn-outline-danger btn-sm w-100 mt-1"),
            ),
            ui.layout_columns(params_card, results_card, col_widths=[4, 8]),
        )

    @output
    @render.ui
    def sim_dim_hint():
        in_sim = _in_sim()
        if not in_sim:
            return None
        try:
            m = api("GET", f"/v1/matrices/{in_sim[0]['id']}")
            dim    = len(m["matrix_a"]) if m.get("matrix_a") else "?"
            stages = ", ".join(m["stage_names"]) if m.get("stage_names") else "—"
            return ui.div(
                ui.tags.small(
                    ui.tags.b(f"Dimension: {dim}×{dim}"),
                    ui.tags.br(),
                    f"Stages: {stages}",
                    class_="text-muted",
                ),
                class_="mb-2",
            )
        except Exception:
            return None

    @output
    @render.ui
    def sim_msg_ui():
        return _msg_div()

    @output
    @render.plot
    def sim_run_plot():
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
