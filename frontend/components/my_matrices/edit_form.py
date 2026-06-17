"""My matrices tab — Edit form server logic.

Handles metadata editing, visibility, share management, and delete.
"""
import httpx
from shiny import reactive, render, req, ui

from components.utils import API_BASE, api

def edit_form_server(input, output, session, *, token, on_modified, tr):
    """Register server logic for the Edit matrix form.

    Parameters
    ----------
    on_modified : callable
        Called after any mutation (save, delete, visibility change, share change).
        Triggers my_matrices_server to refresh the matrix list and re-render.
    """
    _edit_success = reactive.value(None)
    _edit_msg      = reactive.value(None)
    _shares_version = reactive.value(0)
    _deleted_mid   = reactive.value(None)

    def _edit_species_name():
        mid = getattr(input, "mm_my_select", lambda: None)()
        if not mid:
            return "matrix"
        try:
            m = api("GET", f"/v1/matrices/{mid}", token=token())
            return (m.get("species_accepted") or f"matrix_{mid}").replace(" ", "_")
        except ValueError:
            return f"matrix_{mid}"

    def _edit_display_name():
        mid = getattr(input, "mm_my_select", lambda: None)()
        try:
            m = api("GET", f"/v1/matrices/{mid}", token=token())
            return m.get("species_accepted") or f"Matrix #{mid}"
        except ValueError:
            return f"Matrix #{mid}"

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
            _edit_success.set(True)
            _edit_msg.set(tr("my_matrices.changes_saved"))
            on_modified()
        except ValueError as e:
            _edit_success.set(False)
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
            _edit_success.set(True)
            _edit_msg.set(tr("my_matrices.visibility_set", vis=new_vis))
            _invalidate_shares()
        except ValueError as e:
            _edit_success.set(False)
            _edit_msg.set(str(e))

    # ---- Delete ----------------------------------------------------------

    @reactive.effect
    @reactive.event(input.mm_delete_btn)
    def _do_delete():
        req(token())
        mid = getattr(input, "mm_my_select", lambda: None)()
        req(mid)
        name = _edit_display_name()
        modal = ui.modal(
            ui.p(tr("my_matrices.confirm_delete_body", name=name)),
            title=tr("my_matrices.confirm_delete_title"),
            footer=ui.div(
                ui.modal_button(tr("my_matrices.cancel_btn"), class_="btn-secondary me-2"),
                ui.input_action_button("mm_delete_confirm_btn", tr("my_matrices.confirm_delete_btn"),
                                       class_="btn-danger"),
            ),
            easy_close=True,
        )
        ui.modal_show(modal)

    @reactive.effect
    @reactive.event(input.mm_delete_confirm_btn)
    def _do_delete_confirm():
        req(token())
        mid = getattr(input, "mm_my_select", lambda: None)()
        req(mid)
        try:
            api("DELETE", f"/v1/matrices/{mid}", token=token())
            ui.modal_remove()
            ui.notification_show(tr("my_matrices.matrix_deleted"), type="message", duration=4)
            _deleted_mid.set(mid)
            on_modified()
        except ValueError as e:
            ui.modal_remove()
            ui.notification_show(str(e), type="error", duration=5)

    # ---- Share management ------------------------------------------------

    @reactive.effect
    @reactive.event(input.mm_share_btn)
    def _do_add_share():
        req(token())
        mid = getattr(input, "mm_my_select", lambda: None)()
        req(mid)
        target = getattr(input, "mm_share_username", lambda: "")().strip()
        if not target:
            _edit_success.set(False)
            _edit_msg.set(tr("my_matrices.enter_username_error"))
            return
        try:
            api("POST", f"/v1/matrices/{mid}/shares", token=token(),
                json={"username": target})
            _edit_success.set(True)
            _edit_msg.set(tr("my_matrices.shared_with_user", username=target))
            _invalidate_shares()
        except ValueError as e:
            _edit_success.set(False)
            _edit_msg.set(str(e))

    @reactive.effect
    @reactive.event(input.mm_unshare_btn)
    def _do_remove_share():
        req(token())
        mid = getattr(input, "mm_my_select", lambda: None)()
        req(mid)
        sel_uid = getattr(input, "mm_shares_select", lambda: None)()
        if not sel_uid:
            _edit_success.set(False)
            _edit_msg.set(tr("my_matrices.select_user_error"))
            return
        try:
            api("DELETE", f"/v1/matrices/{mid}/shares/{sel_uid}", token=token())
            _edit_success.set(True)
            _edit_msg.set(tr("my_matrices.share_removed"))
            _invalidate_shares()
        except ValueError as e:
            _edit_success.set(False)
            _edit_msg.set(str(e))

    # ---- Rendered outputs ------------------------------------------------

    @output
    @render.ui
    def mm_edit_form():
        _shares_version()   # re-render when shares change
        mid = getattr(input, "mm_my_select", lambda: None)()
        if not mid or mid == _deleted_mid():
            return ui.p(tr("my_matrices.select_to_edit"), class_="text-muted")
        try:
            m = api("GET", f"/v1/matrices/{mid}", token=token())
        except ValueError as e:
            return ui.p(str(e), class_="text-danger")

        vis = m.get("visibility", "private")
        vis_labels = {
            "private": (tr("my_matrices.vis_label_private"), "secondary"),
            "shared":  (tr("my_matrices.vis_label_shared"),  "primary"),
            "public":  (tr("my_matrices.vis_label_public"),  "success"),
        }
        vis_label, vis_color = vis_labels.get(vis, ("Unknown", "secondary"))

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
                ui.h6(tr("my_matrices.shared_with")),
                (
                    ui.div(
                        ui.input_select("mm_shares_select", None,
                                        choices=share_choices,
                                        size=min(5, len(share_choices))),
                        ui.input_action_button("mm_unshare_btn", tr("my_matrices.remove_selected"),
                                               class_="btn-outline-danger btn-sm w-100 mt-1"),
                    )
                    if share_choices
                    else ui.p(tr("my_matrices.no_users"), class_="text-muted small")
                ),
                ui.hr(),
                ui.h6(tr("my_matrices.add_user")),
                ui.input_text("mm_share_username", None, placeholder=tr("my_matrices.username_placeholder")),
                ui.input_action_button("mm_share_btn", tr("my_matrices.share_btn"),
                                       class_="btn-outline-primary btn-sm w-100 mt-1"),
            )

        return ui.div(
            ui.div(
                ui.p(ui.tags.b(tr("my_matrices.editing_prefix") + " "), m.get("species_accepted") or f"Matrix #{mid}",
                     class_="mb-1"),
                ui.tags.span(vis_label, class_=f"badge text-bg-{vis_color} mb-3"),
            ),
            ui.input_text("mm_edit_common", tr("my_matrices.common_name"),
                          value=m.get("common_name") or ""),
            ui.input_text("mm_edit_country", tr("my_matrices.country_code_edit"),
                          value=m.get("country_code") or ""),
            ui.input_action_button("mm_save_btn", tr("my_matrices.save_changes"),
                                   class_="btn-warning w-100 mt-2"),
            ui.div(
                ui.download_button("mm_export_json", tr("my_matrices.export_json"),
                                   class_="btn-sm btn-outline-primary me-1 mt-2"),
                ui.download_button("mm_export_csv", tr("my_matrices.export_csv"),
                                   class_="btn-sm btn-outline-secondary mt-2"),
            ),
            ui.hr(),
            ui.h6(tr("my_matrices.visibility")),
            ui.div(
                ui.input_select(
                    "mm_vis_select", None,
                    choices={"private": tr("my_matrices.vis_private"),
                             "shared":  tr("my_matrices.vis_shared"),
                             "public":  tr("my_matrices.vis_public")},
                    selected=vis,
                ),
                ui.input_action_button("mm_vis_btn", tr("my_matrices.change_vis_btn"),
                                       class_="btn-outline-secondary btn-sm mt-1 w-100"),
            ),
            shares_section,
            ui.hr(),
            ui.input_action_button("mm_delete_btn", tr("my_matrices.delete_matrix_btn"),
                                   class_="btn-outline-danger btn-sm w-100"),
            ui.output_ui("mm_edit_result"),
        )

    @output
    @render.ui
    def mm_edit_result():
        getattr(input, "mm_save_btn",    lambda: None)()
        getattr(input, "mm_vis_btn",     lambda: None)()
        getattr(input, "mm_share_btn",   lambda: None)()
        getattr(input, "mm_unshare_btn", lambda: None)()
        msg = _edit_msg()
        if not msg:
            return None
        ok = bool(_edit_success())
        return ui.div(ui.tags.span(msg, class_=f"text-{'success' if ok else 'danger'} small"),
                      class_="mt-2")
