"""Chapter 9: renovation schedule with crew profiles."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import matplotlib.pyplot as plt

from schedlib.gantt import PALETTE
from rcpsp import solve_rcpsp
from renovation import CREWS, PROJECT

OUT = Path(__file__).resolve().parents[2] / "figures"

res = solve_rcpsp(PROJECT, CREWS, time_limit=20)
st = res["starts"]
T = res["makespan"]
fig, axes = plt.subplots(4, 1, figsize=(4.6, 5.0), sharex=True,
                         gridspec_kw=dict(height_ratios=[4, 1, 1, 1]))
ax = axes[0]
order = sorted(PROJECT, key=lambda a: st[a])
for k, a in enumerate(order):
    d = PROJECT[a][0]
    ax.barh(len(order) - 1 - k, d, left=st[a], height=0.6,
            color=PALETTE[k % len(PALETTE)], edgecolor="#333", lw=0.5)
    ax.text(st[a] + d + 0.4, len(order) - 1 - k, a.replace("_", " "),
            va="center", fontsize=8)
ax.set_yticks([])
ax.spines[["top", "right", "left"]].set_visible(False)
ax.set_title(f"renovation, {T} days", loc="left", fontsize=9)
for ax, r in zip(axes[1:], ["carp", "plumb", "elec"]):
    usage = [sum(PROJECT[a][1].get(r, 0) for a in PROJECT
                 if st[a] <= t < st[a] + PROJECT[a][0]) for t in range(T)]
    ax.bar(range(T), usage, width=1.0, align="edge", color="#BFBFBF",
           edgecolor="#333", lw=0.3)
    ax.axhline(CREWS[r], ls="--", color="black", lw=0.8)
    ax.set_ylabel(r, fontsize=8)
    ax.set_ylim(0, CREWS[r] + 0.5)
    ax.spines[["top", "right"]].set_visible(False)
axes[-1].set_xlabel("day")
axes[0].set_xlim(0, T + 9)
fig.tight_layout()
fig.savefig(OUT / "ch09_renovation.pdf", bbox_inches="tight")
