"""Chapter 16 -- distribution of simulated weighted tardiness."""
import random
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import matplotlib.pyplot as plt

import schedlib.gantt  # noqa: F401
from schedlib.results import load
from robust import (instance, optimise_order, sample_durations, simulate,
                    uncertainty)

ROOT = Path(__file__).resolve().parents[2]
jobs = instance()
cv = uncertainty(jobs)
rng = random.Random(1)
plan = [{j.id: j.p for j in jobs}]
train = [sample_durations(jobs, rng, cv) for _ in range(30)]
test = [sample_durations(jobs, rng, cv) for _ in range(2000)]
saved = load("ch16_robust")                # same orders as the console
if saved:
    det_order, rob_order = saved["deterministic"], saved["robust"]
else:
    det_order = optimise_order(jobs, plan)
    rob_order = optimise_order(jobs, train, time_limit=60)
det = simulate(jobs, det_order, test)
rob = simulate(jobs, rob_order, test)
fig, ax = plt.subplots(figsize=(4.4, 2.3))
bins = range(0, max(det + rob) + 10, 10)
ax.hist(det, bins=bins, histtype="step", color="black", lw=1,
        label="deterministic sequence")
ax.hist(rob, bins=bins, histtype="stepfilled", color="#BFBFBF",
        alpha=0.8, label="robust sequence")
ax.set_xlabel("weighted tardiness in a simulated day")
ax.set_ylabel("scenarios")
ax.legend(frameon=False, fontsize=8)
ax.spines[["top", "right"]].set_visible(False)
fig.tight_layout()
fig.savefig(ROOT / "figures" / "ch16_robust.pdf", bbox_inches="tight")
