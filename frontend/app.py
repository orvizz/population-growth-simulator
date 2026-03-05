"""
Population Growth Simulator — Shiny frontend.

Consumes the FastAPI backend at API_BASE (default: http://localhost:8000).
The frontend never touches the database directly; all data flows through the API.

Run with:
    cd frontend
    python -m shiny run app.py --reload --port 8080
"""
import os

import httpx
from shiny import App, reactive, render, req, ui

API_BASE = os.environ.get("API_BASE_URL", "http://localhost:8000")


# ---------------------------------------------------------------------------
# HTTP helper
# ---------------------------------------------------------------------------

def api(method: str, path: str, *, token: str | None = None, **kwargs):
    headers = {"Authorization": f"Bearer {token}"} if token else {}
    try:
        r = httpx.request(method, f"{API_BASE}{path}", headers=headers, timeout=10, **kwargs)
        r.raise_for_status()
        return r.json()
    except httpx.HTTPStatusError as e:
        try:
            detail = e.response.json().get("detail", str(e))
        except Exception:
            detail = str(e)
        raise ValueError(detail)
    except httpx.RequestError:
        raise ValueError("Cannot reach the API — is the backend running?")


# ---------------------------------------------------------------------------
# UI
# ---------------------------------------------------------------------------

app_ui = ui.page_navbar(

    # -----------------------------------------------------------------------
    # Browse tab
    # -----------------------------------------------------------------------
    ui.nav_panel(
        "Browse matrices",
        ui.layout_sidebar(
            ui.sidebar(
                ui.h6("Filters"),
                ui.input_text("species_q", "Species", placeholder="e.g. Abies"),
                ui.input_select(
                    "kingdom_q", "Kingdom",
                    choices={"": "All kingdoms", "Plantae": "Plantae",
                             "Animalia": "Animalia", "Fungi": "Fungi", "Chromista": "Chromista"},
                ),
                ui.input_select(
                    "source_q", "Source",
                    choices={"": "All sources", "compadre": "COMPADRE", "custom": "Custom"},
                ),
                ui.input_numeric("limit_q", "Max results", value=100, min=1, max=200),
                ui.input_action_button("search_btn", "Search", class_="btn-primary w-100 mt-1"),
                ui.hr(),
                ui.h6("Select a matrix"),
                ui.output_ui("matrix_selector"),
            ),
            ui.card(
                ui.card_header("Matrix detail"),
                ui.output_ui("matrix_detail"),
                full_screen=True,
            ),
        ),
    ),

    # -----------------------------------------------------------------------
    # My matrices tab
    # -----------------------------------------------------------------------
    ui.nav_panel(
        "My matrices",
        ui.output_ui("auth_gate"),
    ),

    # -----------------------------------------------------------------------
    # Account tab
    # -----------------------------------------------------------------------
    ui.nav_panel(
        "Account",
        ui.layout_columns(
            ui.card(
                ui.card_header("Login"),
                ui.input_text("login_user", "Username"),
                ui.input_password("login_pass", "Password"),
                ui.input_action_button("login_btn", "Login", class_="btn-primary w-100 mt-2"),
                ui.output_ui("login_msg"),
            ),
            ui.card(
                ui.card_header("Register new account"),
                ui.input_text("reg_user", "Username"),
                ui.input_text("reg_email", "Email"),
                ui.input_password("reg_pass", "Password (min 8 characters)"),
                ui.input_action_button("reg_btn", "Register", class_="btn-success w-100 mt-2"),
                ui.output_ui("reg_msg"),
            ),
            col_widths=[6, 6],
        ),
        ui.card(
            ui.card_header("Current session"),
            ui.output_ui("session_status"),
        ),
    ),

    title="Population Growth Simulator",
    bg="#1a252f",
    inverse=True,
)


# ---------------------------------------------------------------------------
# Server
# ---------------------------------------------------------------------------

