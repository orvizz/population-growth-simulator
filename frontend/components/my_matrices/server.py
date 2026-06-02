"""My matrices tab — orchestrator: shared state, mm_view render, composes create + edit."""
import httpx
from shiny import reactive, render, ui

from components.utils import API_BASE, api
from .create_form import create_form_server
from .edit_form import edit_form_server


def my_matrices_server(input, output, session, *, token, username):
    # ---- Shared state ----------------------------------------------------
    _version = reactive.value(0)
    _import_msg = reactive.value(None)

    def _invalidate():
        _version.set(_version() + 1)

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

    # ---- Wire sub-servers ------------------------------------------------
    create_form_server(input, output, session, token=token, on_created=_invalidate)
    edit_form_server(input, output, session, token=token, on_modified=_invalidate)

    # ---- Import ----------------------------------------------------------

    @reactive.effect
    @reactive.event(input.mm_import_btn)
    def _do_import():
        files_info = input.mm_import_files()
        if not files_info:
            _import_msg.set("Select at least one file before importing.")
            return
        upload_files = []
        for f in files_info:
            with open(f["datapath"], "rb") as fh:
                upload_files.append(
                    ("files", (f["name"], fh.read(), f.get("type") or "application/octet-stream"))
                )
        try:
            r = httpx.post(
                f"{API_BASE}/v1/matrices/import",
                headers={"Authorization": f"Bearer {token()}"},
                files=upload_files,
                timeout=30,
            )
            r.raise_for_status()
            result = r.json()
        except Exception as exc:
            _import_msg.set(f"Import failed: {exc}")
            return

        n_ok = len(result.get("created", []))
        errors = result.get("errors", [])
        if n_ok:
            _invalidate()
        parts = [f"{n_ok} matrix imported." if n_ok == 1 else f"{n_ok} matrices imported."]
        for e in errors:
            parts.append(f"  ✗ {e['filename']}: {e['reason']}")
        _import_msg.set("\n".join(parts))

    @output
    @render.ui
    def mm_import_result():
        msg = _import_msg()
        if not msg:
            return None
        lines = msg.split("\n")
        ok = lines[0] if lines else ""
        errs = lines[1:]
        color = "success" if not errs else ("warning" if ok.startswith("0") is False else "danger")
        return ui.div(
            ui.tags.span(ok, class_=f"text-{color} small d-block"),
            *[ui.tags.span(e, class_="text-danger small d-block") for e in errs],
            class_="mt-1",
        )

    # ---- Top-level view (login wall or full layout) ----------------------

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
                ui.hr(),
                ui.h6("Import matrices"),
                ui.input_file(
                    "mm_import_files", None,
                    accept=[".json", ".zip"],
                    multiple=True,
                    placeholder="Select .json or .zip",
                ),
                ui.input_action_button("mm_import_btn", "Import",
                                       class_="btn-primary btn-sm w-100"),
                ui.output_ui("mm_import_result"),
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
                        ui.input_action_button("mm_add_stage", "+ Add",
                                                class_="btn btn-outline-primary btn-sm"),
                        col_widths=[8, 4],
                    ),
                    ui.output_ui("mm_stage_tags"),
                    ui.tags.div("Matrix A", class_="section-label"),
                    ui.output_ui("mm_matrix_grid"),
                    ui.tags.div("Matrix U", class_="section-label"),
                    ui.output_ui("mm_matrix_u_grid"),
                    ui.tags.div("Matrix F", class_="section-label"),
                    ui.output_ui("mm_matrix_f_grid"),
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
