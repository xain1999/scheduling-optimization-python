"""Chapter 3 -- watch HiGHS work: print the solver log of a MILP."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "ch02"))

from instances import random_instance
from milp_disjunctive import solve_disjunctive

# [start:log]
jobs = random_instance(12, seed=2)
res = solve_disjunctive(jobs, time_limit=60, msg=True)  # msg=True: log
print("objective", res.objective, "bound", res.bound)
# [end:log]
