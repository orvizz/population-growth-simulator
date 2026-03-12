"""Auth modals — login, register, navbar session controls."""
from shiny import reactive, render, ui

from .utils import api


def _login_modal():
    return ui.modal(
        ui.tags.div(
            ui.tags.label("Username", class_="fw-semibold form-label"),
            ui.input_text("login_user", label=None),
        ),
        ui.tags.div(
            ui.tags.label("Password", class_="fw-semibold form-label"),
            ui.input_password("login_pass", label=None),
        ),
        ui.input_action_button("login_btn", "Log In", class_="btn-primary w-100 mt-1"),
        ui.output_ui("login_msg"),
        ui.div(
            "Don't have an account yet? ",
            ui.input_action_link("go_to_register", "Register here"),
            class_="mt-3 text-center text-muted small",
        ),
        title="Log In",
        easy_close=True,
        footer=None,
    )


def _register_modal():
    return ui.modal(
        ui.tags.div(
            ui.tags.label("Username", class_="fw-semibold form-label"),
            ui.input_text("reg_user", label=None),
        ),
        ui.tags.div(
            ui.tags.label("Email", class_="fw-semibold form-label"),
            ui.input_text("reg_email", label=None),
        ),
        ui.tags.div(
            ui.tags.label("Password (min 8 characters)", class_="fw-semibold form-label"),
            ui.input_password("reg_pass", label=None),
        ),
        ui.input_action_button("reg_btn", "Sign Up", class_="btn-success w-100 mt-1"),
        ui.output_ui("reg_msg"),
        ui.div(
            "Already have an account? ",
            ui.input_action_link("go_to_login", "Log in here"),
            class_="mt-3 text-center text-muted small",
        ),
        title="Sign Up",
        easy_close=True,
        footer=None,
    )


def account_server(input, output, session, *, token, username):
    _reg_success = reactive.value(None)

    # --- Navbar auth buttons --------------------------------------------------

    @output
    @render.ui
    def navbar_auth_buttons():
        uname = username()
        if uname:
            initials = (uname[:2] if len(uname) >= 2 else uname).upper()
            return ui.div(
                ui.tags.div(
                    ui.tags.button(
                        initials,
                        type="button",
                        class_="btn rounded-circle fw-semibold text-white border-0",
                        style=(
                            "width:38px;height:38px;padding:0;font-size:13px;"
                            "background-color:rgba(255,255,255,0.18);"
                            "letter-spacing:0.5px;"
                        ),
                        **{"data-bs-toggle": "dropdown", "aria-expanded": "false"},
                    ),
                    ui.tags.ul(
                        ui.tags.li(
                            ui.tags.div(
                                ui.tags.small("Signed in as", class_="text-muted"),
                                ui.tags.div(ui.tags.b(uname)),
                                class_="px-3 py-2",
                            )
                        ),
                        ui.tags.li(ui.tags.hr(class_="dropdown-divider my-1")),
                        ui.tags.li(
                            ui.input_action_button(
                                "nav_logout_btn",
                                "Sign Out",
                                class_="dropdown-item text-danger",
                            )
                        ),
                        class_="dropdown-menu dropdown-menu-end shadow",
                    ),
                    class_="dropdown d-flex align-items-center",
                ),
            )
        return ui.div(
            ui.input_action_button(
                "nav_login_btn", "Log In", class_="btn btn-outline-light btn-sm me-2"
            ),
            ui.input_action_button(
                "nav_register_btn", "Sign Up", class_="btn btn-primary btn-sm"
            ),
            class_="d-flex align-items-center",
        )

    # --- Open modals ----------------------------------------------------------

    @reactive.effect
    @reactive.event(input.nav_login_btn)
    def _open_login():
        ui.modal_show(_login_modal())

    @reactive.effect
    @reactive.event(input.nav_register_btn)
    def _open_register():
        _reg_success.set(None)
        ui.modal_show(_register_modal())

    # --- Cross-links between modals -------------------------------------------

    @reactive.effect
    @reactive.event(input.go_to_register)
    def _switch_to_register():
        _reg_success.set(None)
        ui.modal_remove()
        ui.modal_show(_register_modal())

    @reactive.effect
    @reactive.event(input.go_to_login)
    def _switch_to_login():
        ui.modal_remove()
        ui.modal_show(_login_modal())

    @reactive.effect
    @reactive.event(input.go_to_login_after_reg)
    def _switch_to_login_after_reg():
        ui.modal_remove()
        ui.modal_show(_login_modal())

    # --- Restore session from localStorage (fires once on page load) ----------

    @reactive.effect
    @reactive.event(input.restored_session)
    def _restore_session():
        data = input.restored_session()
        if data and data.get("token") and data.get("username"):
            token.set(data["token"])
            username.set(data["username"])

    # --- Login ----------------------------------------------------------------

    @reactive.effect
    @reactive.event(input.login_btn)
    async def _do_login():
        try:
            data = api("POST", "/v1/auth/login", data={
                "username": input.login_user(),
                "password": input.login_pass(),
            })
            token.set(data["access_token"])
            username.set(input.login_user())
            await session.send_custom_message("save_session", {
                "token": data["access_token"],
                "username": input.login_user(),
            })
            ui.modal_remove()
        except ValueError:
            token.set(None)
            username.set(None)

    @output
    @render.ui
    def login_msg():
        input.login_btn()
        if input.login_btn() == 0:
            return None
        if username():
            return None
        return ui.div(
            ui.tags.span("Login failed — check your credentials.", class_="text-danger"),
            class_="mt-2",
        )

    # --- Logout ---------------------------------------------------------------

    @reactive.effect
    @reactive.event(input.nav_logout_btn)
    async def _do_logout():
        token.set(None)
        username.set(None)
        await session.send_custom_message("save_session", {})

    # --- Register -------------------------------------------------------------

    @reactive.effect
    @reactive.event(input.reg_btn)
    def _do_register():
        try:
            api("POST", "/v1/auth/register", json={
                "username": input.reg_user(),
                "email": input.reg_email(),
                "password": input.reg_pass(),
            })
            _reg_success.set(True)
        except ValueError:
            _reg_success.set(False)

    @output
    @render.ui
    def reg_msg():
        input.reg_btn()
        if input.reg_btn() == 0:
            return None
        if _reg_success() is True:
            return ui.div(
                ui.tags.span(
                    "Account created — you can now ",
                    ui.input_action_link("go_to_login_after_reg", "log in"),
                    ".",
                    class_="text-success",
                ),
                class_="mt-2",
            )
        if _reg_success() is False:
            return ui.div(
                ui.tags.span(
                    "Registration failed — username or email may already be taken.",
                    class_="text-danger",
                ),
                class_="mt-2",
            )
        return None
