# Regenerate the burndown charts: python generate_burndown.py
# Reads burndown_data.json (estimates + actual completion dates per task) and writes:
#   - ../diagrams/burndown-s0.svg ... burndown-s5.svg  (one chart per sprint)
#   - ../diagrams/burndown-global.svg                  (whole-project chart, shaded by sprint)
# Embedded by chapters/02_planning/sprints/tracking.typ.
import json
from datetime import date, timedelta
from pathlib import Path

import matplotlib.pyplot as plt

HERE = Path(__file__).parent
DATA_PATH = HERE / "burndown_data.json"
DIAGRAMS_DIR = HERE.parent / "diagrams"

# Light, distinct band colour per sprint, used to delimit sprints on the global chart.
SPRINT_BANDS = ["#E0F2FE", "#DCFCE7", "#FEF3C7", "#FCE7F3", "#EDE9FE", "#FFE4D5"]


def parse(d):
    return date.fromisoformat(d)


def sprint_curves(sprint):
    start = parse(sprint["period_start"])
    end = parse(sprint["period_end"])
    total_points = sum(t["points"] for t in sprint["tasks"])
    days = [start + timedelta(days=n) for n in range((end - start).days + 1)]

    ideal = [
        total_points * (1 - n / (len(days) - 1)) if len(days) > 1 else 0
        for n in range(len(days))
    ]

    actual = []
    remaining = total_points
    for day in days:
        completed_today = sum(
            t["points"] for t in sprint["tasks"] if parse(t["end"]) == day
        )
        remaining -= completed_today
        actual.append(max(remaining, 0))

    return days, ideal, actual, total_points


def plot_curve(ax, days, ideal, actual):
    x = list(range(len(days)))
    ax.plot(x, ideal, linestyle="--", color="#9CA3AF", label="Ideal")
    ax.step(x, actual, where="post", color="#2563EB", label="Actual")
    ax.grid(alpha=0.3)


def generate_per_sprint_charts(sprints):
    for sprint in sprints:
        days, ideal, actual, total_points = sprint_curves(sprint)

        fig, ax = plt.subplots(figsize=(5, 3))
        plot_curve(ax, days, ideal, actual)
        ax.set_title(f"{sprint['name']} burndown ({total_points} pts)", fontsize=10)
        ax.set_xlabel("Day", fontsize=8)
        ax.set_ylabel("Remaining points", fontsize=8)
        ax.tick_params(labelsize=7)
        ax.legend(fontsize=8)
        fig.tight_layout()

        out_path = DIAGRAMS_DIR / f"burndown-{sprint['id'].lower()}.svg"
        fig.savefig(out_path, format="svg")
        plt.close(fig)
        print(f"Wrote {out_path}")


def generate_global_chart(sprints):
    project_start = parse(sprints[0]["period_start"])
    project_end = parse(sprints[-1]["period_end"])
    all_tasks = [t for s in sprints for t in s["tasks"]]
    total_points = sum(t["points"] for t in all_tasks)
    days = [project_start + timedelta(days=n) for n in range((project_end - project_start).days + 1)]

    ideal = [
        total_points * (1 - n / (len(days) - 1)) if len(days) > 1 else 0
        for n in range(len(days))
    ]

    actual = []
    remaining = total_points
    for day in days:
        completed_today = sum(t["points"] for t in all_tasks if parse(t["end"]) == day)
        remaining -= completed_today
        actual.append(max(remaining, 0))

    fig, ax = plt.subplots(figsize=(13, 5))

    tick_positions = []
    tick_labels = []
    for color, sprint in zip(SPRINT_BANDS, sprints):
        s_start = (parse(sprint["period_start"]) - project_start).days
        s_end = (parse(sprint["period_end"]) - project_start).days
        ax.axvspan(s_start, s_end, color=color, zorder=0)
        mid = (s_start + s_end) / 2
        ax.text(mid, total_points * 1.02, sprint["name"], ha="center", fontsize=8, color="#374151")
        tick_positions.append(s_start)
        tick_labels.append(sprint["period_start"])

    plot_curve(ax, days, ideal, actual)
    ax.set_xticks(tick_positions)
    ax.set_xticklabels(tick_labels, rotation=30, ha="right", fontsize=7)
    ax.set_xlim(0, len(days) - 1)
    ax.set_ylim(0, total_points * 1.1)
    ax.set_ylabel("Remaining points", fontsize=9)
    ax.set_title(f"Project burndown — Sprint 0 to Sprint 5 ({total_points} pts total)", fontsize=11)
    ax.legend(fontsize=9, loc="upper right")
    fig.tight_layout()

    out_path = DIAGRAMS_DIR / "burndown-global.svg"
    fig.savefig(out_path, format="svg")
    plt.close(fig)
    print(f"Wrote {out_path}")


def main():
    data = json.loads(DATA_PATH.read_text())
    sprints = data["sprints"]
    DIAGRAMS_DIR.mkdir(parents=True, exist_ok=True)

    generate_per_sprint_charts(sprints)
    generate_global_chart(sprints)


if __name__ == "__main__":
    main()
