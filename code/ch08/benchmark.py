"""Chapter 8: priority rules, MILP and CP-SAT on classic benchmarks."""
import csv
from pathlib import Path

from milp_jobshop import milp_jobshop             # import before ortools
from cpsat_jobshop import solve_jobshop
from giffler_thompson import giffler_thompson, rules
from jobshop import known_optimum, read_instance

ROOT = Path(__file__).resolve().parents[2]
NAMES = ["ft06", "la01", "la02", "la03", "la04", "la05", "ft10", "ft20",
         "la16", "la17", "la18", "la19", "la20", "abz5", "abz6", "orb01"]

# [start:bench]
rows = []
for name in NAMES:
    jobs = read_instance(name)
    best_rule = min(giffler_thompson(jobs, r)[0]
                    for r in rules(jobs).values())
    cp = solve_jobshop(jobs, time_limit=60)
    mi = (milp_jobshop(jobs, time_limit=60)
          if name in ("ft06", "la01", "ft10") else None)
    rows.append(dict(name=name, n=len(jobs), m=len(jobs[0]),
                     opt=known_optimum(name), rule=best_rule,
                     cpsat=cp["makespan"], cp_opt=cp["optimal"],
                     cp_sec=round(cp["seconds"], 1),
                     milp=mi["makespan"] if mi else "",
                     milp_opt=mi["optimal"] if mi else "",
                     milp_sec=round(mi["seconds"], 1) if mi else ""))
    print(rows[-1], flush=True)
# [end:bench]

(ROOT / "results").mkdir(exist_ok=True)
with open(ROOT / "results" / "ch08_bench.csv", "w", newline="") as f:
    w = csv.DictWriter(f, fieldnames=rows[0].keys())
    w.writeheader()
    w.writerows(rows)
