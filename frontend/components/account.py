"""Auth modals — login, register, navbar session controls."""
from shiny import reactive, render, ui

from .utils import ApiError, api

_CODE_TO_KEY = {
    "invalid_credentials": "auth.errors.invalid_credentials",
    "username_taken": "auth.errors.username_taken",
    "email_taken": "auth.errors.email_taken",
}

_FIELD_TO_KEY = {
    "username": "auth.errors.username_invalid",
    "email": "auth.errors.email_invalid",
    "password": "auth.errors.password_weak",
}


def _auth_error_message(tr, err: Exception, fallback_key: str) -> str:
    """Map an ApiError from the auth endpoints to a localized message.

    Mapping is based on the API's stable error code (409/401) or the
    field name of a 422 validation error — never on the API's English
    `msg` text — so the result is fully translated via the i18n engine.
    """
    if isinstance(err, ApiError):
        if isinstance(err.raw_detail, str):
            key = _CODE_TO_KEY.get(err.raw_detail)
            if key:
                return tr(key)
        elif isinstance(err.raw_detail, list):
            for item in err.raw_detail:
                loc = (item or {}).get("loc") or []
                field = loc[-1] if loc else None
                key = _FIELD_TO_KEY.get(field)
                if key:
                    return tr(key)
    return tr(fallback_key)


def _login_modal(tr):
    return ui.modal(
        ui.tags.div(
            ui.tags.label(tr("auth.username"), class_="fw-semibold form-label"),
            ui.input_text("login_user", label=None),
        ),
        ui.tags.div(
            ui.tags.label(tr("auth.password"), class_="fw-semibold form-label"),
            ui.input_password("login_pass", label=None),
        ),
        ui.input_action_button("login_btn", tr("auth.login_btn"), class_="btn-primary w-100 mt-1"),
        ui.output_ui("login_msg"),
        ui.div(
            tr("auth.no_account") + " ",
            ui.input_action_link("go_to_register", tr("auth.register_here")),
            class_="mt-3 text-center text-muted small",
        ),
        title=tr("auth.login_title"),
        easy_close=True,
        footer=None,
    )


def _register_modal(tr):
    return ui.modal(
        ui.tags.div(
            ui.tags.label(tr("auth.username"), class_="fw-semibold form-label"),
            ui.input_text("reg_user", label=None),
        ),
        ui.tags.div(
            ui.tags.label(tr("auth.email"), class_="fw-semibold form-label"),
            ui.input_text("reg_email", label=None),
        ),
        ui.tags.div(
            ui.tags.label(tr("auth.password_hint"), class_="fw-semibold form-label"),
            ui.input_password("reg_pass", label=None),
        ),
        ui.input_action_button("reg_btn", tr("auth.signup_btn"), class_="btn-success w-100 mt-1"),
        ui.output_ui("reg_msg"),
        ui.div(
            tr("auth.have_account") + " ",
            ui.input_action_link("go_to_login", tr("auth.login_here")),
            class_="mt-3 text-center text-muted small",
        ),
        title=tr("auth.register_title"),
        easy_close=True,
        footer=None,
    )


def account_server(input, output, session, *, token, username, tr):
    _reg_success = reactive.value(None)
    _login_error = reactive.value(None)
    _reg_error = reactive.value(None)

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
                                ui.tags.small(tr("auth.signed_in_as"), class_="text-muted"),
                                ui.tags.div(ui.tags.b(uname)),
                                class_="px-3 py-2",
                            )
                        ),
                        ui.tags.li(ui.tags.hr(class_="dropdown-divider my-1")),
                        ui.tags.li(
                            ui.input_action_button(
                                "nav_logout_btn",
                                tr("auth.sign_out"),
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
                "nav_login_btn", tr("auth.login_nav"), class_="btn btn-outline-light btn-sm me-2"
            ),
            ui.input_action_button(
                "nav_register_btn", tr("auth.signup_nav"), class_="btn btn-primary btn-sm"
            ),
            class_="d-flex align-items-center",
        )

    # --- Open modals ----------------------------------------------------------

    @reactive.effect
    @reactive.event(input.nav_login_btn)
    def _open_login():
        _login_error.set(None)
        ui.modal_show(_login_modal(tr))

    @reactive.effect
    @reactive.event(input.nav_register_btn)
    def _open_register():
        _reg_success.set(None)
        _reg_error.set(None)
        ui.modal_show(_register_modal(tr))

    # --- Cross-links between modals -------------------------------------------

    @reactive.effect
    @reactive.event(input.go_to_register)
    def _switch_to_register():
        _reg_success.set(None)
        _reg_error.set(None)
        ui.modal_remove()
        ui.modal_show(_register_modal(tr))

    @reactive.effect
    @reactive.event(input.go_to_login)
    def _switch_to_login():
        _login_error.set(None)
        ui.modal_remove()
        ui.modal_show(_login_modal(tr))

    @reactive.effect
    @reactive.event(input.go_to_login_after_reg)
    def _switch_to_login_after_reg():
        _login_error.set(None)
        ui.modal_remove()
        ui.modal_show(_login_modal(tr))

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
            _login_error.set(None)
            await session.send_custom_message("save_session", {
                "token": data["access_token"],
                "username": input.login_user(),
            })
            ui.modal_remove()
        except ValueError as e:
            token.set(None)
            username.set(None)
            _login_error.set(e)

    @output
    @render.ui
    def login_msg():
        input.login_btn()
        if input.login_btn() == 0:
            return None
        if username():
            return None
        err = _login_error()
        if err is None:
            return None
        return ui.div(
            ui.tags.span(_auth_error_message(tr, err, "auth.login_error"), class_="text-danger"),
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
            _reg_error.set(None)
        except ValueError as e:
            _reg_success.set(False)
            _reg_error.set(e)

    @output
    @render.ui
    def reg_msg():
        input.reg_btn()
        if input.reg_btn() == 0:
            return None
        if _reg_success() is True:
            return ui.div(
                ui.tags.span(
                    tr("auth.account_created") + " ",
                    ui.input_action_link("go_to_login_after_reg", tr("auth.log_in_link")),
                    ".",
                    class_="text-success",
                ),
                class_="mt-2",
            )
        if _reg_success() is False:
            err = _reg_error()
            message = (
                _auth_error_message(tr, err, "auth.register_error")
                if err is not None
                else tr("auth.register_error")
            )
            return ui.div(
                ui.tags.span(message, class_="text-danger"),
                class_="mt-2",
            )
        return None
