"""My matrices tab — top-level nav panel UI."""
from shiny import ui


def my_matrices_ui():
    return ui.nav_panel(
        "My matrices",
        ui.output_ui("mm_view"),
    )
