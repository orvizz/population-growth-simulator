"""Browse matrices tab — paginated vertical list + detail view."""
import html as _html
import math
import re as _re

import httpx
from shiny import reactive, render, ui
from components.shared import matrix_to_html, matrix_to_svg
from .utils import API_BASE, api

_DETAIL_RE = _re.compile(r"^/matrices/(\d+)$")
print("[browse] module loaded")


def browse_ui(tr):
    return ui.nav_panel(
        tr("nav.browse_matrices"),
        ui.output_ui("browse_content"),
        value="browse",
    )


def browse_server(input, output, session, *, token, tr):
    # ---- Reactive state --------------------------------------------------

    _search_params = reactive.value({})
    page_size      = reactive.value(20)
    current_page   = reactive.value(1)
    current_rows   = reactive.value([])
    has_next       = reactive.value(False)
    total_count    = reactive.value(0)

    view_mode   = reactive.value("list")
    selected_id = reactive.value(None)
    _url_synced = reactive.value(False)

    # Persist filter/pagination inputs across list↔detail re-renders
    _species_val  = reactive.value("")
    _kingdom_val  = reactive.value("")
    _source_val   = reactive.value("")
    _per_page_val = reactive.value("20")

    # ---- Initialize view mode from browser URL (clientdata arrives before JS) ---

    @reactive.effect
    def _init_from_url():
        path = input[".clientdata_url_pathname"]() or "/"
        print(f"[browse] _init_from_url: path={path!r}")
        m = _DETAIL_RE.match(path)
        if m:
            print(f"[browse] _init_from_url: matched detail id={m.group(1)!r}")
            selected_id.set(m.group(1))
            view_mode.set("detail")
            _url_synced.set(True)

    # ---- Navigation (atomic: both mode and id set in one flush) ----------

    @reactive.effect
    @reactive.event(input.browse_nav)
    def _sync_nav():
        nav = input.browse_nav()
        print(f"[browse] _sync_nav fired: nav={nav!r}")
        if not nav:
            return
        _url_synced.set(True)
        mode = nav.get("mode", "list")
        mid  = nav.get("id")
        if mode == "detail" and mid:
            selected_id.set(str(mid))
            view_mode.set("detail")
        else:
            view_mode.set("list")

    # ---- Filter persistence ----------------------------------------------

    @reactive.effect
    @reactive.event(input.browse_species)
    def _save_species():
        _species_val.set(input.browse_species())

    @reactive.effect
    @reactive.event(input.browse_kingdom)
    def _save_kingdom():
        _kingdom_val.set(input.browse_kingdom())

    @reactive.effect
    @reactive.event(input.browse_source)
    def _save_source():
        _source_val.set(input.browse_source())

    # ---- Data fetching ---------------------------------------------------

    @reactive.effect
    def _fetch_page():
        if view_mode() == "detail":
            return
        ps   = page_size()
        sp   = _search_params()
        page = current_page()
        params = {"limit": ps + 1, "skip": (page - 1) * ps}
        params.update(sp)
        try:
            rows = api("GET", "/v1/matrices", params=params, token=token())
            has_next.set(len(rows) > ps)
            current_rows.set(rows[:ps])
        except ValueError:
            current_rows.set([])
            has_next.set(False)

    @reactive.effect
    def _fetch_count():
        if view_mode() == "detail":
            return
        sp = _search_params()
        try:
            result = api("GET", "/v1/matrices/count", params=sp, token=token())
            total_count.set(result.get("total", 0))
        except ValueError:
            total_count.set(0)

    # ---- Search ----------------------------------------------------------

    @reactive.effect
    @reactive.event(input.browse_search_btn)
    def _do_search():
        sp = {}
        if input.browse_species(): sp["species"]     = input.browse_species()
        if input.browse_kingdom(): sp["kingdom"]     = input.browse_kingdom()
        if input.browse_source():  sp["source_type"] = input.browse_source()
        _search_params.set(sp)
        current_page.set(1)

    # ---- Pagination ------------------------------------------------------

    @reactive.effect
    @reactive.event(input.browse_page_first)
    def _first_page():
        if not input.browse_page_first():
            return
        current_page.set(1)

    @reactive.effect
    @reactive.event(input.browse_page_prev)
    def _prev_page():
        if not input.browse_page_prev():
            return
        current_page.set(max(1, current_page() - 1))

    @reactive.effect
    @reactive.event(input.browse_page_next)
    def _next_page():
        if not input.browse_page_next():
            return
        if has_next():
            current_page.set(current_page() + 1)

    @reactive.effect
    @reactive.event(input.browse_page_last)
    def _last_page():
        if not input.browse_page_last():
            return
        ps = page_size()
        tc = total_count()
        total_pages = math.ceil(tc / ps) if tc > 0 else 1
        current_page.set(total_pages)

    @reactive.effect
    @reactive.event(input.browse_page_input)
    def _go_to_page():
        p = input.browse_page_input()
        if p is None:
            return
        ps = page_size()
        tc = total_count()
        total_pages = math.ceil(tc / ps) if tc > 0 else 1
        new_page = max(1, min(int(p), total_pages))
        if new_page != current_page():
            current_page.set(new_page)

    @reactive.effect
    @reactive.event(input.browse_per_page)
    def _change_per_page():
        _per_page_val.set(input.browse_per_page())
        page_size.set(int(input.browse_per_page()))
        current_page.set(1)

    # ---- URL sync --------------------------------------------------------

    @reactive.effect
    async def _push_browse_url():
        if not _url_synced():
            return
        mode = view_mode()
        mid  = selected_id()
        if mode == "detail" and mid:
            await session.send_custom_message("browse_push_route", f"/matrices/{mid}")
        elif mode == "list":
            await session.send_custom_message("browse_push_route", "/matrices")

    # ---- Export downloads ------------------------------------------------

    def _selected_species_name():
        mid = selected_id()
        if not mid:
            return "matrix"
        for m in current_rows():
            if str(m["id"]) == str(mid):
                return (m.get("species_accepted") or f"matrix_{mid}").replace(" ", "_")
        return f"matrix_{mid}"

    @render.download(filename=lambda: f"{_selected_species_name()}.json")
    def browse_export_json():
        mid = selected_id()
        if not mid:
            yield b""
            return
        t = token()
        headers = {"Authorization": f"Bearer {t}"} if t else {}
        try:
            r = httpx.get(f"{API_BASE}/v1/matrices/{mid}/export", headers=headers, timeout=10)
            r.raise_for_status()
            yield r.content
        except Exception:
            yield b""

    @render.download(filename=lambda: f"{_selected_species_name()}.csv")
    def browse_export_csv():
        mid = selected_id()
        if not mid:
            yield b""
            return
        t = token()
        headers = {"Authorization": f"Bearer {t}"} if t else {}
        try:
            r = httpx.get(f"{API_BASE}/v1/matrices/{mid}/export?format=csv", headers=headers, timeout=10)
            r.raise_for_status()
            yield r.content
        except Exception:
            yield b""

    # ---- Rendering helpers -----------------------------------------------

    def _make_row(m):
        mid       = str(m["id"])
        species   = m.get("species_accepted") or f"Matrix #{mid}"
        common    = m.get("common_name") or ""
        kingdom   = m.get("kingdom") or ""
        source    = m.get("source_type") or ""
        country   = m.get("country_code") or ""
        badge_cls = "badge bg-success" if source == "compadre" else "badge bg-primary"
        click_js  = (
            f"Shiny.setInputValue('browse_nav',"
            f"{{mode:'detail',id:'{mid}'}},"
            f"{{priority:'event'}});"
        )
        return ui.tags.div(
            ui.tags.div(
                ui.tags.span(species, class_="browse-row-species"),
                ui.tags.span(common, class_="browse-row-common") if common else ui.tags.span(),
                class_="browse-row-main",
            ),
            ui.tags.div(
                ui.tags.span(kingdom, class_="badge bg-secondary me-1") if kingdom else ui.tags.span(),
                ui.tags.span(source, class_=badge_cls + " me-1"),
                ui.tags.span(country, class_="browse-row-country") if country else ui.tags.span(),
                class_="browse-row-meta",
            ),
            class_="browse-matrix-row",
            onclick=click_js,
        )

    def _render_list_ui():
        rows  = current_rows()
        page  = current_page()
        ps    = page_size()
        tc    = total_count()
        total_pages = math.ceil(tc / ps) if tc > 0 else 1

        search_bar = ui.div(
            ui.input_text("browse_species", None,
                          placeholder=tr("browse.species_placeholder"),
                          value=_species_val()),
            ui.input_select("browse_kingdom", None,
                            choices={"": tr("browse.all_kingdoms"),
                                     "Plantae": "Plantae", "Animalia": "Animalia",
                                     "Fungi": "Fungi", "Chromista": "Chromista"},
                            selected=_kingdom_val()),
            ui.input_select("browse_source", None,
                            choices={"": tr("browse.all_sources"),
                                     "compadre": "COMPADRE", "custom": "Custom"},
                            selected=_source_val()),
            ui.input_action_button("browse_search_btn", tr("browse.search_btn"),
                                   class_="btn-primary"),
            class_="browse-search-bar",
        )

        count_bar = ui.div(
            ui.tags.span(
                tr("browse.result_count", count=tc) if tc > 0 else "",
                class_="browse-result-count",
            ),
            class_="browse-count-bar",
        )

        list_body = ui.div(
            *[_make_row(m) for m in rows],
            class_="browse-matrix-list",
        ) if rows else ui.p(tr("browse.run_search"), class_="text-muted p-3")

        pagination = ui.div(
            ui.input_action_button("browse_page_first", tr("browse.first_page"),
                                   class_="btn btn-outline-secondary btn-sm browse-page-btn",
                                   disabled=(page <= 1)),
            ui.input_action_button("browse_page_prev", tr("browse.prev_page"),
                                   class_="btn btn-outline-secondary btn-sm browse-page-btn",
                                   disabled=(page <= 1)),
            ui.tags.span(tr("browse.page_label"), class_="browse-page-label"),
            ui.input_numeric("browse_page_input", None, value=page,
                             min=1, max=total_pages, step=1, width="60px"),
            ui.tags.span(f"/ {total_pages}", class_="browse-page-of"),
            ui.input_action_button("browse_page_next", tr("browse.next_page"),
                                   class_="btn btn-outline-secondary btn-sm browse-page-btn",
                                   disabled=(not has_next())),
            ui.input_action_button("browse_page_last", tr("browse.last_page"),
                                   class_="btn btn-outline-secondary btn-sm browse-page-btn",
                                   disabled=(page >= total_pages)),
            ui.tags.span(tr("browse.per_page"), class_="browse-per-page-label ms-4"),
            ui.input_select("browse_per_page", None,
                            choices={"10": "10", "20": "20", "50": "50", "100": "100"},
                            selected=_per_page_val()),
            class_="browse-pagination",
        ) if rows else ui.div()

        return ui.div(search_bar, count_bar, list_body, pagination, class_="browse-list-view")

    def _build_detail_panel(mid):
        print(f"Building detail panel for matrix ID: {mid}")
        try:
            m = api("GET", f"/v1/matrices/{mid}", token=token())
            print(f"Retrieved matrix: {m}")
        except ValueError as e:
            return ui.div(ui.tags.span(str(e), class_="text-danger p-3"))

        badge = ui.tags.span(
            m["source_type"],
            class_="badge bg-success ms-2" if m["source_type"] == "compadre" else "badge bg-primary ms-2",
        )

        def _fmt_matrix(mat, label):
            if not mat:
                return ui.div(ui.h6(label), ui.p(tr("browse.not_available"), class_="text-muted small"))
            rows_txt = "\n".join(
                "  " + "  ".join(f"{v:7.4f}" if v is not None else "   null" for v in row)
                for row in mat
            )
            return ui.div(
                ui.h6(label),
                ui.tags.pre(rows_txt, class_="matrix-display"),
            )

        print("[browse] building meta_rows")
        meta_rows = [
            (tr("browse.species_meta"), m.get("species_accepted") or "—"),
            (tr("browse.common_name"), m.get("common_name") or "—"),
            (tr("browse.kingdom_meta"), m.get("kingdom") or "—"),
            (tr("browse.country"), m.get("country_code") or "—"),
            (tr("browse.dimension"), f"{len(m['matrix_a'])}×{len(m['matrix_a'])}" if m.get("matrix_a") else "—"),
            (tr("browse.stages"), ", ".join(m["stage_names"]) if m.get("stage_names") else "—"),
            (tr("browse.owner_id"), str(m.get("owner_id")) if m.get("owner_id") else tr("browse.public_owner")),
        ]

        stage_names = m.get("stage_names") or []
        try:
            use_static = bool(input.browse_graph_static())
        except Exception:
            use_static = False

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
            _graph_tab(m.get("matrix_a"), tr("browse.matrix_a")),
            _graph_tab(m.get("matrix_u"), tr("browse.matrix_u")),
            _graph_tab(m.get("matrix_f"), tr("browse.matrix_f"),
                       fecundity_rows=list(range(n)) if n else None),
        ] if t is not None]

        species_name_text = m.get("species_accepted") or f"Matrix #{m['id']}"
        header = ui.tags.div(
            ui.tags.span(species_name_text,
                         style="font-size:20px;font-weight:700;letter-spacing:-0.3px;margin-bottom:4px"),
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
                class_="table table-sm mb-2",
            ),
            ui.div(
                ui.download_button("browse_export_json", tr("browse.export_json"),
                                   class_="btn-sm btn-outline-primary me-1"),
                ui.download_button("browse_export_csv", tr("browse.export_csv"),
                                   class_="btn-sm btn-outline-secondary"),
                class_="mb-3",
            ),
            _fmt_matrix(m.get("matrix_a"), tr("browse.matrix_a_long")),
            _fmt_matrix(m.get("matrix_u"), tr("browse.matrix_u_long")),
            _fmt_matrix(m.get("matrix_f"), tr("browse.matrix_f_long")),
        )
        right_col = (ui.navset_tab(*graph_tabs) if graph_tabs
                     else ui.p(tr("browse.no_matrix_data"), class_="text-muted"))

        card_header = ui.card_header(
            ui.tags.div(
                ui.tags.span(tr("browse.matrix_detail")),
                ui.input_switch("browse_graph_static", tr("browse.static_view"), value=False),
                style="display:flex;justify-content:space-between;align-items:center;width:100%",
            )
        )
        return ui.card(
            card_header,
            ui.layout_columns(left_col, right_col, col_widths=[5, 7]),
            full_screen=True,
        )

    def _render_detail_ui():
        back_js = "Shiny.setInputValue('browse_nav',{mode:'list',id:null},{priority:'event'});"
        back_btn = ui.div(
            ui.tags.button(
                "← " + tr("browse.back_to_results"),
                onclick=back_js,
                class_="btn btn-outline-secondary btn-sm browse-back-btn",
            ),
            class_="browse-detail-header",
        )
        mid = selected_id()
        synced = _url_synced()
        print(f"[browse] _render_detail_ui: mid={mid!r} synced={synced!r}")
        if not mid:
            return ui.div(back_btn, ui.p(tr("browse.select_matrix"), class_="text-muted p-3"))
        return ui.div(back_btn, _build_detail_panel(mid), class_="browse-detail-view")

    # ---- Main output ------------------------------------------------------

    @output
    @render.ui
    def browse_content():
        mode = view_mode()
        print(f"[browse] browse_content: mode={mode!r}")
        if mode == "detail":
            return _render_detail_ui()
        return _render_list_ui()
