"""My matrices tab — shared cell-grid editor, used by both create_form.py and edit_form.py."""
from shiny import ui


def render_matrix_grid(tr, stages, prefix, values=None):
    n = len(stages)
    if n == 0:
        return ui.tags.p(tr("my_matrices.add_stages_hint"), class_="text-muted small")
    header = ui.tags.tr(ui.tags.th("", class_="corner"), *[ui.tags.th(s) for s in stages])
    rows = []
    for i, row_name in enumerate(stages):
        cells = [ui.tags.th(row_name)]
        for j in range(n):
            cell_value = values[i][j] if values is not None else 0
            cells.append(ui.tags.td(ui.input_numeric(
                f"{prefix}_cell_{i}_{j}", label=None, value=cell_value, step=0.001, width="72px",
            )))
        rows.append(ui.tags.tr(*cells))
    return ui.tags.div(
        ui.tags.table(ui.tags.thead(header), ui.tags.tbody(*rows), class_="matrix-grid-input"),
        ui.tags.div(tr("my_matrices.tab_hint"), class_="text-muted small mt-1"),
    )


def read_matrix(input, prefix, n):
    return [[float(input[f"{prefix}_cell_{i}_{j}"]() or 0) for j in range(n)] for i in range(n)]
