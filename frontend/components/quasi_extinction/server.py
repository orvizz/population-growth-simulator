"""Quasi-Extinction tab — server logic.

Workflow:
  1. User selects ≥ 2 matrices, sets parameters, clicks Submit.
  2. POST /v1/jobs/quasi-extinction → 202 + job (status=pending).
  3. Poll GET /v1/jobs/{id} every 2 s via reactive.invalidate_later.
  4. When completed: show probability card + histograms + stats.
  5. Jobs sidebar lists all past analyses; click to view results.
"""
from shiny import reactive, render, ui

from components.utils import api, plotly_html
from components.shared import matrix_display


def qe_server(input, output, session, *, token, username):
    """Register all server-side logic for the Quasi-Extinction tab."""

    # ---- Reactive state --------------------------------------------------
    _jobs_cache      = reactive.value([])   # list of JobSummaryRecord dicts
    _selected_job    = reactive.value(None) # full JobRecord dict (when viewing results)
    _pending_job_id  = reactive.value(None) # int — job currently being polled
    _show_form       = reactive.value(True) # True = show setup form, False = show results
    _qe_available    = reactive.value([])   # matrix search results
    _qe_in_sim       = reactive.value([])   # matrices added to analysis
    _qe_msg          = reactive.value(None) # (text: str, is_error: bool) | None

    # ---- Helpers ---------------------------------------------------------

    def _msg_div():
        m = _qe_msg()
        if not m:
            return ui.div()
        text, is_err = m
        cls = "text-danger" if is_err else "text-success"
        return ui.div(ui.tags.span(text, class_=cls), class_="small mt-2")

    def _matrix_select_widget(matrices, select_id):
        if not matrices:
            return ui.p("(empty)", class_="text-muted small")
        choices = {
            str(m["id"]): f"{m.get('species_accepted') or '?'} #{m['id']}"
            for m in matrices
        }
        return ui.input_select(select_id, None, choices=choices,
                               size=min(8, len(choices)))

    def _refresh_jobs():
        t = token()
        if not t:
            _jobs_cache.set([])
            return
        try:
            _jobs_cache.set(api("GET", "/v1/jobs", token=t))
        except ValueError:
            _jobs_cache.set([])

    def _fetch_job(job_id: int):
        try:
            return api("GET", f"/v1/jobs/{job_id}", token=token())
        except ValueError:
            return None

    # ---- Auth change: refresh or clear jobs cache ------------------------

    @reactive.effect
    def _on_auth_change():
        if username():
            _refresh_jobs()
        else:
            _jobs_cache.set([])
            _selected_job.set(None)
            _pending_job_id.set(None)
            _show_form.set(True)
            _qe_msg.set(None)

    # ---- Matrix search ---------------------------------------------------

    @reactive.effect
    @reactive.event(input.qe_search_btn)
    def _search_matrices():
        params = {"limit": 100}
        species = getattr(input, "qe_species", lambda: "")()
        if species:
            params["species"] = species
        try:
            _qe_available.set(api("GET", "/v1/matrices", params=params))
        except ValueError:
            _qe_available.set([])

    @reactive.effect
    @reactive.event(input.qe_add_btn)
    def _add_matrix():
        sel = getattr(input, "qe_matrix_select", lambda: None)()
        if not sel:
            return
        avail = _qe_available()
        current = _qe_in_sim()
        current_ids = {m["id"] for m in current}
        to_add = [m for m in avail if str(m["id"]) == str(sel)
                  and m["id"] not in current_ids]
        if to_add:
            _qe_in_sim.set(current + to_add)

    @reactive.effect
    @reactive.event(input.qe_remove_btn)
    def _remove_matrix():
        sel = getattr(input, "qe_in_sim_select", lambda: None)()
        if not sel:
            return
        _qe_in_sim.set([m for m in _qe_in_sim() if str(m["id"]) != str(sel)])

    # ---- Submit new QE job -----------------------------------------------

    @reactive.effect
    @reactive.event(input.qe_submit_btn)
    def _submit_job():
        t = token()
        if not t:
            _qe_msg.set(("Log in to run quasi-extinction analyses.", True))
            return

        matrices = _qe_in_sim()
        if len(matrices) < 2:
            _qe_msg.set(("Add at least 2 matrices to the analysis.", True))
            return

        raw_vec = getattr(input, "qe_init_vec", lambda: "")().strip()
        if not raw_vec:
            _qe_msg.set(("Enter an initial vector.", True))
            return
        try:
            vec = [float(x.strip()) for x in raw_vec.split(",") if x.strip()]
        except ValueError:
            _qe_msg.set(("Invalid vector — use comma-separated numbers.", True))
            return

        try:
            n_steps = int(getattr(input, "qe_steps", lambda: 50)())
            n_runs  = int(getattr(input, "qe_runs", lambda: 500)())
            threshold = float(getattr(input, "qe_threshold", lambda: 1.0)())
        except (TypeError, ValueError):
            _qe_msg.set(("Invalid numeric parameter.", True))
            return

        body: dict = {
            "matrix_ids": [m["id"] for m in matrices],
            "initial_vector": vec,
            "n_steps": n_steps,
            "n_runs": n_runs,
            "extinction_threshold": threshold,
        }
        seed_val = getattr(input, "qe_seed", lambda: None)()
        if seed_val is not None:
            try:
                body["random_seed"] = int(seed_val)
            except (TypeError, ValueError):
                pass

        try:
            job = api("POST", "/v1/jobs/quasi-extinction", token=t, json=body)
            _pending_job_id.set(job["id"])
            _qe_msg.set(("Analysis started — polling for results…", False))
            _refresh_jobs()
        except ValueError as e:
            _qe_msg.set((str(e), True))

    # ---- Polling loop ----------------------------------------------------

    @reactive.effect
    def _poll_job():
        """Poll the pending job every 2 s until completed or failed."""
        jid = _pending_job_id.get()
        if jid is None:
            return
        job = _fetch_job(jid)
        if job is None:
            # Job vanished — stop polling
            _pending_job_id.set(None)
            return
        status = job.get("status", "")
        if status in ("completed", "failed"):
            _pending_job_id.set(None)
            _selected_job.set(job)
            _show_form.set(False)
            _refresh_jobs()
            if status == "completed":
                _qe_msg.set(("Analysis complete.", False))
            else:
                _qe_msg.set((f"Analysis failed: {job.get('error', 'unknown error')}", True))
        else:
            reactive.invalidate_later(2.0)

    # ---- New analysis button (reset to form) -----------------------------

    @reactive.effect
    @reactive.event(input.qe_new_btn)
    def _new_analysis():
        _show_form.set(True)
        _selected_job.set(None)
        _qe_msg.set(None)
        _qe_in_sim.set([])

    # ---- Sidebar job list click -----------------------------------------

    @reactive.effect
    @reactive.event(input.qe_job_select)
    def _select_job():
        jid_str = getattr(input, "qe_job_select", lambda: None)()
        if not jid_str:
            return
        try:
            jid = int(jid_str)
        except (TypeError, ValueError):
            return
        job = _fetch_job(jid)
        if job:
            _selected_job.set(job)
            _show_form.set(False)
            _qe_msg.set(None)

    # ---- Delete selected job ---------------------------------------------

    @reactive.effect
    @reactive.event(input.qe_delete_btn)
    def _delete_job():
        job = _selected_job()
        if not job:
            return
        try:
            api("DELETE", f"/v1/jobs/{job['id']}", token=token())
            _selected_job.set(None)
            _show_form.set(True)
            _qe_msg.set(("Analysis deleted.", False))
            _refresh_jobs()
        except ValueError as e:
            _qe_msg.set((str(e), True))

    # ---- Rendered outputs ------------------------------------------------

    @output
    @render.ui
    def qe_sidebar_msg():
        return _msg_div()

    @output
    @render.ui
    def qe_jobs_list_out():
        jobs = _jobs_cache()
        selected = _selected_job()
        selected_id = selected["id"] if selected else None

        if not jobs:
            if username():
                return ui.p("No past analyses.", class_="text-muted small")
            return ui.p("Log in to view analyses.", class_="text-muted small")

        items = []
        for j in jobs:
            jid = j["id"]
            status = j.get("status", "")
            is_selected = jid == selected_id

            # Status badge color
            if status == "completed":
                badge_cls = "bg-success"
            elif status == "failed":
                badge_cls = "bg-danger"
            elif status == "running":
                badge_cls = "bg-warning text-dark"
            else:
                badge_cls = "bg-secondary"

            item_cls = "qe-job-item selected" if is_selected else "qe-job-item"
            created = j.get("created_at", "")[:16].replace("T", " ")

            items.append(
                ui.div(
                    ui.div(
                        ui.tags.span(f"#{jid}", class_="text-muted small me-1"),
                        ui.tags.span(status, class_=f"badge {badge_cls} ms-1"),
                        class_="d-flex align-items-center",
                    ),
                    ui.tags.small(created, class_="text-muted d-block"),
                    class_=item_cls,
                    # Use an action button styled as a list item click
                    onclick=(
                        f"Shiny.setInputValue('qe_job_select', '{jid}', "
                        f"{{priority: 'event'}})"
                    ),
                )
            )

        return ui.div(*items)

    @output
    @render.ui
    def qe_main_panel():
        if not username():
            return _login_prompt_panel()
        if _show_form():
            return _build_form_panel()
        job = _selected_job()
        if job is None:
            return _build_form_panel()
        return _build_results_panel(job)

    # ---- Helper panel builders -------------------------------------------

    def _login_prompt_panel():
        return ui.card(
            ui.card_body(
                ui.tags.div(
                    ui.tags.p(
                        "Log in to run quasi-extinction probability analyses.",
                        class_="text-muted",
                    ),
                    class_="text-center py-5",
                ),
            ),
        )

    def _build_form_panel():
        """Setup form for a new quasi-extinction analysis."""
        pending = _pending_job_id.get()
        if pending is not None:
            # Show spinner while polling
            return ui.card(
                ui.card_body(
                    ui.div(
                        ui.tags.div(class_="spinner-border text-success me-3",
                                    role="status",
                                    style="width:2rem;height:2rem"),
                        ui.tags.span("Running analysis — this may take a few seconds…",
                                     class_="text-muted"),
                        class_="d-flex align-items-center justify-content-center py-5",
                    ),
                    _msg_div(),
                ),
            )

        return ui.card(
            ui.card_header("Configure quasi-extinction analysis"),
            ui.card_body(
                # Section 1: Matrix selection
                ui.tags.div("1 · Matrices (select ≥ 2)", class_="section-label"),
                ui.input_text("qe_species", None, placeholder="Species name"),
                ui.input_action_button("qe_search_btn", "Search",
                                       class_="btn-secondary btn-sm mt-1 mb-1"),
                ui.output_ui("qe_matrix_select_out"),
                ui.layout_columns(
                    ui.input_action_button("qe_add_btn", "Add ▼",
                                           class_="btn-outline-secondary btn-sm w-100"),
                    ui.input_action_button("qe_remove_btn", "Remove ▲",
                                           class_="btn-outline-danger btn-sm w-100"),
                    col_widths=[6, 6],
                ),
                ui.output_ui("qe_in_sim_select_out"),
                # Section 2: Parameters
                ui.tags.div("2 · Simulation parameters", class_="section-label mt-3"),
                ui.layout_columns(
                    ui.input_text("qe_init_vec", "Initial vector",
                                  placeholder="e.g. 100, 50"),
                    ui.input_numeric("qe_threshold", "Extinction threshold",
                                     value=1.0, min=0.001, step=0.1),
                    col_widths=[6, 6],
                ),
                ui.layout_columns(
                    ui.input_numeric("qe_steps", "Time steps", value=50, min=1, max=1000),
                    ui.input_numeric("qe_runs", "Number of runs", value=500,
                                     min=10, max=5000),
                    col_widths=[6, 6],
                ),
                ui.input_numeric("qe_seed", "Random seed (blank = random)", value=None),
                ui.tags.small(
                    "Each run is an independent stochastic simulation. "
                    "More runs → more precise probability estimate.",
                    class_="text-muted d-block mb-2",
                ),
                # Submit
                ui.input_action_button("qe_submit_btn", "▶ Run analysis",
                                       class_="btn-primary w-100 mt-2"),
                _msg_div(),
            ),
        )

    def _build_results_panel(job: dict):
        """Results panel for a completed or failed job."""
        status = job.get("status", "")
        result = job.get("result")

        # Header with metadata
        params = job.get("params", {})
        n_steps = params.get("n_steps", "?")
        n_runs  = params.get("n_runs", "?")
        threshold = params.get("extinction_threshold", "?")
        created = job.get("created_at", "")[:16].replace("T", " ")

        header_items = [
            ui.tags.span(f"Job #{job['id']}", class_="fw-bold me-3"),
            ui.tags.span(
                status,
                class_=f"badge {'bg-success' if status == 'completed' else 'bg-danger'} me-3",
            ),
            ui.tags.small(
                f"{n_runs} runs · {n_steps} steps · threshold {threshold} · {created}",
                class_="text-muted",
            ),
        ]

        if status == "failed":
            return ui.card(
                ui.card_header(ui.div(*header_items, class_="d-flex align-items-center")),
                ui.card_body(
                    ui.div(
                        ui.tags.p(f"Analysis failed: {job.get('error', 'unknown error')}",
                                  class_="text-danger"),
                        ui.input_action_button("qe_delete_btn", "Delete",
                                               class_="btn-outline-danger btn-sm"),
                    )
                ),
            )

        if not result:
            return ui.card(
                ui.card_header("Results"),
                ui.card_body(ui.tags.p("No result data available.", class_="text-muted")),
            )

        prob  = result.get("quasi_extinction_probability", 0.0)
        n_ext = result.get("n_extinct", 0)
        mean_fp = result.get("mean_final_population", 0.0)
        std_fp  = result.get("std_final_population", 0.0)
        avg_mat = result.get("average_matrix", [])

        # Probability card color
        if prob < 0.1:
            prob_cls = "qe-probability-low"
        elif prob < 0.5:
            prob_cls = "qe-probability-mid"
        else:
            prob_cls = "qe-probability-high"

        prob_card = ui.div(
            ui.tags.div(
                ui.tags.div(f"{prob:.1%}", class_="qe-prob-number"),
                ui.tags.div(
                    f"Quasi-extinction probability",
                    class_="mt-1",
                    style="font-size:13px",
                ),
                ui.tags.div(
                    f"{n_ext} of {n_runs} runs ended in extinction",
                    class_="text-muted mt-1",
                    style="font-size:11px",
                ),
                class_=f"qe-probability-card {prob_cls}",
            ),
        )

        # Stats card
        stats_card = ui.div(
            ui.tags.div(
                ui.tags.div("Final population statistics", class_="section-label mb-2"),
                ui.tags.table(
                    ui.tags.tbody(
                        ui.tags.tr(
                            ui.tags.th("Mean", class_="text-muted small fw-normal pe-3"),
                            ui.tags.td(f"{mean_fp:,.2f}", class_="small"),
                        ),
                        ui.tags.tr(
                            ui.tags.th("Std dev", class_="text-muted small fw-normal pe-3"),
                            ui.tags.td(f"{std_fp:,.2f}", class_="small"),
                        ),
                    ),
                    class_="table table-sm",
                ),
            ),
            class_="mb-3",
        )

        # Time-to-extinction histogram (only when some runs went extinct)
        tte_dist = result.get("time_to_extinction_distribution", {})
        tte_chart = _tte_histogram(tte_dist) if tte_dist else ui.div()

        # λs distribution histogram
        ls_dist = result.get("lambda_s_distribution", [])
        ls_chart = _lambda_s_histogram(ls_dist, threshold) if ls_dist else ui.div()

        return ui.card(
            ui.card_header(ui.div(*header_items, class_="d-flex align-items-center flex-wrap gap-1")),
            ui.card_body(
                ui.layout_columns(
                    prob_card,
                    stats_card,
                    col_widths=[6, 6],
                ),
                *([
                    ui.tags.div("Average matrix (Ā)", class_="section-label mt-3 mb-1"),
                    matrix_display(avg_mat, stage_names=None),
                ] if avg_mat and isinstance(avg_mat[0], list) and len(avg_mat[0]) == len(avg_mat) else []),
                *([
                    ui.tags.div("Time to extinction distribution",
                                class_="section-label mt-3 mb-1"),
                    tte_chart,
                ] if tte_dist else []),
                ui.tags.div("Stochastic growth rate (λs) distribution",
                            class_="section-label mt-3 mb-1"),
                ls_chart,
                ui.hr(),
                ui.input_action_button("qe_delete_btn", "Delete this analysis",
                                       class_="btn-outline-danger btn-sm"),
            ),
            full_screen=True,
        )

    # ---- Server-rendered sub-outputs (used inside rendered panels) -------

    @output
    @render.ui
    def qe_matrix_select_out():
        return _matrix_select_widget(_qe_available(), "qe_matrix_select")

    @output
    @render.ui
    def qe_in_sim_select_out():
        return _matrix_select_widget(_qe_in_sim(), "qe_in_sim_select")


