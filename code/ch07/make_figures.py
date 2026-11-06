"""Chapter 7: figure: a permutation flow-shop schedule."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import matplotlib.pyplot as plt

from schedlib import Task
from schedlib.gantt import plot_gantt
from flowshop import makespan, taillard_instance
from neh import neh

OUT = Path(__file__).resolve().parents[2] / "figures"


def tasks_for(p, order):
    m = len(p)
    t = [0] * m
    out = []
    for j in order:
        for i in range(m):
            s = max(t[i], t[i - 1] if i else 0)
            out.append(Task(f"J{j+1}", f"M{i+1}", s, s + p[i][j]))
            t[i] = s + p[i][j]
    return out


p = taillard_instance(20261021, 8, 4)
seq = neh(p)
fig, ax = plt.subplots(figsize=(4.6, 2.1))
plot_gantt(tasks_for(p, seq), ax=ax,
           title=f"NEH sequence, makespan {makespan(p, seq)}")
fig.tight_layout()
fig.savefig(OUT / "ch07_flowshop.pdf", bbox_inches="tight")
print(seq, makespan(p, seq))
