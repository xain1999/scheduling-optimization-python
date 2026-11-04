"""Chapter 6 -- figures."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import matplotlib.pyplot as plt

from schedlib.gantt import plot_gantt
from schedlib.results import load
from gpu_cluster import greedy, optimise, training_jobs, weighted_flow

OUT = Path(__file__).resolve().parents[2] / "figures"

jobs = training_jobs()
saved = load("ch06_gpu")                   # same plans as the console
if saved:
    base, plan = saved["greedy"], saved["cpsat"]
else:
    base = greedy(jobs)
    plan, _, _ = optimise(jobs, hint_plan=base)
fig, axes = plt.subplots(2, 1, figsize=(4.6, 5.6), sharex=True)
plot_gantt(base, ax=axes[0],
           title=f"Greedy (FIFO, earliest finish): weighted flow "
                 f"{weighted_flow(jobs, base)}")
plot_gantt(plan, ax=axes[1],
           title=f"CP-SAT: weighted flow {weighted_flow(jobs, plan)}")
axes[0].set_xlabel("")
axes[1].set_xlabel("hours")
fig.tight_layout()
fig.savefig(OUT / "ch06_gpu.pdf", bbox_inches="tight")
