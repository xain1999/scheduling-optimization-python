"""Chapter 17: architecture diagram of a scheduling system."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch

import schedlib.gantt  # noqa: F401  (fonts and PDF settings)

OUT = Path(__file__).resolve().parents[2] / "figures"

BOXES = {
    "ERP / MES /\nspreadsheets": (0.0, 2.3, "#E0E0E0"),
    "data layer\nload, clean,\ncheck": (1.65, 2.3, "#D9E6F2"),
    "model layer\nCP-SAT or\nMILP": (3.3, 2.3, "#D9E6F2"),
    "solver\n(time limit)": (4.95, 2.3, "#F2DDC4"),
    "validator\nindependent\nchecks": (4.95, 0.9, "#C7DDB8"),
    "API\nFastAPI\nservice": (3.3, 0.9, "#D9E6F2"),
    "planners' UI\nGantt, edits": (1.65, 0.9, "#E6C9D9"),
    "log & KPIs\nevery run\nstored": (0.0, 0.9, "#E0E0E0"),
}


W, HGT = 1.42, 0.8


def arrow(ax, a, b):
    """Connect box edges: horizontally within a row, else vertically."""
    (x1, y1, _), (x2, y2, _) = BOXES[a], BOXES[b]
    if y1 == y2:
        if x2 > x1:
            start, end = (x1 + W, y1 + HGT / 2), (x2, y2 + HGT / 2)
        else:
            start, end = (x1, y1 + HGT / 2), (x2 + W, y2 + HGT / 2)
    else:
        start, end = (x1 + W / 2, y1), (x2 + W / 2, y2 + HGT)
    ax.annotate("", xy=end, xytext=start,
                arrowprops=dict(arrowstyle="-|>", lw=0.8, color="#333"))


fig, ax = plt.subplots(figsize=(4.5, 2.7))
for label, (x, y, c) in BOXES.items():
    ax.add_patch(FancyBboxPatch((x, y), W, HGT,
                                boxstyle="round,pad=0.02,rounding_size=0.06",
                                facecolor=c, edgecolor="#333", lw=0.7))
    ax.text(x + W / 2, y + HGT / 2, label, ha="center", va="center",
            fontsize=8, linespacing=1.15)
names = list(BOXES)
for a, b in zip(names, names[1:]):
    arrow(ax, a, b)
ax.set_xlim(-0.05, 6.45)
ax.set_ylim(0.8, 3.2)
ax.axis("off")
fig.tight_layout()
fig.savefig(OUT / "ch17_architecture.pdf", bbox_inches="tight")
