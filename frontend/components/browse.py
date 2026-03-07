"""Browse matrices tab — search and inspect COMPADRE/custom matrices (public)."""
from shiny import reactive, render, ui

from .utils import api


def browse_ui():
    return ui.nav_panel(
        "Browse matrices",
        ui.layout_sidebar(
            ui.sidebar(
                ui.h6("Filters"),
                ui.input_text("browse_species", "Species", placeholder="e.g. Abies"),
                ui.input_select(
                    "browse_kingdom", "Kingdom",
                    choices={"": "All kingdoms", "Plantae": "Plantae",
                             "Animalia": "Animalia", "Fungi": "Fungi", "Chromista": "Chromista"},
                ),
                ui.input_select(
                    "browse_source", "Source",
                    choices={"": "All sources", "compadre": "COMPADRE", "custom": "Custom"},
                ),
                ui.input_numeric("browse_limit", "Max results", value=100, min=1, max=200),
                ui.input_action_button("browse_search_btn", "Search", class_="btn-primary w-100 mt-1"),
                ui.hr(),
                ui.h6("Select a matrix"),
                ui.output_ui("browse_matrix_selector"),
            ),
            ui.card(
                ui.card_header("Matrix detail"),
                ui.output_ui("browse_matrix_detail"),
                full_screen=True,
            ),
        ),
    )


def browse_server(input, output, session, *, token):
    results_cache = reactive.value([])

    @reactive.effect
    @reactive.event(input.browse_search_btn)
    def _do_search():
        params = {"limit": input.browse_limit()}
        if input.browse_species():
            params["species"] = input.browse_species()
        if input.browse_kingdom():
            params["kingdom"] = input.browse_kingdom()
        if input.browse_source():
            params["source_type"] = input.browse_source()
        try:
            results_cache.set(api("GET", "/v1/matrices", params=params, token=token()))
        except ValueError:
            results_cache.set([])

    @output
    @render.ui
    def browse_matrix_selector():
        rows = results_cache()
        if not rows:
            return ui.p("Run a search to see results.", class_="text-muted small")
        choices = {
            str(m["id"]): (m.get("species_accepted") or f"Matrix #{m['id']}")
            for m in rows
        }
        return ui.input_select("browse_selected_id", None, choices=choices, size=15)

    @output
    @render.ui
    def browse_matrix_detail():
        mid = getattr(input, "browse_selected_id", lambda: None)()
        if not mid:
            return ui.p("Select a matrix from the list.", class_="text-muted")
        try:
            m = api("GET", f"/v1/matrices/{mid}", token=token())
        except ValueError as e:
            return ui.div(ui.tags.span(str(e), class_="text-danger"))

        badge = ui.tags.span(
            m["source_type"],
            class_="badge bg-success ms-2" if m["source_type"] == "compadre" else "badge bg-primary ms-2",
        )

        def _fmt_matrix(mat, label):
            if not mat:
                return ui.div(ui.h6(label), ui.p("Not available", class_="text-muted small"))
            rows_txt = "\n".join(
                "  " + "  ".join(f"{v:7.4f}" if v is not None else "   null" for v in row)
                for row in mat
            )
            return ui.div(
                ui.h6(label),
                ui.tags.pre(rows_txt, class_="small bg-light p-2 rounded border"),
            )

        meta_rows = [
            ("Species", m.get("species_accepted") or "—"),
            ("Common name", m.get("common_name") or "—"),
            ("Kingdom", m.get("kingdom") or "—"),
            ("Country", m.get("country_code") or "—"),
            ("Dimension", f"{len(m['matrix_a'])}×{len(m['matrix_a'])}" if m.get("matrix_a") else "—"),
            ("Stages", ", ".join(m["stage_names"]) if m.get("stage_names") else "—"),
            ("Owner ID", str(m.get("owner_id")) if m.get("owner_id") else "public"),
        ]

        return ui.div(
            ui.h5(m.get("species_accepted") or f"Matrix #{m['id']}", badge),
            ui.tags.table(
                ui.tags.tbody(
                    *[ui.tags.tr(
                        ui.tags.th(k, class_="text-end pe-3 text-muted small fw-normal", style="width:120px"),
                        ui.tags.td(v, class_="small"),
                    ) for k, v in meta_rows]
                ),
                class_="table table-sm mb-3",
            ),
            _fmt_matrix(m.get("matrix_a"), "Matrix A — projection"),
            _fmt_matrix(m.get("matrix_u"), "Matrix U — survival / growth"),
            _fmt_matrix(m.get("matrix_f"), "Matrix F — fecundity"),
        )