def server(input, output, session):

    # ---- Shared reactive state --------------------------------------------
    token = reactive.value(None)
    username = reactive.value(None)
    # Cache of last search results: list[dict]
    results_cache = reactive.value([])

    # ---- Auth -------------------------------------------------------------

    @reactive.effect
    @reactive.event(input.login_btn)
    def _do_login():
        try:
            data = api("POST", "/v1/auth/login", data={
                "username": input.login_user(),
                "password": input.login_pass(),
            })
            token.set(data["access_token"])
            username.set(input.login_user())
        except ValueError:
            token.set(None)
            username.set(None)

    @reactive.effect
    @reactive.event(input.logout_btn)
    def _do_logout():
        token.set(None)
        username.set(None)

    @reactive.effect
    @reactive.event(input.reg_btn)
    def _do_register():
        # Validation is done by the API; we just surface the result
        try:
            api("POST", "/v1/auth/register", json={
                "username": input.reg_user(),
                "email": input.reg_email(),
                "password": input.reg_pass(),
            })
        except ValueError:
            pass

    @output
    @render.ui
    def login_msg():
        input.login_btn()
        if input.login_btn() == 0:
            return None
        if username():
            return ui.div(
                ui.tags.span(f"Logged in as {username()}", class_="text-success"),
                class_="mt-2",
            )
        return ui.div(ui.tags.span("Login failed — check credentials.", class_="text-danger"), class_="mt-2")

    @output
    @render.ui
    def reg_msg():
        input.reg_btn()
        if input.reg_btn() == 0:
            return None
        # Reflect last state — real call happened in _do_register
        return ui.div(
            ui.tags.span(
                "Registration successful — you can now log in.",
                class_="text-success",
            ),
            class_="mt-2",
        )

    @output
    @render.ui
    def session_status():
        if username():
            return ui.div(
                ui.p(f"Signed in as: ", ui.tags.b(username())),
                ui.input_action_button("logout_btn", "Log out", class_="btn-outline-secondary btn-sm"),
            )
        return ui.p("Not signed in.", class_="text-muted")

    # ---- Browse -----------------------------------------------------------

    @reactive.effect
    @reactive.event(input.search_btn)
    def _do_search():
        params = {"limit": input.limit_q()}
        if input.species_q():
            params["species"] = input.species_q()
        if input.kingdom_q():
            params["kingdom"] = input.kingdom_q()
        if input.source_q():
            params["source_type"] = input.source_q()
        try:
            results_cache.set(api("GET", "/v1/matrices", params=params))
        except ValueError:
            results_cache.set([])

    @output
    @render.ui
    def matrix_selector():
        rows = results_cache()
        if not rows:
            return ui.p("Run a search to see results.", class_="text-muted small")
        choices = {
            str(m["id"]): (m.get("species_accepted") or f"Matrix #{m['id']}")
            for m in rows
        }
        return ui.input_select("selected_matrix_id", None, choices=choices, size=15)

    @output
    @render.ui
    def matrix_detail():
        req(input.selected_matrix_id())
        try:
            m = api("GET", f"/v1/matrices/{input.selected_matrix_id()}")
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

    # ---- My matrices ------------------------------------------------------

    my_matrices_cache = reactive.value([])
    edit_msg = reactive.value(None)
    create_msg = reactive.value(None)

    @reactive.calc
    def _my_matrices():
        """Fetch user's custom matrices. Re-runs when token changes."""
        t = token()
        if not t:
            return []
        try:
            return api("GET", "/v1/matrices", params={"source_type": "custom"}, token=t)
        except ValueError:
            return []

    @output
    @render.ui
    def auth_gate():
        if not username():
            return ui.card(
                ui.card_header("My matrices"),
                ui.p("Please log in from the Account tab to manage your matrices.", class_="text-muted p-3"),
            )

        matrices = _my_matrices()
        choices = {str(m["id"]): (m.get("species_accepted") or f"Matrix #{m['id']}") for m in matrices}

        return ui.layout_sidebar(
            ui.sidebar(
                ui.h6("Your matrices"),
                ui.input_select("my_matrix_id", None, choices=choices, size=10)
                if choices else ui.p("No custom matrices yet.", class_="text-muted small"),
            ),
            ui.layout_columns(
                # Create card
                ui.card(
                    ui.card_header("Create matrix"),
                    ui.input_text("new_species", "Species name"),
                    ui.input_text("new_common", "Common name (optional)"),
                    ui.input_select(
                        "new_kingdom", "Kingdom",
                        choices={"": "—", "Plantae": "Plantae", "Animalia": "Animalia",
                                 "Fungi": "Fungi", "Chromista": "Chromista"},
                    ),
                    ui.input_text("new_country", "Country code", placeholder="ESP"),
                    ui.input_text(
                        "new_stages", "Stages (comma-separated)",
                        placeholder="seedling, juvenile, adult",
                    ),
                    ui.input_text_area(
                        "new_matrix_a",
                        "Matrix A  (rows separated by ';', values by ',')",
                        placeholder="0.0,1.2,3.4; 0.5,0.0,0.0; 0.0,0.3,0.7",
                        rows=3,
                    ),
                    ui.input_action_button("create_btn", "Create", class_="btn-success w-100 mt-2"),
                    ui.output_ui("create_result"),
                ),
                # Edit card
                ui.card(
                    ui.card_header("Edit selected matrix"),
                    ui.output_ui("edit_form"),
                ),
                col_widths=[6, 6],
            ),
        )

    @output
    @render.ui
    def create_result():
        input.create_btn()
        msg = create_msg()
        if msg:
            color = "success" if "success" in msg.lower() or "created" in msg.lower() else "danger"
            return ui.div(ui.tags.span(msg, class_=f"text-{color}"), class_="mt-2 small")

    @reactive.effect
    @reactive.event(input.create_btn)
    def _do_create():
        req(token())
        raw = input.new_matrix_a().strip()
        if not raw:
            create_msg.set("Matrix A is required.")
            return
        try:
            matrix_a = [
                [float(v.strip()) for v in row.split(",")]
                for row in raw.split(";")
                if row.strip()
            ]
        except ValueError:
            create_msg.set("Invalid matrix format. Use rows separated by ';', values by ','.")
            return

        stages_raw = input.new_stages().strip()
        stage_names = [s.strip() for s in stages_raw.split(",") if s.strip()] or None

        try:
            api("POST", "/v1/matrices", token=token(), json={
                "species_accepted": input.new_species() or None,
                "common_name": input.new_common() or None,
                "kingdom": input.new_kingdom() or None,
                "country_code": input.new_country() or None,
                "matrix_a": matrix_a,
                "stage_names": stage_names,
            })
            create_msg.set("Matrix created successfully.")
            reactive.invalidate_later(0)  # trigger re-render
        except ValueError as e:
            create_msg.set(str(e))

    @output
    @render.ui
    def edit_form():
        mid = input.my_matrix_id() if hasattr(input, "my_matrix_id") else None
        if not mid:
            return ui.p("Select a matrix from the list to edit it.", class_="text-muted")
        try:
            m = api("GET", f"/v1/matrices/{mid}")
        except ValueError as e:
            return ui.p(str(e), class_="text-danger")

        return ui.div(
            ui.p(ui.tags.b("Editing: "), m.get("species_accepted") or f"Matrix #{mid}"),
            ui.input_text("edit_common", "Common name", value=m.get("common_name") or ""),
            ui.input_text("edit_country", "Country code", value=m.get("country_code") or ""),
            ui.input_action_button("save_btn", "Save changes", class_="btn-warning w-100 mt-2"),
            ui.output_ui("edit_result"),
        )

    @output
    @render.ui
    def edit_result():
        input.save_btn() if hasattr(input, "save_btn") else None
        msg = edit_msg()
        if msg:
            color = "success" if "saved" in msg.lower() or "updated" in msg.lower() else "danger"
            return ui.div(ui.tags.span(msg, class_=f"text-{color}"), class_="mt-2 small")

    @reactive.effect
    @reactive.event(input.save_btn)
    def _do_edit():
        req(token())
        mid = input.my_matrix_id()
        req(mid)
        try:
            api("PATCH", f"/v1/matrices/{mid}", token=token(), json={
                "common_name": input.edit_common() or None,
                "country_code": input.edit_country() or None,
            })
            edit_msg.set("Changes saved.")
        except ValueError as e:
            edit_msg.set(str(e))


app = App(app_ui, server)
