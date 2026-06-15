from shiny import ui
import plotly.graph_objects as go


def matrix_display(
    matrix: list[list[float]],
    stage_names: list[str] | None,
) -> ui.TagList:
    """Plotly heatmap + collapsible numeric table for a square matrix."""
    if not matrix:
        return ui.TagList(ui.tags.p("No matrix data.", class_="text-muted small"))
    n = len(matrix)
    names = stage_names or [f"S{i}" for i in range(n)]
    return ui.TagList(
        _matrix_heatmap(matrix, names),
        _matrix_table(matrix, names),
    )


def _matrix_heatmap(matrix: list[list[float]], names: list[str]) -> ui.HTML:
    n = len(matrix)
    fig = go.Figure(go.Heatmap(
        z=matrix,
        x=names,
        y=names,
        colorscale="Blues",
        text=[[f"{v:.3f}" for v in row] for row in matrix],
        texttemplate="%{text}",
        showscale=True,
        colorbar=dict(thickness=10, len=0.8),
        hovertemplate="from %{x} → to %{y}<br>value: %{z:.4f}<extra></extra>",
    ))
    cell_px = max(50, min(80, 300 // n))
    fig.update_layout(
        height=n * cell_px + 80,
        margin=dict(l=60, r=60, t=20, b=60),
        xaxis=dict(title="Stage (j)", side="bottom"),
        yaxis=dict(title="Stage (i)", autorange="reversed"),
        plot_bgcolor="white", paper_bgcolor="white",
        font=dict(family="Inter, sans-serif", size=11),
    )
    return ui.HTML(fig.to_html(include_plotlyjs=False, full_html=False,
                               config={"displayModeBar": False}))


def _matrix_table(matrix: list[list[float]], names: list[str]) -> ui.Tag:
    header = ui.tags.tr(
        ui.tags.th(""),
        *[ui.tags.th(name, class_="text-muted small fw-normal") for name in names],
    )
    rows = [
        ui.tags.tr(
            ui.tags.th(names[i], class_="text-muted small fw-normal pe-2"),
            *[ui.tags.td(f"{v:.4f}", class_="small") for v in row],
        )
        for i, row in enumerate(matrix)
    ]
    return ui.tags.details(
        ui.tags.summary(
            "Show values",
            style="cursor:pointer; font-size:12px; color:#6c757d; margin-top:4px",
        ),
        ui.tags.table(
            ui.tags.thead(header),
            ui.tags.tbody(*rows),
            class_="table table-sm table-bordered mt-1",
            style="font-size:11px",
        ),
    )
