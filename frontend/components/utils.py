"""Shared utilities used across all frontend components."""
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
    """Return a matplotlib Figure for the given simulation history."""
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
