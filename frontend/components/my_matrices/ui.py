"""My matrices tab — top-level nav panel UI."""
from shiny import ui


def my_matrices_ui(tr):
    return ui.nav_panel(
        tr("my_matrices.title"),
        ui.output_ui("mm_view"),
        value="my-matrices",
    )
