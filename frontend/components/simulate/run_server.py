"""Simulate tab — Run sub-tab server logic."""
import json

from shiny import reactive, render, ui

from components.utils import api, plotly_html, render_population_plotly
from components.shared import matrix_display


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
    @render.ui
    def sim_plot_plotly():
        """Interactive Plotly population-dynamics chart."""
        result = _run_result()
        if result is None:
            return ui.div(
                ui.tags.p("Run a simulation to see results here.",
                          class_="text-muted text-center py-5 my-3"),
            )
        history = result.get("result_history", [])
        if not history:
            return ui.div()
        stage_names = result.get("stage_names") or [f"Stage {i}" for i in range(len(history[0]))]
        mode = "Stochastic" if result.get("stochastic") else "Deterministic"
        fig = render_population_plotly(
            history, stage_names,
            title=f"Population dynamics — {mode} ({result['n_steps']} steps)",
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
                ui.tags.small("Analytics unavailable for this simulation.",
                              class_="text-muted d-block mt-2"),
            )

        stochastic = result.get("stochastic", False)
        stage_names = result.get("stage_names") or []

        # --- λ badge ---------------------------------------------------------
        lam = analytics.get("lambda_s" if stochastic else "lambda_1", 0.0)
        reliable = analytics.get("analytics_reliable", True)
        label = "λs" if stochastic else "λ₁"
        if lam > 1.0:
            trend, badge_cls = "Growing", "badge-growing"
        elif lam < 1.0:
            trend, badge_cls = "Declining", "badge-declining"
        else:
            trend, badge_cls = "Stable", "badge-stable"

        warning_parts = []
        if not reliable:
            warning_parts.append(
                ui.tags.span(" ⚠ Low reliability (short run — increase n_steps for better estimates)",
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
        ssd_html = _ssd_chart(ssd, stage_names) if ssd else ui.div()

        # --- Elasticity heatmap ----------------------------------------------
        elast_key = "elasticities_of_mean" if stochastic else "elasticities"
        elast = analytics.get(elast_key, [])
        heatmap_html = _elasticity_heatmap(elast, stage_names) if elast else ui.div()

        # --- Reproductive value (deterministic only) -------------------------
        rv = analytics.get("reproductive_value", []) if not stochastic else []
        rv_html = _rv_chart(rv, stage_names) if rv else ui.div()

        # --- Assemble accordion ----------------------------------------------
        content_items = [lambda_row]
        if ssd:
            content_items += [
                ui.tags.div("Stable stage distribution", class_="section-label mt-2 mb-1"),
                ssd_html,
            ]
        if elast:
            content_items += [
                ui.tags.div("Elasticities", class_="section-label mt-3 mb-1"),
                heatmap_html,
            ]
        if rv:
            content_items += [
                ui.tags.div("Reproductive value", class_="section-label mt-3 mb-1"),
                rv_html,
            ]

        # --- Matrix display --------------------------------------------------
        if stochastic:
            mean_mat = analytics.get("mean_matrix", [])
            if mean_mat and isinstance(mean_mat[0], list) and len(mean_mat[0]) == len(mean_mat):
                content_items += [
                    ui.tags.div("Average matrix (Āₜ)", class_="section-label mt-3 mb-1"),
                    matrix_display(mean_mat, stage_names),
                ]
        else:
            snapshot = result.get("matrices_snapshot") or []
            mat = snapshot[0] if snapshot else []
            if mat:
                content_items += [
                    ui.tags.div("Projection matrix (A)", class_="section-label mt-3 mb-1"),
                    matrix_display(mat, stage_names),
                ]

        return ui.div(
            ui.accordion(
                ui.accordion_panel(
                    "📊 Analytics",
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

def _ssd_chart(ssd: list[float], stage_names: list[str]) -> ui.HTML:
    """Horizontal bar chart of the stable stage distribution."""
    import plotly.graph_objects as go

    names = stage_names or [f"Stage {i}" for i in range(len(ssd))]
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
    return ui.HTML(fig.to_html(include_plotlyjs="cdn", full_html=False,
                               config={"displayModeBar": False}))


def _elasticity_heatmap(elast: list[list[float]], stage_names: list[str]) -> ui.HTML:
    """n×n elasticity heatmap — green sequential colorscale."""
    import plotly.graph_objects as go

    n = len(elast)
    names = stage_names or [f"S{i}" for i in range(n)]
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
        xaxis=dict(title="Source stage (j)", side="bottom"),
        yaxis=dict(title="Destination stage (i)", autorange="reversed"),
        plot_bgcolor="white", paper_bgcolor="white",
        font=dict(family="Inter, sans-serif", size=11),
    )
    return ui.HTML(fig.to_html(include_plotlyjs="cdn", full_html=False,
                               config={"displayModeBar": False}))


def _rv_chart(rv: list[float], stage_names: list[str]) -> ui.HTML:
    """Bar chart of reproductive values (normalised so first stage = 1)."""
    import plotly.graph_objects as go

    names = stage_names or [f"Stage {i}" for i in range(len(rv))]
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
        xaxis_title="Stage",
        yaxis=dict(title="Reproductive value", rangemode="tozero"),
        plot_bgcolor="white", paper_bgcolor="white",
        font=dict(family="Inter, sans-serif", size=11),
        showlegend=False,
    )
    return ui.HTML(fig.to_html(include_plotlyjs="cdn", full_html=False,
                               config={"displayModeBar": False}))
