"""Chapter 13: serial vs parallel SGS, rules, sampling, CP-SAT."""
import csv
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "ch09"))

from rcpsp import random_project, serial_sgs, solve_rcpsp
from sgs import parallel_sgs, priority_rules, random_sampling

ROOT = Path(__file__).resolve().parents[2]
rows = []
for seed in range(1, 11):
    project, cap = random_project(60, seed=seed, strength=0.15)
    rules = priority_rules(project)
    row = dict(seed=seed)
    for name, rule in rules.items():
        row[f"serial {name}"] = serial_sgs(project, cap, rule)[0]
        row[f"parallel {name}"] = parallel_sgs(project, cap, rule)[0]
    row["sampling"] = random_sampling(project, cap, rules["LFT"], n=200)[0]
    r = solve_rcpsp(project, cap, time_limit=20)
    row["cpsat"], row["bound"] = r["makespan"], r["bound"]
    rows.append(row)
    print(row, flush=True)
with open(ROOT / "results" / "ch13_sgs.csv", "w", newline="") as f:
    w = csv.DictWriter(f, fieldnames=rows[0].keys())
    w.writeheader()
    w.writerows(rows)