# ---------------------------------------------------------------------------
# Chart helpers
# ---------------------------------------------------------------------------

def _tte_histogram(tte_dist: dict) -> "ui.HTML":
    """Bar chart of time-to-extinction distribution."""
    import plotly.graph_objects as go

    steps = [int(k) for k in sorted(tte_dist.keys(), key=int)]
    counts = [tte_dist[str(s)] for s in steps]

    fig = go.Figure(go.Bar(
        x=steps, y=counts,
        marker_color="#c0392b",
        name="Extinct runs",
    ))
    fig.update_layout(
        height=220,
        margin=dict(l=40, r=20, t=20, b=40),
        xaxis_title="Step at extinction",
        yaxis_title="Number of runs",
        plot_bgcolor="white", paper_bgcolor="white",
        font=dict(family="Inter, sans-serif", size=11),
        showlegend=False,
    )
    return ui.HTML(plotly_html(fig))


def _lambda_s_histogram(ls_dist: list, threshold: float | None = None) -> "ui.HTML":
    """Histogram of per-run stochastic growth rate estimates."""
    import plotly.graph_objects as go

    fig = go.Figure(go.Histogram(
        x=ls_dist,
        nbinsx=40,
        marker_color="#4a7c59",
        opacity=0.85,
        name="λs per run",
    ))

    # Vertical line at λs = 1 (neutral growth)
    fig.add_vline(x=1.0, line=dict(color="#c0392b", width=2, dash="dash"),
                  annotation_text="λs = 1", annotation_position="top right")

    fig.update_layout(
        height=220,
        margin=dict(l=40, r=20, t=20, b=40),
        xaxis_title="λs (per run)",
        yaxis_title="Count",
        plot_bgcolor="white", paper_bgcolor="white",
        font=dict(family="Inter, sans-serif", size=11),
        showlegend=False,
    )
    return ui.HTML(plotly_html(fig))
