"""My matrices tab — create and edit the current user's custom matrices (auth required)."""
from shiny import reactive, render, req, ui

from .utils import api


def my_matrices_ui():
    return ui.nav_panel(
        "My matrices",
        ui.output_ui("mm_view"),
    )


def my_matrices_server(input, output, session, *, token, username):
    # Bump to force _my_matrices() to re-fetch after mutations
    _version = reactive.value(0)
    _create_msg = reactive.value(None)
    _edit_msg = reactive.value(None)

    def _invalidate():
        _version.set(_version() + 1)

    @reactive.calc
    def _my_matrices():
        _version()  # reactive dependency
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
        raw = getattr(input, "mm_matrix_a", lambda: "")().strip()
        if not raw:
            _create_msg.set("Matrix A is required.")
            return
        try:
            matrix_a = [
                [float(v.strip()) for v in row.split(",")]
                for row in raw.split(";")
                if row.strip()
            ]
        except ValueError:
            _create_msg.set("Invalid matrix — rows separated by ';', values by ','.")
            return

        stages_raw = getattr(input, "mm_stages", lambda: "")().strip()
        stage_names = [s.strip() for s in stages_raw.split(",") if s.strip()] or None

        try:
            api("POST", "/v1/matrices", token=token(), json={
                "species_accepted": getattr(input, "mm_species", lambda: "")() or None,
                "common_name": getattr(input, "mm_common", lambda: "")() or None,
                "kingdom": getattr(input, "mm_kingdom", lambda: "")() or None,
                "country_code": getattr(input, "mm_country", lambda: "")() or None,
                "matrix_a": matrix_a,
                "stage_names": stage_names,
            })
            _create_msg.set("Matrix created.")
            _invalidate()
        except ValueError as e:
            _create_msg.set(str(e))

    # ---- Edit -------------------------------------------------------------

    @reactive.effect
    @reactive.event(input.mm_save_btn)
    def _do_save():
        req(token())
        mid = getattr(input, "mm_my_select", lambda: None)()
        req(mid)
        try:
            api("PATCH", f"/v1/matrices/{mid}", token=token(), json={
                "common_name": getattr(input, "mm_edit_common", lambda: "")() or None,
                "country_code": getattr(input, "mm_edit_country", lambda: "")() or None,
            })
            _edit_msg.set("Changes saved.")
            _invalidate()
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

    # ---- Outputs ----------------------------------------------------------

    @output
    @render.ui
    def mm_view():
        if not username():
            return ui.card(
                ui.card_header("My matrices"),
                ui.p("Please log in from the Account tab to manage your matrices.",
                     class_="text-muted p-3"),
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
                # Create
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
                    ui.input_text("mm_stages", "Stages (comma-separated)",
                                  placeholder="seedling, juvenile, adult"),
                    ui.input_text_area(
                        "mm_matrix_a",
                        "Matrix A  (rows by ';', values by ',')",
                        placeholder="0.0,1.2,3.4; 0.5,0.0,0.0; 0.0,0.3,0.7",
                        rows=3,
                    ),
                    ui.input_action_button("mm_create_btn", "Create",
                                           class_="btn-success w-100 mt-2"),
                    ui.output_ui("mm_create_result"),
                ),
                # Edit
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
        mid = getattr(input, "mm_my_select", lambda: None)()
        if not mid:
            return ui.p("Select a matrix from the list to edit it.", class_="text-muted")
        try:
            m = api("GET", f"/v1/matrices/{mid}")
        except ValueError as e:
            return ui.p(str(e), class_="text-danger")

        return ui.div(
            ui.p(ui.tags.b("Editing: "), m.get("species_accepted") or f"Matrix #{mid}"),
            ui.input_text("mm_edit_common", "Common name",
                          value=m.get("common_name") or ""),
            ui.input_text("mm_edit_country", "Country code",
                          value=m.get("country_code") or ""),
            ui.input_action_button("mm_save_btn", "Save changes",
                                   class_="btn-warning w-100 mt-2"),
            ui.input_action_button("mm_delete_btn", "Delete matrix",
                                   class_="btn-outline-danger btn-sm w-100 mt-1"),
            ui.output_ui("mm_edit_result"),
        )

    @output
    @render.ui
    def mm_edit_result():
        getattr(input, "mm_save_btn", lambda: None)()
        getattr(input, "mm_delete_btn", lambda: None)()
        msg = _edit_msg()
        if not msg:
            return None
        color = "success" if "saved" in msg.lower() or "deleted" in msg.lower() else "danger"
        return ui.div(ui.tags.span(msg, class_=f"text-{color} small"), class_="mt-2")
