"""Chapter 2 -- generate the figures used in the text."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
sys.path.insert(0, str(Path(__file__).resolve().parent))

import matplotlib.pyplot as plt

from cpsat_model import solve_cpsat
from instances import JOBS, random_instance
from parallel_cpsat import solve_parallel
from schedlib import evaluate, sequence_to_schedule
from schedlib.gantt import plot_gantt
from schedlib.results import load

OUT = Path(__file__).resolve().parents[2] / "figures"
OUT.mkdir(exist_ok=True)


def single_machine_figure():
    # the optimal schedule printed in the text (saved by cpsat_model.py)
    order = load("ch02_single") or ["J1", "J3", "J7", "J5", "J6", "J4",
                                    "J2", "J8"]
    schedule = sequence_to_schedule(JOBS, order)
    assert evaluate(JOBS, schedule)["sumwT"] == solve_cpsat(JOBS).objective
    fig, ax = plt.subplots(figsize=(4.4, 1.7))
    plot_gantt(schedule, ax=ax, due={j.id: j.d for j in JOBS})
    # release dates as small triangles in their own band, below the
    # labels of narrow bars
    for j in JOBS:
        ax.plot(j.r, -0.9, marker="^", color="#333333", markersize=3.5)
    ax.set_ylim(-1.05, 0.6)
    ax.set_xlabel("time (hours)   ▲ = release date,  | = due date of a late job")
    fig.tight_layout()
    fig.savefig(OUT / "ch02_optimal_single.pdf", bbox_inches="tight")
    plt.close(fig)


def parallel_figure():
    jobs = random_instance(12, seed=7, spread=0.3, slack=0.2)
    schedule = load("ch02_parallel")       # same solution as the console
    if schedule is None:
        schedule, _ = solve_parallel(jobs, ["M1", "M2"])
    k = evaluate(jobs, schedule)
    plot_gantt(schedule, due={j.id: j.d for j in jobs},
               title=f"Two machines: $\\sum w_jT_j$ = {k['sumwT']}",
               filename=OUT / "ch02_parallel.pdf")


if __name__ == "__main__":
    single_machine_figure()
    parallel_figure()
    print("figures written to", OUT)
