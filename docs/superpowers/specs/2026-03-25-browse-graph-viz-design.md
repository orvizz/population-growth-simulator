# Browse Tab — Matrix Graph Visualization Integration

**Date:** 2026-03-25
**Status:** Approved

## Goal

Embed an interactive vis-network graph of each matrix inside the Browse matrices detail view, so users can visually explore population stage transitions alongside the existing numeric tables.

## Layout

The matrix detail card (`browse_matrix_detail`) is restructured into two side-by-side columns using `ui.layout_columns(col_widths=[5, 7])`:

- **Left column (width 5):** existing content — species header, metadata table, and text matrix tables (`_fmt_matrix` for A, U, F).
- **Right column (width 7):** new tabbed graph panel.

The existing text matrix tables are kept; the graph is additive.

## Graph Panel

A `ui.navset_tab` with up to three `ui.nav_panel` entries — one per matrix type (A, U, F). A tab is only created if the corresponding matrix data is present in the API response (e.g. `m.get("matrix_a")` is non-empty).

Tab labels mirror the existing headings:
- `"Matrix A — projection"`
- `"Matrix U — survival/growth"`
- `"Matrix F — fecundity"`

Each tab embeds its graph via:

```python
ui.HTML(f'<iframe srcdoc="{html.escape(matrix_to_html(...))}" width="100%" height="480px" frameborder="0"></iframe>')
```

## Node Labels

Stage names come from `m.get("stage_names")`. If absent or shorter than the matrix dimension, fall back to `f"Stage {i+1}"` for missing entries.

## Edge Colouring

- **Matrix F:** pass `fecundity_rows=list(range(n))` — all edges rendered green (reproductive arcs).
- **Matrix A and U:** no `fecundity_rows` — all edges rendered in default blue.

## Files Changed

| File | Change |
|---|---|
| `frontend/components/browse.py` | Modify `browse_matrix_detail` to use `ui.layout_columns` and append the tabbed graph panel |

No new files. `matrix_to_html` is already imported at the top of `browse.py`.

## Out of Scope

- Graph panel on the Simulate or My Matrices tabs (separate tasks).
- Fecundity row detection for Matrix A (requires domain metadata not currently in the API response).
- Physics/fit controls customisation beyond `matrix_to_html` defaults.
