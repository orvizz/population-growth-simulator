"""Account tab — login, register, logout."""
from shiny import reactive, render, ui

from .utils import api


def account_ui():
    return ui.nav_panel(
        "Account",
        ui.layout_columns(
            ui.card(
                ui.card_header("Login"),
                ui.input_text("acct_login_user", "Username"),
                ui.input_password("acct_login_pass", "Password"),
                ui.input_action_button("acct_login_btn", "Login", class_="btn-primary w-100 mt-2"),
                ui.output_ui("acct_login_msg"),
            ),
            ui.card(
                ui.card_header("Register new account"),
                ui.input_text("acct_reg_user", "Username"),
                ui.input_text("acct_reg_email", "Email"),
                ui.input_password("acct_reg_pass", "Password (min 8 characters)"),
                ui.input_action_button("acct_reg_btn", "Register", class_="btn-success w-100 mt-2"),
                ui.output_ui("acct_reg_msg"),
            ),
            col_widths=[6, 6],
        ),
        ui.card(
            ui.card_header("Current session"),
            ui.output_ui("acct_session"),
        ),
    )


def account_server(input, output, session, *, token, username):
    @reactive.effect
    @reactive.event(input.acct_login_btn)
    def _do_login():
        try:
            data = api("POST", "/v1/auth/login", data={
                "username": input.acct_login_user(),
                "password": input.acct_login_pass(),
            })
            token.set(data["access_token"])
            username.set(input.acct_login_user())
        except ValueError:
            token.set(None)
            username.set(None)

    @reactive.effect
    @reactive.event(input.acct_logout_btn)
    def _do_logout():
        token.set(None)
        username.set(None)

    @reactive.effect
    @reactive.event(input.acct_reg_btn)
    def _do_register():
        try:
            api("POST", "/v1/auth/register", json={
                "username": input.acct_reg_user(),
                "email": input.acct_reg_email(),
                "password": input.acct_reg_pass(),
            })
        except ValueError:
            pass

    @output
    @render.ui
    def acct_login_msg():
        input.acct_login_btn()
        if input.acct_login_btn() == 0:
            return None
        if username():
            return ui.div(ui.tags.span(f"Logged in as {username()}", class_="text-success"), class_="mt-2")
        return ui.div(ui.tags.span("Login failed — check credentials.", class_="text-danger"), class_="mt-2")

    @output
    @render.ui
    def acct_reg_msg():
        input.acct_reg_btn()
        if input.acct_reg_btn() == 0:
            return None
        return ui.div(
            ui.tags.span("Registration submitted — you can now log in.", class_="text-success"),
            class_="mt-2",
        )

    @output
    @render.ui
    def acct_session():
        if username():
            return ui.div(
                ui.p(f"Signed in as: ", ui.tags.b(username())),
                ui.input_action_button("acct_logout_btn", "Log out", class_="btn-outline-secondary btn-sm"),
            )
        return ui.p("Not signed in.", class_="text-muted")
