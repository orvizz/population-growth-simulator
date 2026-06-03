"""Shared utilities used across all frontend components."""
import math
import os

import httpx
import matplotlib.pyplot as plt

API_BASE = os.environ.get("API_BASE_URL", "http://localhost:8000")


def api(method: str, path: str, *, token: str | None = None, **kwargs):
    """Call the backend API. Raises ValueError with the detail message on HTTP errors."""
    headers = {"Authorization": f"Bearer {token}"} if token else {}
    try:
        r = httpx.request(method, f"{API_BASE}{path}", headers=headers, timeout=10, **kwargs)
        r.raise_for_status()
        return r.json()
    except httpx.HTTPStatusError as e:
        try:
            detail = e.response.json().get("detail", str(e))
        except Exception:
            detail = str(e)
        raise ValueError(detail)
    except httpx.RequestError:
        raise ValueError("Cannot reach the API — is the backend running?")


def render_population_plot(result_history: list, stage_names: list | None, title: str = "Population dynamics"):
    """Return a matplotlib Figure for the given simulation history (used by tests / legacy)."""
    stage_names = stage_names or [f"Stage {i}" for i in range(len(result_history[0]))]
    time_steps = list(range(len(result_history)))

    fig, ax = plt.subplots(figsize=(9, 4))
    for i, name in enumerate(stage_names):
        values = [step[i] for step in result_history]
        ax.plot(time_steps, values, marker="o", markersize=3, linewidth=1.5, label=name)

    ax.set_title(title)
    ax.set_xlabel("Time step (n)")
    ax.set_ylabel("Population")
    ax.legend(loc="upper right")
    ax.grid(True, alpha=0.3)
    fig.tight_layout()
    return fig


def render_population_plotly(
    result_history: list,
    stage_names: list | None,
    title: str = "Population dynamics",
):
    """Return a Plotly Figure for the given simulation history.

    Produces an interactive line chart with hover tooltips, zoom/pan, and
    per-stage toggle via legend click. Use ``fig.to_html(...)`` to embed
    in a Shiny ``render.ui`` output.
    """
    import plotly.graph_objects as go

    n_stages = len(result_history[0]) if result_history else 0
    names = stage_names or [f"Stage {i}" for i in range(n_stages)]
    x = list(range(len(result_history)))

    # Ecological green palette — cycles if more stages than colours
    _GREEN_PALETTE = [
        "#2d5a27", "#4a7c59", "#6aaa85", "#98d4b0",
        "#1a2e1a", "#b6e6c8", "#3d7a3d", "#88c888",
    ]

    def _safe(v):
        """Convert int/float to float; return None for non-finite values so plotly draws a gap."""
        try:
            f = float(v)
            return None if not math.isfinite(f) else f
        except (TypeError, ValueError):
            return None

    fig = go.Figure()
    for i, name in enumerate(names):
        fig.add_trace(go.Scatter(
            x=x,
            y=[_safe(step[i]) for step in result_history],
            mode="lines+markers",
            name=name,
            marker=dict(size=4),
            line=dict(color=_GREEN_PALETTE[i % len(_GREEN_PALETTE)], width=2),
        ))

    fig.update_layout(
        title=dict(text=title, font=dict(size=13, family="Inter, sans-serif")),
        xaxis_title="Time step (n)",
        yaxis_title="Population",
        height=350,
        margin=dict(l=50, r=20, t=45, b=40),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        plot_bgcolor="white",
        paper_bgcolor="white",
        font=dict(family="Inter, sans-serif", size=11),
        xaxis=dict(showgrid=True, gridcolor="#f0f0e8"),
        yaxis=dict(showgrid=True, gridcolor="#f0f0e8"),
        hovermode="x unified",
    )
    return fig


def plotly_html(fig, *, height: str | None = None) -> str:
    """Serialize a Plotly figure to an embeddable HTML fragment.

    The first call in a session loads plotly.js from CDN; subsequent calls
    reuse the already-loaded library (``include_plotlyjs='cdn'`` handles this
    transparently because Plotly checks if the global is already defined).
    """
    kwargs: dict = dict(include_plotlyjs="cdn", full_html=False,
                        config={"displayModeBar": False, "responsive": True})
    if height:
        fig.update_layout(height=None)  # let CSS control height if caller passes one
    return fig.to_html(**kwargs)
