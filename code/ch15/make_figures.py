"""Chapter 15 -- LNS convergence (from results/ch15_lns.json)."""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import matplotlib.pyplot as plt

import schedlib.gantt  # noqa: F401

ROOT = Path(__file__).resolve().parents[2]
data = json.loads((ROOT / "results" / "ch15_lns.json").read_text())["30x30"]
hist = data["history"]
fig, ax = plt.subplots(figsize=(4.4, 2.3))
ax.step([h[0] for h in hist], [h[1] for h in hist], where="post",
        color="black", lw=1, label="LNS (best so far)")
ax.axhline(data["direct"], color="#555", ls="--", lw=1,
           label="one CP-SAT run, 60 s")
ax.axhline(data["bound"], color="#999", ls=":", lw=1,
           label="CP-SAT lower bound")
ax.set_xlabel("seconds"); ax.set_ylabel("makespan")
ax.legend(frameon=False, fontsize=8)
ax.spines[["top", "right"]].set_visible(False)
fig.tight_layout()
fig.savefig(ROOT / "figures" / "ch15_lns.pdf", bbox_inches="tight")
