"""Chapter 5: CP-SAT on 40 jobs, with and without an ATC warm start."""
import csv
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "ch02"))
sys.path.insert(0, str(Path(__file__).resolve().parent))

from ortools.sat.python import cp_model

from atc import best_atc
from cpsat_model import build_cpsat
from schedlib import evaluate, sequence_to_schedule
from wt_instances import instance_seed, wt_instance
from schedlib.status import check_cpsat

ROOT = Path(__file__).resolve().parents[2]


# [start:hint]
def cpsat_with_hint(jobs, order, time_limit=20):
    model, start = build_cpsat(jobs)
    for t in sequence_to_schedule(jobs, order):   # warm start from ATC
        model.add_hint(start[t.job], t.start)
    solver = cp_model.CpSolver()
    solver.parameters.max_time_in_seconds = time_limit
    solver.parameters.num_workers = 8
    check_cpsat(solver, solver.solve(model))  # a hint is no guarantee
    return solver.objective_value, solver.best_objective_bound
# [end:hint]


rows = []
for tf in (0.4, 0.6, 0.8):
    for rdd in (0.2, 0.6, 1.0):
        jobs = wt_instance(40, tf, rdd, instance_seed(tf, rdd, 7))
        order = best_atc(jobs)
        atc = evaluate(jobs, sequence_to_schedule(jobs, order))["sumwT"]
        value, bound = cpsat_with_hint(jobs, order)
        rows.append(dict(tf=tf, rdd=rdd, atc=atc, hinted=value,
                         bound=bound))
        print(rows[-1], flush=True)
with open(ROOT / "results" / "ch05_large_hint.csv", "w", newline="") as f:
    w = csv.DictWriter(f, fieldnames=rows[0].keys())
    w.writeheader()
    w.writerows(rows)
