"""
Unit tests for the shared matrix-grid editor
(frontend/components/my_matrices/matrix_grid.py).

Both create_form.py and edit_form.py render/read the same A/U/F cell grids;
this module is the single source of truth so the two forms can't drift.
"""
from frontend.components.my_matrices.matrix_grid import read_matrix, render_matrix_grid


def _tr(key, **kwargs):
    return key


class _FakeInput:
    """Stand-in for Shiny's `input` proxy: input["x"]() returns the value."""

    def __init__(self, values: dict):
        self._values = values

    def __getitem__(self, key):
        return lambda: self._values.get(key)


def test_read_matrix_reads_cells_in_row_major_order():
    fake = _FakeInput({
        "mm_cell_0_0": 1.0, "mm_cell_0_1": 2.0,
        "mm_cell_1_0": 3.0, "mm_cell_1_1": 4.0,
    })
    assert read_matrix(fake, "mm", 2) == [[1.0, 2.0], [3.0, 4.0]]


def test_read_matrix_treats_none_as_zero():
    fake = _FakeInput({"mm_cell_0_0": None})
    assert read_matrix(fake, "mm", 1) == [[0.0]]


def test_render_matrix_grid_empty_stages_shows_hint():
    result = render_matrix_grid(_tr, [], "mm")
    assert "my_matrices.add_stages_hint" in str(result)


def test_render_matrix_grid_defaults_cells_to_zero_without_values():
    html = str(render_matrix_grid(_tr, ["seedling", "adult"], "mm"))
    assert 'id="mm_cell_0_0"' in html
    assert 'id="mm_cell_1_1"' in html


def test_render_matrix_grid_prepopulates_cells_from_values():
    html = str(render_matrix_grid(
        _tr, ["seedling", "adult"], "mm_edit", values=[[0.2, 0.5], [0.1, 0.8]]
    ))
    assert 'id="mm_edit_cell_0_0"' in html
    assert "0.2" in html
    assert "0.8" in html
