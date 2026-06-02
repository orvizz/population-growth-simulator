"""Quasi-Extinction tab — UI definition."""
from shiny import ui


def qe_ui():
    """Return the nav_panel for the Quasi-Extinction tab.

    Layout: sidebar (past analyses list) + main panel (form or results).
    The main panel content is server-rendered via output_ui("qe_main_panel")
    so the server can switch between the setup form and the results view.
    """
    return ui.nav_panel(
        "Quasi-Extinction",
        ui.layout_sidebar(
            ui.sidebar(
                ui.tags.div("Past analyses", class_="section-label"),
                ui.output_ui("qe_jobs_list_out"),
                ui.hr(),
                ui.input_action_button(
                    "qe_new_btn", "＋ New analysis",
                    class_="btn-primary w-100",
                ),
                ui.output_ui("qe_sidebar_msg"),
                width=260,
            ),
            ui.output_ui("qe_main_panel"),
        ),
    )
