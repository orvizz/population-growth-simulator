"""My matrices tab — create and edit the current user's custom matrices (auth required)."""
from shiny import reactive, render, req, ui

from .utils import api

_VIS_BADGE = {
    "private": ("Private", "secondary"),
    "shared":  ("Shared",  "primary"),
    "public":  ("Public",  "success"),
}


def my_matrices_ui():
    return ui.nav_panel(
        "My matrices",
        ui.output_ui("mm_view"),
    )


def my_matrices_server(input, output, session, *, token, username):
    _version      = reactive.value(0)
    _create_msg   = reactive.value(None)
    _edit_msg     = reactive.value(None)
    _shares_version = reactive.value(0)
    _stages       = reactive.value([])   # list of stage name strings

    def _invalidate():
        _version.set(_version() + 1)

    def _invalidate_shares():
        _shares_version.set(_shares_version() + 1)

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

    # ---- Create -----------------------------------------------------------

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
            _invalidate()
        except ValueError as e:
            _create_msg.set(str(e))

    # ---- Stage builder ----------------------------------------------------

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

    _remove_btn_seen = reactive.value({})  # {btn_id: last seen click count}

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

    # ---- Matrix grid ------------------------------------------------------

    @output
    @render.ui
    def mm_matrix_grid():
        stages = _stages()
        n = len(stages)
        if n == 0:
            return ui.tags.p("Add stages above to define the matrix dimensions.", class_="text-muted small")
        # Header row
        header_cells = [ui.tags.th("", class_="corner")]
        for s in stages:
            header_cells.append(ui.tags.th(s))
        header = ui.tags.tr(*header_cells)
        # Data rows
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

    # ---- Edit / visibility ------------------------------------------------

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
            _invalidate()
        except ValueError as e:
            _edit_msg.set(str(e))

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

    # ---- Delete -----------------------------------------------------------

    @reactive.effect
    @reactive.event(input.mm_delete_btn)
    def _do_delete():
        req(token())
        mid = getattr(input, "mm_my_select", lambda: None)()
        req(mid)
        try:
            api("DELETE", f"/v1/matrices/{mid}", token=token())
            _edit_msg.set("Matrix deleted.")
            _invalidate()
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

    # ---- Outputs ----------------------------------------------------------

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
                        ui.input_action_button("mm_add_stage", "+ Add", class_="btn btn-outline-primary btn-sm"),
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

    @output
    @render.ui
    def mm_create_result():
        input.mm_create_btn()
        msg = _create_msg()
        if not msg:
            return None
        color = "success" if "created" in msg.lower() else "danger"
        return ui.div(ui.tags.span(msg, class_=f"text-{color} small"), class_="mt-2")

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

        # Shares section — only relevant when visibility is "shared"
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
                ui.tags.span(vis_label,
                             class_=f"badge text-bg-{vis_color} mb-3"),
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
