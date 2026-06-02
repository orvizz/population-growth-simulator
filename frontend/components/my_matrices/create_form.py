"""My matrices tab — Create form server logic.

Handles stage builder, matrix grid, and the create action.
"""
from shiny import reactive, render, req, ui

from components.utils import api


def create_form_server(input, output, session, *, token, on_created, tr):
    """Register server logic for the Create matrix form.

    Parameters
    ----------
    on_created : callable
        Called after a matrix is successfully created. Triggers
        my_matrices_server to refresh the matrix list.
    """
    _stages     = reactive.value([])
    _create_msg = reactive.value(None)
    _create_success = reactive.value(None)

    # ---- Create action ---------------------------------------------------

    @reactive.effect
    @reactive.event(input.mm_create_btn)
    def _do_create():
        req(token())
        stages = _stages()
        n = len(stages)
        if not stages or n < 2:
            _create_success.set(False)
            _create_msg.set(tr("my_matrices.add_two_stages"))
            return
        rows   = _read_matrix(input, "mm",   n)
        rows_u = _read_matrix(input, "mm_u", n)
        rows_f = _read_matrix(input, "mm_f", n)
        try:
            api("POST", "/v1/matrices", token=token(), json={
                "species_accepted": getattr(input, "mm_species", lambda: "")() or None,
                "common_name":      getattr(input, "mm_common",  lambda: "")() or None,
                "kingdom":          getattr(input, "mm_kingdom", lambda: "")() or None,
                "country_code":     getattr(input, "mm_country", lambda: "")() or None,
                "matrix_a":         rows,
                "matrix_u":         rows_u,
                "matrix_f":         rows_f,
                "stage_names":      stages,
                "visibility":       "private",
            })
            _create_success.set(True)
            _create_msg.set(tr("my_matrices.matrix_created"))
            _stages.set([])
            on_created()
        except ValueError as e:
            _create_success.set(False)
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
            return ui.tags.p(tr("my_matrices.no_stages_yet"), class_="text-muted small")
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
    def _render_matrix_grid(stages, prefix):
        n = len(stages)
        if n == 0:
            return ui.tags.p(tr("my_matrices.add_stages_hint"), class_="text-muted small")
        header = ui.tags.tr(ui.tags.th("", class_="corner"), *[ui.tags.th(s) for s in stages])
        rows = []
        for i, row_name in enumerate(stages):
            cells = [ui.tags.th(row_name)]
            for j in range(n):
                cells.append(ui.tags.td(ui.input_numeric(f"{prefix}_cell_{i}_{j}", label=None, value=0, step=0.001, width="72px")))
            rows.append(ui.tags.tr(*cells))
        return ui.tags.div(
                        ui.tags.table(ui.tags.thead(header), ui.tags.tbody(*rows),
            class_="matrix-grid-input"),
                    ui.tags.div(tr("my_matrices.tab_hint"), class_="text-muted small mt-1"),
            )

    def _read_matrix(input, prefix, n):
        return [[float(input[f"{prefix}_cell_{i}_{j}"]() or 0) for j in range(n)] for i
    in range(n)]

    @output
    @render.ui
    def mm_matrix_grid():
        return _render_matrix_grid(_stages(), "mm") 
    
    @output
    @render.ui
    def mm_matrix_u_grid():
        return _render_matrix_grid(_stages(), "mm_u") 
    

    @output
    @render.ui
    def mm_matrix_f_grid():
        return _render_matrix_grid(_stages(), "mm_f") 

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
                tr("my_matrices.valid_matrix", n=n),
                style="color:#2d5a27;font-size:11px;font-weight:600;margin-top:4px;"
            )
        except Exception:
            return ui.tags.div(
                tr("my_matrices.invalid_cells"),
                class_="text-danger small mt-1"
            )

    @output
    @render.ui
    def mm_create_result():
        input.mm_create_btn()
        msg = _create_msg()
        if not msg:
            return None
        color = "success" if _create_success() else "danger"
        return ui.div(ui.tags.span(msg, class_=f"text-{color} small"), class_="mt-2")
