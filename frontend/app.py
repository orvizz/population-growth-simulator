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

_SESSION_JS = """
$(document).on('shiny:sessioninitialized', function () {
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

app_ui = ui.page_navbar(
    browse_ui(),
    my_matrices_ui(),
    simulate_ui(),
    ui.nav_spacer(),
    ui.nav_control(ui.output_ui("navbar_auth_buttons")),
    ui.head_content(ui.tags.script(ui.HTML(_SESSION_JS))),
    id="main_nav",
    title="Population Growth Simulator",
    bg="#1a252f",
    inverse=True,
)


def server(input, output, session):
    token = reactive.value(None)
    username = reactive.value(None)

    account_server(input, output, session, token=token, username=username)
    browse_server(input, output, session, token=token)
    my_matrices_server(input, output, session, token=token, username=username)
    simulate_server(input, output, session, token=token, username=username)


app = App(app_ui, server)
