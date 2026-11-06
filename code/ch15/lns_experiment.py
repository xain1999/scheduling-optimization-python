"""Chapter 15: LNS versus one big CP-SAT run on a 50 x 15 job shop."""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "ch08"))

from ortools.sat.python import cp_model

from cpsat_jobshop import solve_jobshop
from giffler_thompson import giffler_thompson, rules
from lns_jobshop import lns, random_jobshop


class Recorder(cp_model.CpSolverSolutionCallback):
    def __init__(self):
        super().__init__()
        self.history = []

    def on_solution_callback(self):
        self.history.append((self.wall_time, self.objective_value))


ROOT = Path(__file__).resolve().parents[2]
# [start:experiment]
out = {}
for n, m in [(50, 15), (30, 30)]:
    jobs = random_jobshop(n, m)
    gt, _ = giffler_thompson(jobs, rules(jobs)["MWKR"])
    direct = solve_jobshop(jobs, time_limit=60)
    hist = []
    best, _ = lns(jobs, seconds=60, history=hist)
    out[f"{n}x{m}"] = dict(gt=gt, direct=direct["makespan"],
                           bound=direct["bound"], lns=best,
                           history=hist)
    print(n, m, "GT", gt, "CP-SAT", direct["makespan"], "bound",
          direct["bound"], "LNS", best, flush=True)
# [end:experiment]
(ROOT / "results" / "ch15_lns.json").write_text(json.dumps(out))
