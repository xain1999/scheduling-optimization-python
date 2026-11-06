"""Chapter 1: generate the figures used in the text."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
sys.path.insert(0, str(Path(__file__).resolve().parent))

import matplotlib.pyplot as plt

from brute_force import brute_force
from dispatching_rules import RULES, apply_rule
from print_shop import JOBS
from schedlib import Task, evaluate, sequence_to_schedule
from schedlib.gantt import plot_gantt

OUT = Path(__file__).resolve().parents[2] / "figures"
OUT.mkdir(exist_ok=True)
due = {j.id: j.d for j in JOBS}


def rules_figure():
    _, opt_order = brute_force(JOBS, "sumwT")
    panels = [("SPT", apply_rule(RULES["SPT"])),
              ("EDD", apply_rule(RULES["EDD"])),
              ("Optimal for weighted tardiness", opt_order)]
    fig, axes = plt.subplots(3, 1, figsize=(4.4, 3.3), sharex=True)
    for ax, (name, order) in zip(axes, panels):
        sched = sequence_to_schedule(JOBS, order)
        k = evaluate(JOBS, sched)
        plot_gantt(sched, ax=ax, due=due,
                   title=f"{name}:  $\\sum w_jT_j$ = {k['sumwT']},  "
                         f"$L_{{\\max}}$ = {k['Lmax']}")
        ax.set_xlabel("")
    axes[-1].set_xlabel("time (hours)")
    fig.tight_layout()
    fig.savefig(OUT / "ch01_rules_gantt.pdf", bbox_inches="tight")
    plt.close(fig)


def exchange_figure():
    """Two schedules that differ only by swapping adjacent jobs i and j."""
    a = [Task("A", "S", 0, 4), Task("i", "S", 4, 9), Task("j", "S", 9, 11),
         Task("B", "S", 11, 15)]
    b = [Task("A", "S'", 0, 4), Task("j", "S'", 4, 6), Task("i", "S'", 6, 11),
         Task("B", "S'", 11, 15)]
    fig, ax = plt.subplots(figsize=(4.4, 1.25))
    plot_gantt(a + b, ax=ax)
    ax.set_xticks([0, 4, 6, 9, 11, 15],
                  ["0", "$t$", "", "", "$t+p_i+p_j$", ""], fontsize=10)
    ax.set_xlabel("")
    fig.tight_layout()
    fig.savefig(OUT / "ch01_exchange.pdf", bbox_inches="tight")
    plt.close(fig)


if __name__ == "__main__":
    rules_figure()
    exchange_figure()
    print("figures written to", OUT)
