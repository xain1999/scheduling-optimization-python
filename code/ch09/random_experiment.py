"""Chapter 9: CPM, serial SGS and CP-SAT on random projects."""
import csv
from pathlib import Path

from rcpsp import random_project, serial_sgs, solve_rcpsp
from renovation import critical_path_method

ROOT = Path(__file__).resolve().parents[2]

# [start:experiment]
rows = []
for n in (30, 60):
    for strength in (0.1, 0.3, 0.6):
        for seed in (1, 2):
            project, cap = random_project(n, seed=seed,
                                          strength=strength)
            cpm, table = critical_path_method(project)
            lft = {a: table[a][1] + project[a][0] for a in project}
            sgs, _ = serial_sgs(project, cap, lambda a: lft[a])
            r = solve_rcpsp(project, cap, time_limit=20)
            rows.append(dict(n=n, strength=strength, seed=seed,
                             cpm=cpm, sgs=sgs, cpsat=r["makespan"],
                             bound=r["bound"], optimal=r["optimal"],
                             seconds=round(r["seconds"], 1)))
            print(rows[-1], flush=True)
# [end:experiment]

with open(ROOT / "results" / "ch09_random.csv", "w", newline="") as f:
    w = csv.DictWriter(f, fieldnames=rows[0].keys())
    w.writeheader()
    w.writerows(rows)
