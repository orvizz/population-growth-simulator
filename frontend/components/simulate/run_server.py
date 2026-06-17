"""Simulate tab — Run sub-tab server logic."""
import json
import math

from shiny import reactive, render, ui

from components.utils import api, plotly_html, render_population_plotly
from components.shared import matrix_display


def run_server(input, output, session, *, token, username, msg, refresh_library, tr):
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
    _prev_mode  = reactive.value("det")

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
            return ui.p(tr("simulate.empty"), class_="text-muted small")
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
        mode = getattr(input, "sim_mode", lambda: "det")()
        if mode == "det" and len(current) >= 1:
            msg.set((tr("simulate.det_one_matrix_only"), True))
            return
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

    # ---- Mode change guard -----------------------------------------------

    @reactive.effect
    @reactive.event(input.sim_mode)
    def _on_mode_change():
        new_mode = input.sim_mode()
        prev = _prev_mode()
        matrices = _in_sim()

        if new_mode == "det" and prev == "sto" and len(matrices) >= 2:
            modal = ui.modal(
                ui.p(tr("simulate.det_mode_warning_body", n=len(matrices))),
                title=tr("simulate.det_mode_warning_title"),
                easy_close=False,
                footer=ui.div(
                    ui.input_action_button(
                        "sim_det_cancel_btn",
                        tr("simulate.det_mode_cancel_btn"),
                        class_="btn-secondary me-2",
                    ),
                    ui.input_action_button(
                        "sim_det_keep_btn",
                        tr("simulate.det_mode_keep_first_btn"),
                        class_="btn-warning me-2",
                    ),
                    ui.input_action_button(
                        "sim_det_clear_btn",
                        tr("simulate.det_mode_clear_btn"),
                        class_="btn-danger",
                    ),
                ),
            )
            ui.modal_show(modal)
        else:
            _prev_mode.set(new_mode)

    @reactive.effect
    @reactive.event(input.sim_det_cancel_btn)
    def _det_cancel():
        ui.modal_remove()
        ui.update_radio_buttons("sim_mode", selected="sto")

    @reactive.effect
    @reactive.event(input.sim_det_keep_btn)
    def _det_keep_first():
        ui.modal_remove()
        _in_sim.set(_in_sim()[:1])
        _prev_mode.set("det")

    @reactive.effect
    @reactive.event(input.sim_det_clear_btn)
    def _det_clear():
        ui.modal_remove()
        _in_sim.set([])
        _prev_mode.set("det")

    # ---- Run simulation --------------------------------------------------

    @reactive.effect
    @reactive.event(input.sim_run_btn)
    def _run_simulation():
        matrices = _in_sim()
        if not matrices:
            msg.set((tr("simulate.add_matrix_error"), True))
            return

        raw_vec = getattr(input, "sim_init_vec", lambda: "")().strip()
        if not raw_vec:
            msg.set((tr("simulate.enter_vector_error"), True))
            return
        try:
            vec = [float(x.strip()) for x in raw_vec.split(",") if x.strip()]
        except ValueError:
            msg.set((tr("simulate.invalid_vector_error"), True))
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
                msg.set((tr("simulate.add_two_matrices_error"), True))
                return
            body["matrix_ids"] = [m["id"] for m in matrices]
            n_runs_val = getattr(input, "sim_n_runs", lambda: 100)()
            try:
                body["n_runs"] = int(n_runs_val) if n_runs_val is not None else 100
            except (TypeError, ValueError):
                body["n_runs"] = 100
            seed_val = getattr(input, "sim_seed", lambda: None)()
            if seed_val is not None:
                try:
                    body["random_seed"] = int(seed_val)
                except (TypeError, ValueError):
                    pass

        try:
            result = api("POST", "/v1/simulations/run", json=body)
            _run_result.set(result)
            msg.set((tr("simulate.done_steps", n_steps=result['n_steps']), False))
        except ValueError as e:
            msg.set((str(e), True))

    # ---- Save simulation -------------------------------------------------

    @reactive.effect
    @reactive.event(input.sim_save_btn)
    def _save_simulation():
        result = _run_result()
        if result is None:
            msg.set((tr("simulate.run_first_error"), True))
            return
        t = token()
        if not t:
            msg.set((tr("simulate.login_to_save_error"), True))
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
            msg.set((tr("simulate.saved_as", name=saved['name']), False))
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
                msg.set((tr("simulate.imported", name=restored['name']), False))
                refresh_library()
            else:
                _run_result.set(data)
                msg.set((tr("simulate.loaded_from_file"), False))
                ui.update_navs("sim_subtab", selected="run")
        except Exception as e:
            msg.set((tr("simulate.import_failed", error=str(e)), True))

    # ---- Download --------------------------------------------------------

    @output
    @render.download(filename="simulation.json")
    def sim_download_run():
        result = _run_result()
        yield json.dumps(result if result is not None else {}, indent=2)

    # ---- Data table modal ------------------------------------------------

    @reactive.effect
    @reactive.event(input.sim_show_table_btn)
    def _show_data_table():
        result = _run_result()
        if result is None:
            return
        history = result.get("result_history", [])
        if not history:
            return
        n_stages = len(history[0])
        stage_names = result.get("stage_names") or [
            tr("simulate.stage_count", n=i + 1) for i in range(n_stages)
        ]
        is_stoch = result.get("stochastic", False)
        min_h = result.get("result_min_history") if is_stoch else None
        max_h = result.get("result_max_history") if is_stoch else None
        var_h = result.get("result_variance") if is_stoch else None
        modal = ui.modal(
            _build_trajectory_table(history, stage_names, min_h, max_h, var_h, tr),
            title=tr("simulate.data_table_title"),
            easy_close=True,
            size="xl",
            footer=ui.modal_button(tr("simulate.close_btn")),
        )
        ui.modal_show(modal)

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
            ui.input_text("sim_save_name", tr("simulate.save_as_name")),
            ui.input_action_button("sim_save_btn", tr("simulate.save_as_new"),
                                   class_="btn-success w-100 mt-1"),
        )

    @output
    @render.ui
    def sim_plot_plotly():
        """Interactive Plotly population-dynamics chart."""
        result = _run_result()
        if result is None:
            return ui.div(
                ui.tags.p(tr("simulate.run_simulation_for_results"),
                          class_="text-muted text-center py-5 my-3"),
            )
        history = result.get("result_history", [])
        if not history:
            return ui.div()
        stage_names = result.get("stage_names") or [tr("simulate.stage_count", n=i+1) for i in range(len(history[0]))]
        mode = tr("simulate.stochastic") if result.get("stochastic") else tr("simulate.deterministic")
        is_stoch = result.get("stochastic", False)
        min_h = result.get("result_min_history") if is_stoch else None
        max_h = result.get("result_max_history") if is_stoch else None
        fig = render_population_plotly(
            history, stage_names,
            title=f"{tr('simulate.population_dynamics')} — {mode} ({result['n_steps']} steps)",
            min_history=min_h,
            max_history=max_h,
        )
        return ui.HTML(plotly_html(fig))

    @output
    @render.ui
    def sim_summary():
        result = _run_result()
        if result is None:
            return None
        history = result.get("result_history", [])
        if not history:
            return None
        stage_names = result.get("stage_names") or [tr("simulate.stage_count", n=i+1) for i in range(len(history[0]))]
        final         = history[-1]
        total_initial = math.floor(sum(history[0]))
        total_final   = math.floor(sum(final))
        growth        = total_final / total_initial if total_initial else float("nan")

        rows = [
            ui.tags.tr(
                ui.tags.th(sname, class_="text-end pe-3 text-muted small fw-normal",
                           style="width:140px"),
                ui.tags.td(f"{math.floor(val):,}", class_="small"),
            )
            for sname, val in zip(stage_names, final)
        ]
        return ui.div(
            ui.hr(),
            ui.h6(tr("simulate.final_population")),
            ui.tags.table(ui.tags.tbody(*rows), class_="table table-sm mb-2"),
            ui.tags.small(
                tr("simulate.total_summary",
                   from_val=f"{total_initial:,}",
                   to_val=f"{total_final:,}",
                   growth=f"{growth:.3f}"),
                class_="text-muted",
            ),
        )

    @output
    @render.ui
    def sim_analytics_panel():
        """Collapsible analytics accordion — shown after a run completes."""
        result = _run_result()
        if result is None:
            return ui.div()

        analytics = result.get("analytics")
        if analytics is None:
            return ui.div(
                ui.tags.small(tr("simulate.analytics_unavailable"),
                              class_="text-muted d-block mt-2"),
            )

        stochastic = result.get("stochastic", False)
        stage_names = result.get("stage_names") or []

        # --- λ badge ---------------------------------------------------------
        lam = analytics.get("lambda_s" if stochastic else "lambda_1", 0.0)
        reliable = analytics.get("analytics_reliable", True)
        label = "λs" if stochastic else "λ₁"
        if lam > 1.0:
            trend, badge_cls = tr("simulate.trend_growing"), "badge-growing"
        elif lam < 1.0:
            trend, badge_cls = tr("simulate.trend_declining"), "badge-declining"
        else:
            trend, badge_cls = tr("simulate.trend_stable"), "badge-stable"

        warning_parts = []
        if not reliable:
            warning_parts.append(
                ui.tags.span(tr("simulate.low_reliability"),
                             class_="text-warning small ms-2")
            )

        lambda_row = ui.div(
            ui.tags.span(f"{label} = {lam:.4f}", class_=f"lambda-badge {badge_cls}"),
            ui.tags.span(f"  {trend}", class_="text-muted small ms-2"),
            *warning_parts,
            class_="mb-3",
        )

        # --- Stable stage distribution bar chart -----------------------------
        ssd_key = "stable_stage_distribution_of_mean" if stochastic else "stable_stage_distribution"
        ssd = analytics.get(ssd_key, [])
        ssd_html = _ssd_chart(ssd, stage_names, tr) if ssd else ui.div()

        # --- Elasticity heatmap ----------------------------------------------
        elast_key = "elasticities_of_mean" if stochastic else "elasticities"
        elast = analytics.get(elast_key, [])
        heatmap_html = _elasticity_heatmap(elast, stage_names, tr) if elast else ui.div()

        # --- Reproductive value (deterministic only) -------------------------
        rv = analytics.get("reproductive_value", []) if not stochastic else []
        rv_html = _rv_chart(rv, stage_names, tr) if rv else ui.div()

        # --- Assemble accordion ----------------------------------------------
        content_items = [lambda_row]
        if ssd:
            content_items += [
                ui.tags.div(tr("simulate.stable_stage_distribution"), class_="section-label mt-2 mb-1"),
                ssd_html,
            ]
        if elast:
            content_items += [
                ui.tags.div(tr("simulate.elasticities"), class_="section-label mt-3 mb-1"),
                heatmap_html,
            ]
        if rv:
            content_items += [
                ui.tags.div(tr("simulate.reproductive_value"), class_="section-label mt-3 mb-1"),
                rv_html,
            ]

        # --- Matrix display --------------------------------------------------
        if stochastic:
            mean_mat = analytics.get("mean_matrix", [])
            if mean_mat and isinstance(mean_mat[0], list) and len(mean_mat[0]) == len(mean_mat):
                content_items += [
                    ui.tags.div(tr("simulate.average_matrix"), class_="section-label mt-3 mb-1"),
                    matrix_display(mean_mat, stage_names),
                ]
        else:
            snapshot = result.get("matrices_snapshot") or []
            mat = snapshot[0] if snapshot else []
            if mat:
                content_items += [
                    ui.tags.div(tr("simulate.projection_matrix"), class_="section-label mt-3 mb-1"),
                    matrix_display(mat, stage_names),
                ]

        return ui.div(
            ui.accordion(
                ui.accordion_panel(
                    f"📊 {tr('simulate.analytics')}",
                    *content_items,
                ),
                id="analytics_accordion",
                open=False,
            ),
            class_="mt-3",
        )

    # ---- Reset callback (returned to server.py) --------------------------

    def reset():
        """Clear run-tab state. Called by library's 'New simulation' button."""
        _run_result.set(None)
        _in_sim.set([])
        msg.set(None)

    return reset


