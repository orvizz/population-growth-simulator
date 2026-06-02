"""My matrices tab — Edit form server logic.

Handles metadata editing, visibility, share management, and delete.
"""
import httpx
from shiny import reactive, render, req, ui

from components.utils import API_BASE, api

_VIS_BADGE = {
    "private": ("Private", "secondary"),
    "shared":  ("Shared",  "primary"),
    "public":  ("Public",  "success"),
}


def edit_form_server(input, output, session, *, token, on_modified):
    """Register server logic for the Edit matrix form.

    Parameters
    ----------
    on_modified : callable
        Called after any mutation (save, delete, visibility change, share change).
        Triggers my_matrices_server to refresh the matrix list and re-render.
    """
    _edit_msg      = reactive.value(None)
    _shares_version = reactive.value(0)

    def _edit_species_name():
        mid = getattr(input, "mm_my_select", lambda: None)()
        if not mid:
            return "matrix"
        try:
            m = api("GET", f"/v1/matrices/{mid}", token=token())
            return (m.get("species_accepted") or f"matrix_{mid}").replace(" ", "_")
        except ValueError:
            return f"matrix_{mid}"

    @render.download(filename=lambda: f"{_edit_species_name()}.json")
    def mm_export_json():
        mid = getattr(input, "mm_my_select", lambda: None)()
        if not mid:
            yield b""
            return
        try:
            r = httpx.get(f"{API_BASE}/v1/matrices/{mid}/export",
                          headers={"Authorization": f"Bearer {token()}"}, timeout=10)
            r.raise_for_status()
            yield r.content
        except Exception:
            yield b""

    @render.download(filename=lambda: f"{_edit_species_name()}.csv")
    def mm_export_csv():
        mid = getattr(input, "mm_my_select", lambda: None)()
        if not mid:
            yield b""
            return
        try:
            r = httpx.get(f"{API_BASE}/v1/matrices/{mid}/export?format=csv",
                          headers={"Authorization": f"Bearer {token()}"}, timeout=10)
            r.raise_for_status()
            yield r.content
        except Exception:
            yield b""

    def _invalidate_shares():
        _shares_version.set(_shares_version() + 1)

    # ---- Save metadata ---------------------------------------------------

    @reactive.effect
    @reactive.event(input.mm_save_btn)
    def _do_save():
        req(token())
        mid = getattr(input, "mm_my_select", lambda: None)()
        req(mid)
        try:
            api("PATCH", f"/v1/matrices/{mid}", token=token(), json={
                "common_name":  getattr(input, "mm_edit_common",   lambda: "")() or None,
                "country_code": getattr(input, "mm_edit_country",  lambda: "")() or None,
            })
            _edit_msg.set("Changes saved.")
            on_modified()
        except ValueError as e:
            _edit_msg.set(str(e))

    # ---- Change visibility -----------------------------------------------

    @reactive.effect
    @reactive.event(input.mm_vis_btn)
    def _do_change_visibility():
        req(token())
        mid = getattr(input, "mm_my_select", lambda: None)()
        req(mid)
        new_vis = getattr(input, "mm_vis_select", lambda: None)()
        if not new_vis:
            return
        try:
            api("PATCH", f"/v1/matrices/{mid}", token=token(), json={"visibility": new_vis})
            _edit_msg.set(f"Visibility set to '{new_vis}'.")
            _invalidate_shares()
        except ValueError as e:
            _edit_msg.set(str(e))

    # ---- Delete ----------------------------------------------------------

    @reactive.effect
    @reactive.event(input.mm_delete_btn)
    def _do_delete():
        req(token())
        mid = getattr(input, "mm_my_select", lambda: None)()
        req(mid)
        try:
            api("DELETE", f"/v1/matrices/{mid}", token=token())
            _edit_msg.set("Matrix deleted.")
            on_modified()
        except ValueError as e:
            _edit_msg.set(str(e))

    # ---- Share management ------------------------------------------------

    @reactive.effect
    @reactive.event(input.mm_share_btn)
    def _do_add_share():
        req(token())
        mid = getattr(input, "mm_my_select", lambda: None)()
        req(mid)
        target = getattr(input, "mm_share_username", lambda: "")().strip()
        if not target:
            _edit_msg.set("Enter a username to share with.")
            return
        try:
            api("POST", f"/v1/matrices/{mid}/shares", token=token(),
                json={"username": target})
            _edit_msg.set(f"Shared with '{target}'.")
            _invalidate_shares()
        except ValueError as e:
            _edit_msg.set(str(e))

    @reactive.effect
    @reactive.event(input.mm_unshare_btn)
    def _do_remove_share():
        req(token())
        mid = getattr(input, "mm_my_select", lambda: None)()
        req(mid)
        sel_uid = getattr(input, "mm_shares_select", lambda: None)()
        if not sel_uid:
            _edit_msg.set("Select a user to remove.")
            return
        try:
            api("DELETE", f"/v1/matrices/{mid}/shares/{sel_uid}", token=token())
            _edit_msg.set("Share removed.")
            _invalidate_shares()
        except ValueError as e:
            _edit_msg.set(str(e))

    # ---- Rendered outputs ------------------------------------------------

    @output
    @render.ui
    def mm_edit_form():
        _shares_version()   # re-render when shares change
        mid = getattr(input, "mm_my_select", lambda: None)()
        if not mid:
            return ui.p("Select a matrix from the list to edit it.", class_="text-muted")
        try:
            m = api("GET", f"/v1/matrices/{mid}", token=token())
        except ValueError as e:
            return ui.p(str(e), class_="text-danger")

        vis = m.get("visibility", "private")
        vis_label, vis_color = _VIS_BADGE.get(vis, ("Unknown", "secondary"))

        shares_section = ui.div()
        if vis == "shared":
            try:
                shares = api("GET", f"/v1/matrices/{mid}/shares", token=token())
            except ValueError:
                shares = []

            share_choices = {str(s["shared_with_user_id"]): s["shared_with_username"]
                             for s in shares}

            shares_section = ui.div(
                ui.hr(),
                ui.h6("Shared with"),
                (
                    ui.div(
                        ui.input_select("mm_shares_select", None,
                                        choices=share_choices,
                                        size=min(5, len(share_choices))),
                        ui.input_action_button("mm_unshare_btn", "Remove selected",
                                               class_="btn-outline-danger btn-sm w-100 mt-1"),
                    )
                    if share_choices
                    else ui.p("No users yet.", class_="text-muted small")
                ),
                ui.hr(),
                ui.h6("Add user"),
                ui.input_text("mm_share_username", None, placeholder="Username"),
                ui.input_action_button("mm_share_btn", "Share",
                                       class_="btn-outline-primary btn-sm w-100 mt-1"),
            )

        return ui.div(
            ui.div(
                ui.p(ui.tags.b("Editing: "), m.get("species_accepted") or f"Matrix #{mid}",
                     class_="mb-1"),
                ui.tags.span(vis_label, class_=f"badge text-bg-{vis_color} mb-3"),
            ),
            ui.input_text("mm_edit_common", "Common name",
                          value=m.get("common_name") or ""),
            ui.input_text("mm_edit_country", "Country code",
                          value=m.get("country_code") or ""),
            ui.input_action_button("mm_save_btn", "Save changes",
                                   class_="btn-warning w-100 mt-2"),
            ui.div(
                ui.download_button("mm_export_json", "Export JSON",
                                   class_="btn-sm btn-outline-primary me-1 mt-2"),
                ui.download_button("mm_export_csv", "Export CSV",
                                   class_="btn-sm btn-outline-secondary mt-2"),
            ),
            ui.hr(),
            ui.h6("Visibility"),
            ui.div(
                ui.input_select(
                    "mm_vis_select", None,
                    choices={"private": "Private (only me)",
                             "shared":  "Shared (specific users)",
                             "public":  "Public (everyone)"},
                    selected=vis,
                ),
                ui.input_action_button("mm_vis_btn", "Change",
                                       class_="btn-outline-secondary btn-sm mt-1 w-100"),
            ),
            shares_section,
            ui.hr(),
            ui.input_action_button("mm_delete_btn", "Delete matrix",
                                   class_="btn-outline-danger btn-sm w-100"),
            ui.output_ui("mm_edit_result"),
        )

    @output
    @render.ui
    def mm_edit_result():
        getattr(input, "mm_save_btn",    lambda: None)()
        getattr(input, "mm_delete_btn",  lambda: None)()
        getattr(input, "mm_vis_btn",     lambda: None)()
        getattr(input, "mm_share_btn",   lambda: None)()
        getattr(input, "mm_unshare_btn", lambda: None)()
        msg = _edit_msg()
        if not msg:
            return None
        ok = any(w in msg.lower() for w in ("saved", "deleted", "shared", "set", "removed"))
        return ui.div(ui.tags.span(msg, class_=f"text-{'success' if ok else 'danger'} small"),
                      class_="mt-2")
