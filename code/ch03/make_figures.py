"""Chapter 3 -- figures."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import matplotlib.pyplot as plt
import numpy as np
import pulp

import schedlib.gantt  # noqa: F401  (sets fonts and PDF options)
from schedlib.gantt import PALETTE
from lot_sizing import build, random_data

OUT = Path(__file__).resolve().parents[2] / "figures"


def lp_geometry():
    fig, ax = plt.subplots(figsize=(4.0, 3.0))
    a = np.linspace(0, 60, 400)
    ax.plot(a, (120 - 2 * a) / 3, color="#333", lw=1)
    ax.plot(a, 80 - 2 * a, color="#333", lw=1, ls="--")
    ax.axhline(30, color="#333", lw=1, ls=":")
    poly = np.array([[0, 0], [40, 0], [30, 20], [15, 30], [0, 30]])
    ax.fill(poly[:, 0], poly[:, 1], color="#D9E6F2", zorder=0)
    for k in (900, 1300, 1700):
        ax.plot(a, (k - 30 * a) / 40, color="#888", lw=0.6)
        ax.text(2, (k - 60) / 40 + 0.8, f"profit {k}", fontsize=8,
                color="#555")
    ax.plot(30, 20, "o", color="black", ms=4)
    ax.annotate("optimum (30, 20)", (30, 20), (34, 26), fontsize=8.5,
                arrowprops=dict(arrowstyle="-", lw=0.6))
    for (x, y) in poly[1:4]:
        ax.plot(x, y, "o", color="#555", ms=2.5)
    ax.text(41, 3, "cutter", fontsize=8)
    ax.text(48, 7.5, "press", fontsize=8)
    ax.text(45, 31, "demand", fontsize=8)
    ax.set_xlim(0, 60); ax.set_ylim(0, 45)
    ax.set_xlabel("brochure batches $a$")
    ax.set_ylabel("catalogue batches $b$")
    ax.spines[["top", "right"]].set_visible(False)
    fig.tight_layout()
    fig.savefig(OUT / "ch03_lp_geometry.pdf", bbox_inches="tight")
    plt.close(fig)


def lot_sizing_plan():
    data = random_data(n_products=8, n_periods=15)
    m = build(data, "tight")
    m.solve(pulp.HiGHS(msg=False, threads=1))
    var = {v.name: v.value() for v in m.variables()}
    T = data.periods
    fig, ax = plt.subplots(figsize=(4.4, 2.9))
    bottom = np.zeros(len(T))
    # hatching and direct labels keep products apart in greyscale print
    hatches = ["", "////", "....", "xxx", "\\\\\\", "---", "ooo", "++"]
    for k, i in enumerate(data.products):
        hours = np.array([data.unit_time[i] * var[f"x_{i}_{t}"] +
                          data.setup_time[i] * round(var[f"y_{i}_{t}"])
                          for t in T])
        ax.bar(T, hours, bottom=bottom, color=PALETTE[k],
               hatch=hatches[k % len(hatches)], edgecolor="#333",
               lw=0.4, label=i)
        for t, h, b in zip(T, hours, bottom):
            if h >= 45:                       # room for a label
                ax.text(t, b + h / 2, i, ha="center", va="center",
                        fontsize=8, bbox=dict(boxstyle="square,pad=0.1",
                                              fc="white", ec="none"))
        bottom += hours
    ax.plot(T, [data.capacity[t] for t in T], color="black", lw=0.9,
            drawstyle="steps-mid", label="capacity")
    ax.set_xlabel("week"); ax.set_ylabel("press hours")
    ax.set_xticks(T)
    ax.set_ylim(0, 1.6 * max(data.capacity.values()))
    ax.legend(ncol=4, fontsize=8, frameon=False, loc="upper center")
    ax.spines[["top", "right"]].set_visible(False)
    fig.tight_layout()
    fig.savefig(OUT / "ch03_lot_sizing.pdf", bbox_inches="tight")
    plt.close(fig)


if __name__ == "__main__":
    lp_geometry()
    lot_sizing_plan()
