"""Quasi-Extinction tab — UI definition."""
from shiny import ui


def qe_ui(tr):
    """Return the nav_panel for the Quasi-Extinction tab.

    Layout: sidebar (past analyses list) + main panel (form or results).
    The main panel content is server-rendered via output_ui("qe_main_panel")
    so the server can switch between the setup form and the results view.
    """
    return ui.nav_panel(
        tr("quasi_extinction.tab_title"),
        ui.layout_sidebar(
            ui.sidebar(
                ui.tags.div(tr("quasi_extinction.past_analyses"), class_="section-label"),
                ui.div(
                    ui.output_ui("qe_jobs_list_out"),
                    style="max-height:50vh;overflow-y:auto;",
                ),
                ui.hr(),
                ui.input_action_button(
                    "qe_new_btn", tr("quasi_extinction.new_analysis_btn"),
                    class_="btn-primary w-100",
                ),
                ui.output_ui("qe_sidebar_msg"),
                width=260,
            ),
            ui.output_ui("qe_main_panel"),
        ),
        value="quasi-extinction",
    )
