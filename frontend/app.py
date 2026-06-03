"""
Population Growth Simulator — Shiny frontend entry point.

Run with:
    cd frontend
    python -m shiny run app.py --reload --port 8888
"""
import urllib.parse as _urlparse
from pathlib import Path

from shiny import App, reactive, ui
from starlette.requests import Request

from components.account import account_server
from components.browse import browse_server, browse_ui
from components.my_matrices import my_matrices_server, my_matrices_ui
from components.quasi_extinction import qe_server, qe_ui
from components.simulate import simulate_server, simulate_ui
from i18ntranslator import get_translator, SUPPORTED_LANGUAGES, DEFAULT_LANGUAGE

# ---- SPA Middleware -------------------------------------------------------
# Rewrites known tab paths to "/" so Shiny always serves from root.
# Uses raw ASGI (not BaseHTTPMiddleware) to avoid breaking WebSocket upgrades.
#
# Two rewrites are needed:
#   HTTP GET  /simulate          → /
#   WebSocket /simulate/websocket/ → /websocket/
# Shiny's JS builds its WebSocket URL as <pathname>/websocket/ relative to the
# current window.location, so every route needs its WS path remapped too.

_ROUTES = {"/", "/matrices", "/simulate", "/my-matrices", "/quasi-extinction"}

_WS_ROUTES = {
    "/matrices/websocket/":          "/websocket/",
    "/simulate/websocket/":          "/websocket/",
    "/my-matrices/websocket/":       "/websocket/",
    "/quasi-extinction/websocket/":  "/websocket/",
}


class SPAMiddleware:
    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        path = scope.get("path", "")
        if scope["type"] == "http" and scope.get("method") == "GET" and path in _ROUTES:
            scope["path"] = "/"
        elif scope["type"] == "websocket" and path in _WS_ROUTES:
            scope["path"] = _WS_ROUTES[path]
        await self.app(scope, receive, send)


# ---- Client-side JS -------------------------------------------------------

_SESSION_JS = """
$(document).on('shiny:sessioninitialized', function () {
  // ---- Routing: activate the tab that matches the current URL path ----
  var pathMap = {
    '/matrices':          'browse',
    '/simulate':          'simulate',
    '/quasi-extinction':  'quasi-extinction',
    '/my-matrices':       'my-matrices',
  };
  var tab = pathMap[window.location.pathname];
  if (tab) {
    Shiny.setInputValue('route_path', tab, { priority: 'event' });
  }

  // ---- Session restore: re-hydrate auth token from localStorage --------
  var token    = localStorage.getItem('pgs_auth_token');
  var username = localStorage.getItem('pgs_auth_username');
  if (token && username) {
    Shiny.setInputValue(
      'restored_session',
      { token: token, username: username },
      { priority: 'event' }
    );
  }
});

// ---- URL sync: update the browser URL when the server switches tabs ----
Shiny.addCustomMessageHandler('push_route', function (path) {
  var langParam = new URLSearchParams(window.location.search).get('lang');
  if (langParam) path = path + '?lang=' + encodeURIComponent(langParam);
  history.pushState(null, '', path);
});

Shiny.addCustomMessageHandler('save_session', function (data) {
  if (data && data.token) {
    localStorage.setItem('pgs_auth_token',    data.token);
    localStorage.setItem('pgs_auth_username', data.username);
  } else {
    localStorage.removeItem('pgs_auth_token');
    localStorage.removeItem('pgs_auth_username');
  }
});
"""

# ---- Language switcher ---------------------------------------------------

def _lang_switcher(current_lang: str, tr) -> ui.Tag:
    options = []
    for code in SUPPORTED_LANGUAGES:
        label = tr(f"lang.{code}")
        selected = (code == current_lang)
        opt = ui.tags.option(label, value=code)
        if selected:
            opt = ui.tags.option(label, value=code, selected=True)
        options.append(opt)
    return ui.nav_control(
        ui.tags.select(
            *options,
            onchange=(
                "var p = window.location.pathname;"
                " window.location.href = p + '?lang=' + this.value;"
            ),
            class_="form-select form-select-sm",
            style="width:auto;min-width:90px;background-color:rgba(255,255,255,0.15);color:white;border-color:rgba(255,255,255,0.3);",
            title=tr(f"lang.{current_lang}"),
        )
    )


# ---- App UI --------------------------------------------------------------

def app_ui(request: Request):
    lang = request.query_params.get("lang", DEFAULT_LANGUAGE)
    if lang not in SUPPORTED_LANGUAGES:
        lang = DEFAULT_LANGUAGE
    tr = get_translator(lang)

    return ui.page_navbar(
        browse_ui(tr),
        simulate_ui(tr),
        qe_ui(tr),
        my_matrices_ui(tr),
        ui.nav_spacer(),
        _lang_switcher(lang, tr),
        ui.nav_control(ui.output_ui("navbar_auth_buttons")),
        ui.head_content(
            ui.include_css(Path(__file__).parent / "static/custom.css"),
            ui.tags.script(ui.HTML(_SESSION_JS)),
        ),
        id="main_nav",
        title=tr("title"),
        bg="#1a2e1a",
        inverse=True,
    )


# ---- Server --------------------------------------------------------------

def server(input, output, session):
    token    = reactive.value(None)
    username = reactive.value(None)

    @reactive.calc
    def _lang():
        qs = input[".clientdata_url_search"]() or ""
        params = _urlparse.parse_qs(qs.lstrip("?"))
        lang = params.get("lang", [DEFAULT_LANGUAGE])[0]
        return lang if lang in SUPPORTED_LANGUAGES else DEFAULT_LANGUAGE

    def _tr(key: str, **kwargs) -> str:
        return get_translator(_lang())(key, **kwargs)
    account_server(input, output, session, token=token, username=username, tr=_tr)
    browse_server(input, output, session, token=token, tr=_tr)
    my_matrices_server(input, output, session, token=token, username=username, tr=_tr)
    simulate_server(input, output, session, token=token, username=username, tr=_tr)
    qe_server(input, output, session, token=token, username=username, tr=_tr)

    # ---- Routing effects -------------------------------------------------

    @reactive.effect
    @reactive.event(input.route_path)
    def _apply_initial_route():
        """On page load: activate the tab matching the URL path."""
        ui.update_navset("main_nav", selected=input.route_path())

    @reactive.effect
    @reactive.event(input.main_nav)
    async def _push_route():
        """On tab change: push the corresponding path to the browser URL."""
        tab_to_path = {
            "browse":            "/matrices",
            "simulate":          "/simulate",
            "quasi-extinction":  "/quasi-extinction",
            "my-matrices":       "/my-matrices",
        }
        path = tab_to_path.get(input.main_nav(), "/")
        await session.send_custom_message("push_route", path)


# ---- ASGI app (wrapped with SPA middleware) ------------------------------

app = App(app_ui, server)
app = SPAMiddleware(app)
