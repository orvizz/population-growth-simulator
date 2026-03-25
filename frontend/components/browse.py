"""Browse matrices tab — search and inspect COMPADRE/custom matrices (public)."""
import html as _html
from shiny import reactive, render, ui
from components.shared import matrix_to_html, matrix_to_svg
from .utils import api


def browse_ui():
    return ui.nav_panel(
        "Browse matrices",
        ui.layout_sidebar(
            ui.sidebar(
                ui.tags.div("Search", class_="section-label"),
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
                ui.tags.div("Results", class_="section-label"),
                ui.output_ui("browse_matrix_selector"),
            ),
            ui.card(
                ui.card_header(
                    ui.tags.div(
                        ui.tags.span("Matrix detail"),
                        ui.input_switch("browse_graph_static", "Static view", value=False),
                        style="display:flex; justify-content:space-between; align-items:center; width:100%",
                    )
                ),
                ui.output_ui("browse_matrix_detail"),
                full_screen=True,
            ),
        ),
    )





def browse_server(input, output, session, *, token):
    results_cache = reactive.value([])

    @reactive.effect
    def _load_default():
        try:
            rows = api("GET", "/v1/matrices", params={"source_type": "compadre", "limit": 15}, token=None)
            if rows:
                results_cache.set(rows)
        except ValueError:
            pass

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
        first_id = next(iter(choices), None)
        return ui.input_select("browse_selected_id", None, choices=choices, size=15, selected=first_id)
    @output
    @render.ui
    def browse_card_header():
        mid = getattr(input, "browse_selected_id", lambda: None)()
        if not mid:
            return ui.card_header("Matrix detail")
        return ui.card_header(
            ui.tags.div(
                ui.tags.span("Matrix detail"),
                ui.input_switch("browse_graph_static", "Static view",
    value=False),
                style="display:flex; justify-content:space-between;    align-items:center;",
            )
        )
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
                ui.tags.pre(rows_txt, class_="matrix-display"),
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

        # Build graph tabs only for matrices that exist
        stage_names = m.get("stage_names") or []
        use_static = getattr(input, "browse_graph_static", lambda: False)()

        def _labels(mat):
            n = len(mat)
            return [stage_names[i] if i < len(stage_names) else f"Stage {i+1}" for i in range(n)]

        def _graph_tab(mat, label, fecundity_rows=None):
            if not mat:
                return None
            lbl = _labels(mat)
            if use_static:
                svg = matrix_to_svg(mat, lbl, title=label, fecundity_rows=fecundity_rows)
                content = ui.HTML(f'<div style="width:100%;overflow:auto;">{svg}</div>')
            else:
                graph_html = matrix_to_html(mat, lbl, title=label, height="440px", fecundity_rows=fecundity_rows)
                iframe = f'<iframe srcdoc="{_html.escape(graph_html)}" width="100%" height="460px" frameborder="0" style="border:none;"></iframe>'
                content = ui.HTML(iframe)
            return ui.nav_panel(label, content)

        n = len(m["matrix_a"]) if m.get("matrix_a") else 0
        graph_tabs = [t for t in [
            _graph_tab(m.get("matrix_a"), "Matrix A"),
            _graph_tab(m.get("matrix_u"), "Matrix U"),
            _graph_tab(m.get("matrix_f"), "Matrix F", fecundity_rows=list(range(n)) if n else None),
        ] if t is not None]

        species_name_text = m.get("species_accepted") or f"Matrix #{m['id']}"
        header = ui.tags.div(
            ui.tags.span(species_name_text, style="font-size:20px;font-weight:700;letter-spacing:-0.3px;margin-bottom:4px"),
            badge,
        )
        left_col = ui.div(
            header,
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
        right_col = ui.navset_tab(*graph_tabs) if graph_tabs else ui.p("No matrix data available.", class_="text-muted")

        return ui.layout_columns(left_col, right_col, col_widths=[5, 7])
