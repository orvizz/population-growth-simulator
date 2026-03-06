"""
Population Growth Simulator — Shiny frontend entry point.

Run with:
    cd frontend
    python -m shiny run app.py --reload --port 8080
"""
from shiny import App, reactive, ui

from components.account import account_server, account_ui
from components.browse import browse_server, browse_ui
from components.my_matrices import my_matrices_server, my_matrices_ui
from components.simulate import simulate_server, simulate_ui

app_ui = ui.page_navbar(
    browse_ui(),
    my_matrices_ui(),
    simulate_ui(),
    account_ui(),
    title="Population Growth Simulator",
    bg="#1a252f",
    inverse=True,
)


def server(input, output, session):
    token = reactive.value(None)
    username = reactive.value(None)

    account_server(input, output, session, token=token, username=username)
    browse_server(input, output, session)
    my_matrices_server(input, output, session, token=token, username=username)
    simulate_server(input, output, session, token=token, username=username)


app = App(app_ui, server)
