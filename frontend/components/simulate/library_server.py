"""Simulate tab — Library sub-tab server logic."""
import json

from shiny import reactive, render, ui

from components.utils import api, plotly_html, render_population_plotly


def library_server(input, output, session, *, token, username, msg,
                   lib_cache, refresh_library, reset_run, tr):
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
            ui.update_navset("sim_subtab", selected="library")
        else:
            ui.update_navset("sim_subtab", selected="run")
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
            msg.set((tr("simulate.simulation_deleted"), False))
            refresh_library()
        except ValueError as e:
            msg.set((str(e), True))

    # ---- New simulation button -------------------------------------------

    @reactive.effect
    @reactive.event(input.sim_new_btn)
    def _go_run_tab():
        reset_run()
        ui.update_navs("sim_subtab", selected="run")

    # ---- Re-run ----------------------------------------------------------

    @reactive.effect
    @reactive.event(input.lib_rerun_btn)
    def _lib_rerun():
        sim = _lib_selected_sim()
        if not sim:
            return

        raw_vec = getattr(input, "lib_init_vec", lambda: "")().strip()
        if not raw_vec:
            msg.set((tr("simulate.enter_vector_error"), True))
            return
        try:
            vec = [float(x.strip()) for x in raw_vec.split(",") if x.strip()]
        except ValueError:
            msg.set((tr("simulate.invalid_vector_error"), True))
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
            msg.set((tr("simulate.rerun_complete", n_steps=result['n_steps']), False))
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
            msg.set((tr("simulate.login_to_save_error"), True))
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
            msg.set((tr("simulate.saved_as", name=saved['name']), False))
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
            return ui.p(tr("simulate.no_saved"), class_="text-muted small")
        choices = {str(s["id"]): s.get("name") or f"Sim #{s['id']}" for s in sims}
        return ui.input_select("sim_saved_select", None, choices=choices,
                               size=min(10, len(choices)))

    @output
    @render.ui
    def lib_sim_header():
        sim = _lib_selected_sim()
        if not sim:
            return ui.tags.span(tr("simulate.select_simulation"),
                                class_="text-muted")
        name = sim.get("name") or f"Simulation #{sim.get('id', '?')}"
        mode = tr("simulate.stochastic") if sim.get("stochastic") else tr("simulate.deterministic")
        badge_class = "badge bg-warning text-dark" if sim.get("stochastic") else "badge bg-info text-dark"
        return ui.div(
            ui.tags.span(name, class_="fw-bold me-2"),
            ui.tags.span(mode, class_=badge_class),
        )

    @output
    @render.ui
    def lib_plot_plotly():
        """Interactive Plotly chart for the library selected simulation."""
        result = _lib_rerun_result()
        sim = _lib_selected_sim()
        data = result if result is not None else sim
        if data is None:
            return ui.div(
                ui.tags.p(tr("simulate.select_sidebar"),
                          class_="text-muted text-center py-4"),
            )
        history = data.get("result_history", [])
        if not history:
            return ui.div()
        stage_names = (
            data.get("stage_names")
            or (sim.get("stage_names") if sim else None)
            or [f"Stage {i}" for i in range(len(history[0]))]
        )
        is_sto = data.get("stochastic", False) or (sim or {}).get("stochastic", False)
        name = (sim or {}).get("name", "Simulation")
        fig = render_population_plotly(
            history, stage_names,
            title=f"{name} — {tr('simulate.stochastic') if is_sto else tr('simulate.deterministic')}",
        )
        fig.update_layout(height=300)
        return ui.HTML(plotly_html(fig))

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
                tr("simulate.total_summary",
                   from_val=f"{total_initial:,.2f}",
                   to_val=f"{total_final:,.2f}",
                   growth=f"{growth:.3f}"),
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
        return ui.input_numeric("lib_seed", tr("simulate.random_seed"),
                                value=sim.get("random_seed"))
