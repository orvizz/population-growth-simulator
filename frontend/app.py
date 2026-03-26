"""
Population Growth Simulator — Shiny frontend entry point.

Run with:
    cd frontend
    python -m shiny run app.py --reload --port 8080
"""
from shiny import App, reactive, ui

from components.account import account_server
from components.browse import browse_server, browse_ui
from components.my_matrices import my_matrices_server, my_matrices_ui
from components.simulate import simulate_server, simulate_ui

# ---- SPA Middleware -------------------------------------------------------
# Rewrites known tab paths to "/" so Shiny always serves from root.
# Uses raw ASGI (not BaseHTTPMiddleware) to avoid breaking WebSocket upgrades.
#
# Two rewrites are needed:
#   HTTP GET  /simulate          → /
#   WebSocket /simulate/websocket/ → /websocket/
# Shiny's JS builds its WebSocket URL as <pathname>/websocket/ relative to the
# current window.location, so every route needs its WS path remapped too.

_ROUTES = {"/", "/matrices", "/simulate", "/my-matrices"}

_WS_ROUTES = {
    "/matrices/websocket/":    "/websocket/",
    "/simulate/websocket/":    "/websocket/",
    "/my-matrices/websocket/": "/websocket/",
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
    '/matrices':    'Browse matrices',
    '/simulate':    'Simulate',
    '/my-matrices': 'My matrices',
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

# ---- App UI --------------------------------------------------------------

app_ui = ui.page_navbar(
    browse_ui(),
    my_matrices_ui(),
    simulate_ui(),
    ui.nav_spacer(),
    ui.nav_control(ui.output_ui("navbar_auth_buttons")),
    ui.head_content(
        ui.include_css("static/custom.css"),
        ui.tags.script(ui.HTML(_SESSION_JS)),
    ),
    id="main_nav",
    title="Population Growth Simulator",
    bg="#1a2e1a",
    inverse=True,
)


# ---- Server --------------------------------------------------------------

def server(input, output, session):
    token    = reactive.value(None)
    username = reactive.value(None)

    account_server(input, output, session, token=token, username=username)
    browse_server(input, output, session, token=token)
    my_matrices_server(input, output, session, token=token, username=username)
    simulate_server(input, output, session, token=token, username=username)

    # ---- Routing effects -------------------------------------------------

    @reactive.effect
    @reactive.event(input.route_path)
    def _apply_initial_route():
        """On page load: activate the tab matching the URL path."""
        ui.update_navs("main_nav", selected=input.route_path())

    @reactive.effect
    @reactive.event(input.main_nav)
    async def _push_route():
        """On tab change: push the corresponding path to the browser URL."""
        tab_to_path = {
            "Browse matrices": "/matrices",
            "Simulate":        "/simulate",
            "My matrices":     "/my-matrices",
        }
        path = tab_to_path.get(input.main_nav(), "/")
        await session.send_custom_message("push_route", path)


# ---- ASGI app (wrapped with SPA middleware) ------------------------------

app = App(app_ui, server)
app = SPAMiddleware(app)
