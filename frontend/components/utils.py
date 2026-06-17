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
        if not r.content:
            return None
        return r.json()
    except httpx.HTTPStatusError as e:
        try:
            detail = e.response.json().get("detail", str(e))
        except Exception:
            detail = str(e)
        if isinstance(detail, list):
            # FastAPI/Pydantic 422 responses: a list of {loc, msg, type, ...}.
            # Surface the per-field message instead of the raw dict structure.
            messages = []
            for item in detail:
                if isinstance(item, dict) and item.get("msg"):
                    loc = item.get("loc") or []
                    field = loc[-1] if loc else None
                    messages.append(f"{field}: {item['msg']}" if field else item["msg"])
            detail = "; ".join(messages) or "Invalid request — please check your input and try again."
        elif not isinstance(detail, str):
            detail = "Invalid request — please check your input and try again."
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
    min_history: list | None = None,
    max_history: list | None = None,
):
    """Return a Plotly Figure for the given simulation history.

    Produces an interactive line chart with hover tooltips, zoom/pan, and
    per-stage toggle via legend click. Use ``fig.to_html(...)`` to embed
    in a Shiny ``render.ui`` output.

    When min_history and max_history are provided (stochastic runs), a shaded
    min/max band is drawn behind each stage's mean trajectory line.
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
    # RGB triplets matching the palette above (for rgba fill)
    _GREEN_RGB = [
        "45,90,39", "74,124,89", "106,170,133", "152,212,176",
        "26,46,26", "182,230,200", "61,122,61", "136,200,136",
    ]

    def _safe(v):
        """Convert int/float to float; return None for non-finite values so plotly draws a gap."""
        try:
            f = float(v)
            return None if not math.isfinite(f) else f
        except (TypeError, ValueError):
            return None

    show_band = min_history is not None and max_history is not None

    fig = go.Figure()
    for i, name in enumerate(names):
        color = _GREEN_PALETTE[i % len(_GREEN_PALETTE)]
        rgb = _GREEN_RGB[i % len(_GREEN_RGB)]

        if show_band:
            min_y = [math.floor(v) if (v := _safe(step[i])) is not None else None for step in min_history]
            max_y = [math.floor(v) if (v := _safe(step[i])) is not None else None for step in max_history]
            # Filled band: upper edge forward then lower edge backward (toself)
            fig.add_trace(go.Scatter(
                x=x + x[::-1],
                y=max_y + list(reversed(min_y)),
                fill="toself",
                fillcolor=f"rgba({rgb},0.15)",
                line=dict(color="rgba(0,0,0,0)"),
                showlegend=False,
                hoverinfo="skip",
            ))

        fig.add_trace(go.Scatter(
            x=x,
            y=[math.floor(v) if (v := _safe(step[i])) is not None else None for step in result_history],
            mode="lines+markers",
            name=name,
            marker=dict(size=4),
            line=dict(color=color, width=2),
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
    kwargs: dict = dict(include_plotlyjs=False, full_html=False,
                        config={"displayModeBar": False, "responsive": True})
    if height:
        fig.update_layout(height=None)  # let CSS control height if caller passes one
    return fig.to_html(**kwargs)
