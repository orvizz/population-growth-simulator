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
    _stage_configs     = reactive.value(None)  # list[dict] | None: per-stage {threshold, excluded}
    _initial_vector    = reactive.value(None)  # list[float] | None: from modal
    _stage_names_cache = reactive.value(None)  # list[str] | None: resolved from first matrix

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
            _stage_configs.set(None)
            _initial_vector.set(None)
            _stage_names_cache.set(None)

    @reactive.effect
    @reactive.event(input.qe_remove_btn)
    def _remove_matrix():
        sel = getattr(input, "qe_in_sim_select", lambda: None)()
        if not sel:
            return
        _qe_in_sim.set([m for m in _qe_in_sim() if str(m["id"]) != str(sel)])
        _stage_configs.set(None)
        _initial_vector.set(None)
        _stage_names_cache.set(None)

    @reactive.effect
    @reactive.event(input.qe_configure_stages_btn)
    def _open_stage_modal():
        matrices = _qe_in_sim()
        if not matrices:
            return
        first = matrices[0]
        matrix_a = first.get("matrix_a") or []
        n = len(matrix_a)
        stage_names = first.get("stage_names") or [f"S{i}" for i in range(n)]
        _stage_names_cache.set(stage_names)

        global_threshold = float(getattr(input, "qe_threshold", lambda: 1.0)())
        current_configs = _stage_configs() or []
        current_init = _initial_vector() or []

        header = ui.tags.thead(
            ui.tags.tr(
                ui.tags.th("Stage", class_="small"),
                ui.tags.th("Initial population", class_="small"),
                ui.tags.th(f"Threshold (global: {global_threshold})", class_="small"),
                ui.tags.th("Exclude", class_="small text-center"),
            )
        )
        rows = []
        for i, name in enumerate(stage_names):
            cfg = current_configs[i] if i < len(current_configs) else {}
            init_val = float(current_init[i]) if i < len(current_init) else 0.0
            threshold_val = cfg.get("threshold") if isinstance(cfg, dict) else None
            excluded_val = cfg.get("excluded", False) if isinstance(cfg, dict) else False

            rows.append(ui.tags.tr(
                ui.tags.td(ui.tags.span(name, class_="small"), class_="align-middle"),
                ui.tags.td(
                    ui.input_numeric(f"qe_stage_{i}_init", None, value=init_val, min=0, step=1)
                ),
                ui.tags.td(
                    ui.input_text(
                        f"qe_stage_{i}_threshold", None,
                        value="" if threshold_val is None else str(threshold_val),
                        placeholder=str(global_threshold),
                    )
                ),
                ui.tags.td(
                    ui.input_checkbox(f"qe_stage_{i}_exclude", None, value=bool(excluded_val)),
                    class_="text-center",
                ),
            ))

        modal = ui.modal(
            ui.tags.table(header, ui.tags.tbody(*rows), class_="table table-sm mb-2"),
            ui.tags.small(
                "Leave threshold blank to fall back to the global threshold.",
                class_="text-muted",
            ),
            title="Configure stages",
            footer=ui.div(
                ui.modal_button("Cancel", class_="btn-secondary me-2"),
                ui.input_action_button("qe_stage_save_btn", "Save", class_="btn-primary"),
            ),
            easy_close=True,
            size="m",
        )
        ui.modal_show(modal)

    @reactive.effect
    @reactive.event(input.qe_stage_save_btn)
    def _save_stage_config():
        names = _stage_names_cache() or []
        n = len(names)
        if n == 0:
            return

        any_included = any(
            not bool(getattr(input, f"qe_stage_{i}_exclude", lambda: False)())
            for i in range(n)
        )
        if not any_included:
            ui.notification_show(
                "At least one stage must not be excluded.",
                type="error",
                duration=4,
            )
            return

        init_vec = []
        configs = []
        for i in range(n):
            raw_init = getattr(input, f"qe_stage_{i}_init", lambda: None)()
            init_val = float(raw_init) if raw_init is not None else 0.0
            threshold_raw = str(getattr(input, f"qe_stage_{i}_threshold", lambda: "")() or "").strip()
            excluded = bool(getattr(input, f"qe_stage_{i}_exclude", lambda: False)())

            threshold = None
            if threshold_raw:
                try:
                    threshold = float(threshold_raw)
                except ValueError:
                    ui.notification_show(
                        f"Invalid threshold for stage '{names[i]}'.",
                        type="error",
                        duration=4,
                    )
                    return

            init_vec.append(init_val)
            configs.append({"threshold": threshold, "excluded": excluded})

        _initial_vector.set(init_vec)
        _stage_configs.set(configs)
        ui.modal_remove()

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

        vec = _initial_vector()
        if not vec:
            _qe_msg.set(("Configure stages first (click 'Configure stages').", True))
            return

        try:
            n_steps   = int(getattr(input, "qe_steps", lambda: 50)())
            n_runs    = int(getattr(input, "qe_runs", lambda: 500)())
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

        stage_configs = _stage_configs()
        if stage_configs is not None:
            body["stage_configs"] = stage_configs

        stage_names = _stage_names_cache()
        if stage_names is not None:
            body["stage_names"] = stage_names

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
        _stage_configs.set(None)      # new
        _initial_vector.set(None)     # new
        _stage_names_cache.set(None)  # new

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

    # ---- View matrices modal ---------------------------------------------

    @reactive.effect
    @reactive.event(input.qe_view_matrices_btn)
    def _open_matrices_modal():
        job = _selected_job()
        if not job:
            return
        snapshot = job.get("matrices_snapshot") or []
        stage_names = (job.get("params") or {}).get("stage_names")
        _matrices_modal(snapshot, stage_names)

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
                # Section 2: Stage configuration
                ui.tags.div("2 · Stage configuration", class_="section-label mt-3"),
                ui.input_action_button(
                    "qe_configure_stages_btn",
                    "Configure stages…",
                    class_="btn-outline-secondary btn-sm w-100",
                    disabled=(len(_qe_in_sim()) < 2),
                ),
                ui.output_ui("qe_stage_summary_out"),
                # Section 3: Simulation parameters
                ui.tags.div("3 · Simulation parameters", class_="section-label mt-3"),
                ui.layout_columns(
                    ui.input_numeric("qe_threshold", "Global extinction threshold",
                                     value=1.0, min=0.001, step=0.1),
                    ui.input_numeric("qe_steps", "Time steps", value=50, min=1, max=1000),
                    col_widths=[6, 6],
                ),
                ui.layout_columns(
                    ui.input_numeric("qe_runs", "Number of runs", value=500, min=10, max=5000),
                    ui.input_numeric("qe_seed", "Random seed (blank = random)", value=None),
                    col_widths=[6, 6],
                ),
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
                class_="text-muted me-3",
            ),
            ui.input_action_button(
                "qe_view_matrices_btn",
                "View matrices",
                class_="btn-outline-secondary btn-sm",
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
                _threshold_summary_card(params),
                *([
                    ui.tags.div("Average matrix (Ā)", class_="section-label mt-3 mb-1"),
                    matrix_display(avg_mat, stage_names=params.get("stage_names")),
                ] if avg_mat and isinstance(avg_mat[0], list) and len(avg_mat[0]) == len(avg_mat) else []),
                *([
                    ui.tags.div("Time to extinction distribution",
                                class_="section-label mt-3 mb-1"),
                    tte_chart,
                ] if tte_dist else []),
                *([
                    ui.tags.div("Which stage triggered extinction",
                                class_="section-label mt-3 mb-1"),
                    _trigger_breakdown_chart(
                        result.get("extinction_trigger_counts", {}),
                        params.get("stage_names"),
                    ),
                ] if result.get("extinction_trigger_counts") else []),
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

    @output
    @render.ui
    def qe_stage_summary_out():
        configs = _stage_configs()
        names = _stage_names_cache()
        if not names or configs is None:
            return ui.tags.small(
                "Not configured — click 'Configure stages' to set up.",
                class_="text-muted d-block",
            )
        n_excluded = sum(1 for c in configs if c.get("excluded", False))
        threshold = float(getattr(input, "qe_threshold", lambda: 1.0)())
        return ui.tags.small(
            f"{len(names)} stages · global threshold: {threshold} · {n_excluded} excluded",
            class_="text-muted d-block",
        )


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


def _threshold_summary_card(params: dict) -> "ui.Tag":
    """Card showing per-stage threshold config. Returns empty div if no stage_configs."""
    stage_configs = params.get("stage_configs")
    if not stage_configs:
        return ui.div()

    stage_names = params.get("stage_names") or [f"S{i}" for i in range(len(stage_configs))]
    global_threshold = params.get("extinction_threshold", 1.0)

    rows = []
    for i, cfg in enumerate(stage_configs):
        name = stage_names[i] if i < len(stage_names) else f"S{i}"
        excluded = cfg.get("excluded", False) if isinstance(cfg, dict) else False
        specific = cfg.get("threshold") if isinstance(cfg, dict) else None

        if excluded:
            threshold_display = "—"
            status_badge = ui.tags.span("Excluded", class_="badge bg-secondary")
        else:
            threshold_display = (
                f"{specific}" if specific is not None
                else f"{global_threshold} (global)"
            )
            status_badge = ui.tags.span("Monitored", class_="badge bg-success")

        rows.append(ui.tags.tr(
            ui.tags.td(name, class_="small"),
            ui.tags.td(threshold_display, class_="small"),
            ui.tags.td(status_badge),
        ))

    return ui.div(
        ui.tags.div("Stage threshold configuration", class_="section-label mb-2"),
        ui.tags.table(
            ui.tags.thead(
                ui.tags.tr(
                    ui.tags.th("Stage", class_="small text-muted fw-normal"),
                    ui.tags.th("Threshold", class_="small text-muted fw-normal"),
                    ui.tags.th("Status", class_="small text-muted fw-normal"),
                )
            ),
            ui.tags.tbody(*rows),
            class_="table table-sm",
        ),
        class_="mb-3",
    )


def _trigger_breakdown_chart(trigger_counts: dict, stage_names: list[str] | None) -> "ui.HTML":
    """Horizontal bar chart of which stage triggered extinction most often."""
    import plotly.graph_objects as go

    # trigger_counts keys are string stage indices (JSON serialised)
    sorted_items = sorted(trigger_counts.items(), key=lambda x: int(x[0]))
    indices = [int(k) for k, _ in sorted_items]
    counts  = [v for _, v in sorted_items]
    labels  = [
        (stage_names[i] if stage_names and i < len(stage_names) else f"S{i}")
        for i in indices
    ]

    fig = go.Figure(go.Bar(
        x=counts,
        y=labels,
        orientation="h",
        marker_color="#c0392b",
        name="Runs triggered",
    ))
    fig.update_layout(
        height=220,
        margin=dict(l=100, r=20, t=20, b=40),
        xaxis_title="Number of runs",
        yaxis_title=None,
        plot_bgcolor="white",
        paper_bgcolor="white",
        font=dict(family="Inter, sans-serif", size=11),
        showlegend=False,
    )
    return ui.HTML(plotly_html(fig))


def _matrices_modal(matrices_snapshot: list, stage_names: list[str] | None) -> None:
    """Open a modal showing each matrix in matrices_snapshot."""
    if not matrices_snapshot:
        return

    cards = []
    for i, mat in enumerate(matrices_snapshot):
        cards.append(
            ui.div(
                ui.tags.div(f"Matrix {i + 1}", class_="section-label mb-2"),
                matrix_display(mat, stage_names=stage_names),
                class_="mb-4",
            )
        )

    modal = ui.modal(
        *cards,
        title="Matrices used in this analysis",
        easy_close=True,
        size="xl",
        footer=ui.modal_button("Close"),
    )
    ui.modal_show(modal)