# ---------------------------------------------------------------------------
# Analytics chart helpers
# ---------------------------------------------------------------------------

def _ssd_chart(ssd: list[float], stage_names: list[str], tr) -> ui.HTML:
    """Horizontal bar chart of the stable stage distribution."""
    import plotly.graph_objects as go

    names = stage_names or [f"{tr('simulate.stage')} {i}" for i in range(len(ssd))]
    fig = go.Figure(go.Bar(
        x=ssd,
        y=names,
        orientation="h",
        marker_color="#4a7c59",
        text=[f"{v:.1%}" for v in ssd],
        textposition="outside",
    ))
    fig.update_layout(
        height=max(120, 30 * len(names) + 60),
        margin=dict(l=10, r=60, t=10, b=10),
        xaxis=dict(range=[0, max(ssd) * 1.2], showticklabels=False, showgrid=False),
        yaxis=dict(autorange="reversed"),
        plot_bgcolor="white", paper_bgcolor="white",
        font=dict(family="Inter, sans-serif", size=11),
        showlegend=False,
    )
    return ui.HTML(fig.to_html(include_plotlyjs=False, full_html=False,
                               config={"displayModeBar": False}))


def _elasticity_heatmap(elast: list[list[float]], stage_names: list[str], tr) -> ui.HTML:
    """n×n elasticity heatmap — green sequential colorscale."""
    import plotly.graph_objects as go

    n = len(elast)
    names = stage_names or [f"{tr('simulate.stage')} {i}" for i in range(n)]
    # Row = destination stage (i), Column = source stage (j)
    fig = go.Figure(go.Heatmap(
        z=elast,
        x=names,
        y=names,
        colorscale="Greens",
        text=[[f"{v:.3f}" for v in row] for row in elast],
        texttemplate="%{text}",
        showscale=True,
        colorbar=dict(thickness=10, len=0.8),
        hovertemplate="from %{x} → to %{y}<br>elasticity: %{z:.4f}<extra></extra>",
    ))
    cell_px = max(50, min(80, 300 // n))
    fig.update_layout(
        height=n * cell_px + 80,
        margin=dict(l=60, r=60, t=20, b=60),
        xaxis=dict(title=tr("simulate.source_stage"), side="bottom"),
        yaxis=dict(title=tr("simulate.dest_stage"), autorange="reversed"),
        plot_bgcolor="white", paper_bgcolor="white",
        font=dict(family="Inter, sans-serif", size=11),
    )
    return ui.HTML(fig.to_html(include_plotlyjs=False, full_html=False,
                               config={"displayModeBar": False}))


def _build_trajectory_table(history, stage_names, min_h, max_h, var_h, tr) -> "ui.Tag":
    """Scrollable HTML table of the full population trajectory.

    Stochastic: grouped two-row header — Stage (colspan 4) / Mean | Min | Max | Var.
    Deterministic: single-row header — Step | Stage1 | Stage2 | …
    """
    is_stoch = min_h is not None
    n_stages = len(stage_names)

    if is_stoch:
        th = ui.tags.th
        step_th = th(tr("simulate.step"), rowspan="2",
                     class_="text-center align-middle border-end",
                     style="min-width:48px")
        stage_ths = [
            th(name, colspan="4",
               class_="text-center border-start border-end small",
               style="min-width:160px")
            for name in stage_names
        ]
        header_row1 = ui.tags.tr(step_th, *stage_ths)
        metric_labels = [tr("simulate.col_mean"), tr("simulate.col_min"),
                         tr("simulate.col_max"), tr("simulate.col_std")]
        metric_ths = []
        for i in range(n_stages):
            for j, label in enumerate(metric_labels):
                cls = "text-end small text-muted" + (" border-start" if j == 0 else "")
                metric_ths.append(th(label, class_=cls, style="min-width:80px"))
        header_row2 = ui.tags.tr(*metric_ths)
        header = ui.tags.thead(header_row1, header_row2)
    else:
        cells = [ui.tags.th(tr("simulate.step"), class_="text-center border-end",
                            style="min-width:48px")]
        for name in stage_names:
            cells.append(ui.tags.th(name, class_="text-end small", style="min-width:100px"))
        header = ui.tags.thead(ui.tags.tr(*cells))

    rows = []
    for t, row in enumerate(history):
        if is_stoch:
            tds = [ui.tags.td(str(t), class_="text-center text-muted small border-end")]
            for s in range(n_stages):
                mean_v = row[s] if s < len(row) else 0.0
                min_v  = min_h[t][s] if min_h and t < len(min_h) and s < len(min_h[t]) else 0.0
                max_v  = max_h[t][s] if max_h and t < len(max_h) and s < len(max_h[t]) else 0.0
                var_v  = var_h[t][s] if var_h and t < len(var_h) and s < len(var_h[t]) else 0.0
                tds += [
                    ui.tags.td(f"{math.floor(mean_v):,}", class_="text-end small border-start"),
                    ui.tags.td(f"{math.floor(min_v):,}",  class_="text-end small"),
                    ui.tags.td(f"{math.floor(max_v):,}",  class_="text-end small"),
                    ui.tags.td(f"{math.sqrt(max(0.0, var_v)):,.4f}", class_="text-end small"),
                ]
        else:
            tds = [ui.tags.td(str(t), class_="text-center text-muted small border-end")]
            for s in range(n_stages):
                v = row[s] if s < len(row) else 0.0
                tds.append(ui.tags.td(f"{math.floor(v):,}", class_="text-end small"))
        rows.append(ui.tags.tr(*tds))

    return ui.div(
        ui.tags.div(
            ui.tags.table(
                header,
                ui.tags.tbody(*rows),
                class_="table table-sm table-hover table-bordered mb-0",
            ),
            style="max-height:65vh; overflow-y:auto; overflow-x:auto;",
        )
    )


def _rv_chart(rv: list[float], stage_names: list[str], tr) -> ui.HTML:
    """Bar chart of reproductive values (normalised so first stage = 1)."""
    import plotly.graph_objects as go

    names = stage_names or [f"{tr('simulate.stage')} {i}" for i in range(len(rv))]
    fig = go.Figure(go.Bar(
        x=names,
        y=rv,
        marker_color="#2d5a27",
        text=[f"{v:.2f}" for v in rv],
        textposition="outside",
    ))
    fig.update_layout(
        height=220,
        margin=dict(l=10, r=10, t=10, b=40),
        xaxis_title=tr("simulate.stage"),
        yaxis=dict(title=tr("simulate.reproductive_value"), rangemode="tozero"),
        plot_bgcolor="white", paper_bgcolor="white",
        font=dict(family="Inter, sans-serif", size=11),
        showlegend=False,
    )
    return ui.HTML(fig.to_html(include_plotlyjs=False, full_html=False,
                               config={"displayModeBar": False}))
