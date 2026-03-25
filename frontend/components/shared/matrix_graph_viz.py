"""
matrix_graph_viz.py
-------------------
A library to generate interactive graph visualizations from a square
transition/adjacency matrix with node labels.

Produces self-contained HTML with vis-network (draggable nodes,
tooltips, zoom, etc.) that can be embedded in Python Shiny via
ui.HTML() or saved to disk.
"""

from __future__ import annotations
import json
from typing import Optional


# ---------------------------------------------------------------------------
# Colour helpers
# ---------------------------------------------------------------------------
_DEFAULT_FWD_COLOR = "#2a6496"   # blue  – standard forward transitions
_DEFAULT_SELF_COLOR = "#2a6496"  # same  – self-loops
_DEFAULT_REPRO_COLOR = "#2d6a4f" # green – fecundity / reproductive arcs


def _edge_color(value: float, threshold: float = 0.0) -> str:
    """Return green for fecundity-style edges (above threshold) else blue."""
    return _DEFAULT_REPRO_COLOR if value > threshold else _DEFAULT_FWD_COLOR


# ---------------------------------------------------------------------------
# Core builder
# ---------------------------------------------------------------------------

def matrix_to_html(
    matrix: list[list[float]],
    labels: list[str],
    *,
    title: str = "Population Graph",
    width: str = "100%",
    height: str = "500px",
    min_edge_value: float = 0.0,
    fecundity_rows: Optional[list[int]] = None,
    physics_enabled: bool = True,
    show_controls: bool = True,
) -> str:
    """
    Convert a square matrix + label list into a self-contained HTML string
    with an interactive, draggable vis-network graph.

    Parameters
    ----------
    matrix          : NxN list-of-lists (floats).
    labels          : List of N node labels.
    title           : Shown above the graph.
    width / height  : CSS dimensions of the container.
    min_edge_value  : Edges with |value| <= this are omitted.
    fecundity_rows  : Row indices whose edges should be drawn in green
                      (reproductive / fecundity arcs).  If None, no
                      green styling is applied.
    physics_enabled : Whether vis-network physics (spring layout) starts on.
    show_controls   : Show a small toolbar (physics toggle, fit button).
    """
    n = len(labels)
    if len(matrix) != n or any(len(row) != n for row in matrix):
        raise ValueError("matrix must be square and match the number of labels")

    fecundity_rows = set(fecundity_rows or [])

    # ---- nodes -------------------------------------------------------
    nodes = []
    for i, lbl in enumerate(labels):
        nodes.append({"id": i, "label": lbl})

    # ---- edges -------------------------------------------------------
    edges = []
    eid = 0
    for i in range(n):
        for j in range(n):
            v = matrix[i][j]
            if abs(v) <= min_edge_value:
                continue
            color = _DEFAULT_REPRO_COLOR if i in fecundity_rows else _DEFAULT_FWD_COLOR
            edges.append({
                "id": eid,
                "from": i,
                "to": j,
                "label": str(round(v, 4)),
                "arrows": "to",
                "color": {"color": color, "highlight": color, "hover": color},
                "width": max(1, min(6, abs(v) * 3)),
                "smooth": {"type": "curvedCW", "roundness": 0.15} if i != j else
                          {"type": "curvedCW", "roundness": 0.6},
            })
            eid += 1

    nodes_json = json.dumps(nodes)
    edges_json = json.dumps(edges)

    controls_html = ""
    if show_controls:
        controls_html = """
        <div id="mgv-toolbar" style="
            position:absolute; top:8px; right:8px; z-index:10;
            display:flex; gap:6px;">
          <button onclick="togglePhysics()" id="mgv-phys-btn"
            style="padding:4px 10px; border-radius:4px; border:1px solid #888;
                   background:#f0f0f0; cursor:pointer; font-size:12px;">
            ⚛ Physics
          </button>
          <button onclick="network.fit()"
            style="padding:4px 10px; border-radius:4px; border:1px solid #888;
                   background:#f0f0f0; cursor:pointer; font-size:12px;">
            ⊡ Fit
          </button>
        </div>"""

    physics_js = "true" if physics_enabled else "false"

    html = f"""<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<title>{title}</title>
<script src="https://unpkg.com/vis-network@9.1.9/standalone/umd/vis-network.min.js"></script>
<style>
  body {{ margin:0; font-family: 'Segoe UI', sans-serif; }}
  #mgv-wrap {{
    position: relative;
    width: {width};
    height: {height};
    border: 1px solid #d0d0d0;
    border-radius: 8px;
    overflow: hidden;
    background: #fafafa;
  }}
  #mgv-graph {{ width:100%; height:100%; }}
</style>
</head>
<body>
<div id="mgv-wrap">
  {controls_html}
  <div id="mgv-graph"></div>
</div>
<script>
const nodes = new vis.DataSet({nodes_json});
const edges = new vis.DataSet({edges_json});

const options = {{
  nodes: {{
    shape: "circle",
    size: 38,
    font: {{ size: 14, face: "Segoe UI", bold: true }},
    color: {{
      background: "#d6d6d6",
      border: "#444",
      highlight: {{ background: "#bde0fe", border: "#1a6fb5" }},
      hover:      {{ background: "#e8f4fd", border: "#1a6fb5" }}
    }},
    borderWidth: 2,
    shadow: {{ enabled: true, size: 6, x: 2, y: 2, color: "rgba(0,0,0,0.15)" }}
  }},
  edges: {{
    font: {{ size: 11, align: "middle", background: "rgba(255,255,255,0.75)" }},
    selfReferenceSize: 30,
    selectionWidth: 2
  }},
  physics: {{
    enabled: {physics_js},
    barnesHut: {{
      gravitationalConstant: -8000,
      springLength: 160,
      springConstant: 0.04
    }}
  }},
  interaction: {{
    hover: true,
    tooltipDelay: 100,
    navigationButtons: false
  }},
  layout: {{ improvedLayout: true }}
}};

const container = document.getElementById("mgv-graph");
const network = new vis.Network(container, {{ nodes, edges }}, options);

let physicsOn = {physics_js};
function togglePhysics() {{
  physicsOn = !physicsOn;
  network.setOptions({{ physics: {{ enabled: physicsOn }} }});
  const btn = document.getElementById("mgv-phys-btn");
  if (btn) btn.style.background = physicsOn ? "#c8f7c5" : "#f0f0f0";
}}
</script>
</body>
</html>"""
    return html


def matrix_to_file(
    matrix: list[list[float]],
    labels: list[str],
    filepath: str,
    **kwargs,
) -> None:
    """Save the HTML visualization to *filepath*."""
    html = matrix_to_html(matrix, labels, **kwargs)
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(html)
    print(f"Graph saved to {filepath}")