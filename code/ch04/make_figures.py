"""Chapter 4 -- figures."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle
from ortools.sat.python import cp_model

from schedlib import Task
from schedlib.gantt import PALETTE, plot_gantt
from schedlib.results import load
from berth_2d import QUAY, ships, solve_berths
from cumulative_crew import TASKS, CREW, solve_crew
from paint_shop import ProgressLogger, build, paint_jobs

OUT = Path(__file__).resolve().parents[2] / "figures"


def crew_figure():
    saved = load("ch04_crew")              # same plan as the console
    if saved:
        plan = {t: tuple(se) for t, se in saved["plan"].items()}
        makespan = saved["makespan"]
    else:
        plan, makespan = solve_crew()
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(4.4, 3.2), sharex=True,
                                   gridspec_kw=dict(height_ratios=[2, 1]))
    # stack tasks on rows so overlapping tasks are visible
    rows = []
    tasks = []
    for t, (s, e) in sorted(plan.items(), key=lambda kv: kv[1]):
        for r, free_at in enumerate(rows):
            if free_at <= s:
                rows[r] = e
                break
        else:
            rows.append(e)
            r = len(rows) - 1
        tasks.append(Task(f"{t}({TASKS[t][1]})", f"row {r + 1}", s, e))
    plot_gantt(tasks, ax=ax1)
    ax1.set_yticks([]); ax1.set_xlabel("")
    ax1.set_title("tasks (people needed)", loc="left", fontsize=8.5)
    usage = [sum(TASKS[t][1] for t, (s, e) in plan.items() if s <= u < e)
             for u in range(makespan)]
    ax2.bar(range(makespan), usage, width=1.0, align="edge",
            color="#BFBFBF", edgecolor="#333", lw=0.5)
    ax2.axhline(CREW, color="black", lw=0.9, ls="--")
    ax2.set_ylabel("people"); ax2.set_xlabel("time (hours)")
    ax2.set_ylim(0, CREW + 0.6)
    ax2.spines[["top", "right"]].set_visible(False)
    fig.tight_layout()
    fig.savefig(OUT / "ch04_crew.pdf", bbox_inches="tight")
    plt.close(fig)


def berth_figure():
    fleet = ships()
    plan = load("ch04_berths")             # same plan as the console
    if plan is None:
        plan, _, _ = solve_berths(fleet)
    fig, ax = plt.subplots(figsize=(4.4, 2.6))
    for k, s in enumerate(fleet):
        t, x = plan[s["name"]]
        ax.add_patch(Rectangle((t, x), s["hours"], s["length"],
                               facecolor=PALETTE[k % len(PALETTE)],
                               edgecolor="#333", lw=0.6))
        ax.text(t + s["hours"] / 2, x + s["length"] / 2, s["name"],
                ha="center", va="center", fontsize=8)
        ax.plot([s["arrival"], t], [x + s["length"] / 2] * 2,
                color="#777", lw=0.6, ls=":")
    horizon = max(plan[s["name"]][0] + s["hours"] for s in fleet)
    ax.set_xlim(0, horizon + 1); ax.set_ylim(0, QUAY)
    ax.set_xlabel("time (hours)"); ax.set_ylabel("quay position")
    ax.spines[["top", "right"]].set_visible(False)
    fig.tight_layout()
    fig.savefig(OUT / "ch04_berths.pdf", bbox_inches="tight")
    plt.close(fig)


def convergence_figure():
    jobs = paint_jobs()
    m, start, tardiness, setups = build(jobs)
    m.minimize(tardiness)
    solver = cp_model.CpSolver()
    solver.parameters.max_time_in_seconds = 30
    solver.parameters.num_workers = 8
    logger = ProgressLogger()
    solver.solve(m, logger)
    hist = logger.history + [(solver.wall_time, solver.objective_value,
                              solver.best_objective_bound)]
    t = [h[0] for h in hist]
    fig, ax = plt.subplots(figsize=(4.4, 2.2))
    ax.step(t, [h[1] for h in hist], where="post", color="black", lw=1,
            label="best schedule found")
    ax.step(t, [h[2] for h in hist], where="post", color="#777", lw=1,
            ls="--", label="proven lower bound")
    ax.set_xscale("log")
    ax.xaxis.set_major_formatter(          # 0.1, 1, 10: no tiny exponents
        plt.FuncFormatter(lambda v, _: f"{v:g}"))
    ax.set_xlabel("seconds (log scale)")
    ax.set_ylabel("weighted tardiness")
    ax.legend(frameon=False, fontsize=8)
    ax.spines[["top", "right"]].set_visible(False)
    fig.tight_layout()
    fig.savefig(OUT / "ch04_convergence.pdf", bbox_inches="tight")
    plt.close(fig)
    print("solutions:", len(logger.history), "final", hist[-1])


if __name__ == "__main__":
    crew_figure()
    berth_figure()
    convergence_figure()
