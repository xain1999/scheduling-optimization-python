"""Chapter 8: figure: an optimal ft06 schedule with its critical path."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import matplotlib.pyplot as plt

from schedlib import Task
from schedlib.gantt import plot_gantt
from cpsat_jobshop import sequences_from_starts, solve_jobshop
from jobshop import critical_path, read_instance

OUT = Path(__file__).resolve().parents[2] / "figures"

jobs = read_instance("ft06")
res = solve_jobshop(jobs, time_limit=10)
cmax, _, path = critical_path(jobs, sequences_from_starts(jobs,
                                                          res["starts"]))
tasks = [Task(f"J{j+1}", f"M{jobs[j][k][0] + 1}", s, s + jobs[j][k][1])
         for (j, k), s in res["starts"].items()]
fig, ax = plt.subplots(figsize=(4.6, 2.6))
plot_gantt(tasks, ax=ax, title=f"ft06, makespan {cmax}")
order = sorted({t.resource for t in tasks}, reverse=True)
row = {r: i for i, r in enumerate(order)}
for (j, k) in path:                     # outline critical operations
    s = res["starts"][j, k]
    d = jobs[j][k][1]
    y = row[f"M{jobs[j][k][0] + 1}"]
    ax.add_patch(plt.Rectangle((s, y - 0.31), d, 0.62, fill=False,
                               edgecolor="black", lw=1.8))
fig.tight_layout()
fig.savefig(OUT / "ch08_ft06.pdf", bbox_inches="tight")
print("critical path:", path)
