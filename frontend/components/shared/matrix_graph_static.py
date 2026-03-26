"""
matrix_graph_static.py
----------------------
Generate a responsive, publication-quality SVG of a population matrix graph.

Pure SVG output — networkx is used only for layout; no matplotlib dependency.
The returned string has viewBox set and width:100% so it resizes freely.
"""

from __future__ import annotations
import math
from typing import Optional

import networkx as nx

_FWD_COLOR = "#2a6496"    # blue  – survival / growth
_REPRO_COLOR = "#2d6a4f"  # green – fecundity / reproductive
_NODE_FILL = "#d6d6d6"
_NODE_STROKE = "#333333"
_NODE_R = 42        # node radius in SVG units
_CURVE = 38         # perpendicular offset for curved edges (px)
_VW, _VH = 900, 520
_PAD = 120          # padding inside viewBox so nodes aren't clipped


def _marker(mid: str, color: str) -> str:
    return (
        f'<marker id="{mid}" markerWidth="9" markerHeight="7" '
        f'refX="8" refY="3.5" orient="auto" markerUnits="strokeWidth">'
        f'<polygon points="0 0,9 3.5,0 7" fill="{color}"/>'
        f'</marker>'
    )


def matrix_to_svg(
    matrix: list[list[float]],
    labels: list[str],
    *,
    title: str = "",
    fecundity_rows: Optional[list[int]] = None,
    min_edge_value: float = 0.0,
) -> str:
    """
    Convert a square matrix + label list into a responsive SVG string.

    Parameters
    ----------
    matrix          : NxN list-of-lists (floats).
    labels          : List of N node labels.
    title           : Optional title drawn above the graph.
    fecundity_rows  : Row indices whose edges are drawn in green.
    min_edge_value  : Edges with |value| <= this are omitted.
    """
    n = len(labels)
    if len(matrix) != n or any(len(r) != n for r in matrix):
        raise ValueError("matrix must be square and match the number of labels")

    fecundity_rows = set(fecundity_rows or [])

    # ---- collect edges -------------------------------------------------------
    edges: list[tuple[int, int, float, str]] = []
    edge_set: set[tuple[int, int]] = set()
    for i in range(n):
        for j in range(n):
            v = matrix[i][j]
            if abs(v) <= min_edge_value:
                continue
            color = _REPRO_COLOR if i in fecundity_rows else _FWD_COLOR
            edges.append((i, j, v, color))
            edge_set.add((i, j))

    # ---- layout --------------------------------------------------------------
    G = nx.DiGraph()
    G.add_nodes_from(range(n))
    for i, j, _, _ in edges:
        G.add_edge(i, j)
    raw = nx.spring_layout(G, seed=42, k=2.5)

    xs = [raw[i][0] for i in range(n)]
    ys = [raw[i][1] for i in range(n)]
    xspan = max(max(xs) - min(xs), 1e-9)
    yspan = max(max(ys) - min(ys), 1e-9)
    xmin, ymin = min(xs), min(ys)

    def _s(x: float, y: float) -> tuple[float, float]:
        return (
            _PAD + (x - xmin) / xspan * (_VW - 2 * _PAD),
            _PAD + (y - ymin) / yspan * (_VH - 2 * _PAD),
        )

    pos = {i: _s(*raw[i]) for i in range(n)}

    # ---- build SVG parts -----------------------------------------------------
    defs = (
        "<defs>"
        + _marker("arr-blue", _FWD_COLOR)
        + _marker("arr-green", _REPRO_COLOR)
        + "</defs>"
    )

    edge_els: list[str] = []
    lbl_els: list[str] = []

    for i, j, v, color in edges:
        mid = "arr-green" if color == _REPRO_COLOR else "arr-blue"
        val = str(round(v, 2))

        if i == j:
            # Self-loop: cubic bezier looping above the node
            cx, cy = pos[i]
            r = _NODE_R
            p1x, p1y = cx - r * 0.3, cy - r * 0.96
            p2x, p2y = cx + r * 0.3, cy - r * 0.96
            c1x, c1y = cx - r * 1.6, cy - r * 3.0
            c2x, c2y = cx + r * 1.6, cy - r * 3.0
            d = (
                f"M {p1x:.1f},{p1y:.1f} "
                f"C {c1x:.1f},{c1y:.1f} {c2x:.1f},{c2y:.1f} {p2x:.1f},{p2y:.1f}"
            )
            edge_els.append(
                f'<path d="{d}" fill="none" stroke="{color}" '
                f'stroke-width="2" marker-end="url(#{mid})"/>'
            )
            lbl_els.append(
                f'<text x="{cx:.1f}" y="{cy - r * 3.35:.1f}" '
                f'text-anchor="middle" dominant-baseline="auto" '
                f'font-size="11" fill="#333">{val}</text>'
            )
        else:
            x1, y1 = pos[i]
            x2, y2 = pos[j]
            dx, dy = x2 - x1, y2 - y1
            dist = math.hypot(dx, dy) or 1e-9
            ux, uy = dx / dist, dy / dist

            # Shorten line to node edges (+ room for arrowhead)
            sx1, sy1 = x1 + ux * _NODE_R, y1 + uy * _NODE_R
            sx2, sy2 = x2 - ux * (_NODE_R + 10), y2 - uy * (_NODE_R + 10)

            # Reverse edges curve in opposite directions
            sign = -1 if (j, i) in edge_set and i > j else 1
            qx = (sx1 + sx2) / 2 - uy * _CURVE * sign
            qy = (sy1 + sy2) / 2 + ux * _CURVE * sign

            d = f"M {sx1:.1f},{sy1:.1f} Q {qx:.1f},{qy:.1f} {sx2:.1f},{sy2:.1f}"
            edge_els.append(
                f'<path d="{d}" fill="none" stroke="{color}" '
                f'stroke-width="2" marker-end="url(#{mid})"/>'
            )
            # Label at ~40 % along the bezier (closer to source = less crowding)
            t = 0.4
            lx = (1 - t) ** 2 * sx1 + 2 * (1 - t) * t * qx + t ** 2 * sx2
            ly = (1 - t) ** 2 * sy1 + 2 * (1 - t) * t * qy + t ** 2 * sy2
            lbl_els.append(
                f'<text x="{lx:.1f}" y="{ly:.1f}" '
                f'text-anchor="middle" dominant-baseline="middle" '
                f'font-size="11" fill="#333">{val}</text>'
            )

    node_els: list[str] = []
    for i in range(n):
        cx, cy = pos[i]
        node_els.append(
            f'<circle cx="{cx:.1f}" cy="{cy:.1f}" r="{_NODE_R}" '
            f'fill="{_NODE_FILL}" stroke="{_NODE_STROKE}" stroke-width="2.5"/>'
        )
        node_els.append(
            f'<text x="{cx:.1f}" y="{cy:.1f}" '
            f'dominant-baseline="middle" text-anchor="middle" '
            f'font-size="12" font-weight="bold" fill="#222">{labels[i]}</text>'
        )

    title_el = ""
    if title:
        title_el = (
            f'<text x="{_VW // 2}" y="26" text-anchor="middle" '
            f'font-size="14" font-weight="bold" fill="#222">{title}</text>'
        )

    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" '
        f'viewBox="0 0 {_VW} {_VH}" '
        f'style="width:100%;height:auto;display:block;background:white;">\n'
        f"{defs}\n"
        f'<g>{"".join(edge_els)}</g>\n'
        f'<g>{"".join(lbl_els)}</g>\n'
        f'<g>{"".join(node_els)}</g>\n'
        f"{title_el}\n"
        f"</svg>"
    )
