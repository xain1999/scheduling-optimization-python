"""Gantt chart helper used for every schedule figure in the book.

The palette is chosen so that bars stay distinguishable when the book
is printed in black and white, and each bar carries its job label.
"""
from __future__ import annotations

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt

from .core import Task

# Embed TrueType fonts in PDFs (required for print-on-demand)
matplotlib.rcParams["pdf.fonttype"] = 42
matplotlib.rcParams["ps.fonttype"] = 42
# DejaVu Sans ships with matplotlib: figures look the same everywhere
matplotlib.rcParams["font.family"] = "DejaVu Sans"
matplotlib.rcParams["font.size"] = 8.5
# Legible in print: text is set at 8 pt or more (math subscripts,
# drawn smaller by matplotlib, at about 7 pt).
for key in ("xtick.labelsize", "ytick.labelsize", "legend.fontsize"):
    matplotlib.rcParams[key] = 8

# Light-to-mid tones with distinct luminance: readable in greyscale
PALETTE = ["#D9E6F2", "#A9C4DE", "#F2DDC4", "#C7DDB8", "#E6C9D9",
           "#BFBFBF", "#F2EBB8", "#B8D8D8", "#DDC4F2", "#E0E0E0"]


# [start:gantt]
def plot_gantt(schedule: list[Task], title: str = "",
               due: dict[str, int] | None = None,
               ax=None, filename: str | None = None,
               width: float = 4.4, height: float | None = None):
    """Draw a schedule as a Gantt chart (one row per resource)."""
    resources = sorted({t.resource for t in schedule}, reverse=True)
    jobs = sorted({t.job for t in schedule},
                  key=lambda s: (len(s), s))
    colour = {j: PALETTE[i % len(PALETTE)] for i, j in enumerate(jobs)}
    row = {r: i for i, r in enumerate(resources)}

    if ax is None:
        h = height or 0.6 + 0.5 * len(resources)
        fig, ax = plt.subplots(figsize=(width, h))
    else:
        fig = ax.figure

    horizon = max(t.end for t in schedule)
    # width of one character of a 6 pt label, in time units
    axes_in = ax.get_position().width * fig.get_figwidth()
    char = 8 * 0.62 / 72 * (horizon * 1.02) / axes_in
    placed = {}                     # (row, side) -> right end of label
    for t in sorted(schedule, key=lambda t: t.start):
        y = row[t.resource]
        ax.barh(y, t.end - t.start, left=t.start, height=0.62,
                color=colour[t.job], edgecolor="#333333",
                linewidth=0.6)
        mid = (t.start + t.end) / 2
        if (t.end - t.start) >= 1.15 * char * len(t.job):
            ax.text(mid, y, t.job, ha="center", va="center",
                    fontsize=8)
            continue
        # bar too narrow: label below (or above, if that collides),
        # tied to its bar by a short leader line
        half = char * len(t.job) / 2
        for sign, side, va in ((-1, "below", "top"),
                               (1, "above", "bottom")):
            if placed.get((y, side), -1e9) < mid - half:
                break
        placed[y, side] = mid + half + char * 0.5
        ax.plot([mid, mid], [y + sign * 0.31, y + sign * 0.42],
                color="#333333", linewidth=0.6)
        ax.text(mid, y + sign * 0.43, t.job, ha="center", va=va,
                fontsize=8)

    if due:  # mark due dates of late jobs with a small tick
        end_of = {}
        for t in schedule:
            end_of[t.job] = max(end_of.get(t.job, 0), t.end)
        for j, d in due.items():
            if j in end_of and end_of[j] > d:
                res = next(t.resource for t in schedule if t.job == j)
                y = row[res]
                ax.plot([d, d], [y + 0.34, y + 0.46], color="#000000",
                        linewidth=0.9)

    ax.set_yticks(range(len(resources)), resources)
    top = len(resources) - 1               # room for labels above it
    above = any(side == "above" and y == top for y, side in placed)
    ax.set_ylim(-0.8, top + (0.85 if above else 0.55))
    ax.set_xlim(0, horizon * 1.02)
    ax.set_xlabel("time")
    ax.spines[["top", "right"]].set_visible(False)
    ax.tick_params(axis="y", length=0)
    if title:
        ax.set_title(title, loc="left", fontsize=10)
    if filename:
        fig.tight_layout()
        fig.savefig(filename, bbox_inches="tight")
        plt.close(fig)
    return ax
# [end:gantt]
