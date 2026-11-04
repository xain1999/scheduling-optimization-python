"""Chapter 2 -- MILP model 1: start times + disjunctive (big-M) ordering."""
import sys
import time
from itertools import combinations
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
sys.path.insert(0, str(Path(__file__).resolve().parent))

import pulp

from instances import JOBS, horizon
from schedlib import (Job, SolveResult, Task, evaluate,
                      validate_single_machine)


# [start:model]
def build_disjunctive(jobs: list[Job], relax: bool = False):
    H = horizon(jobs)
    M = H                         # big-M: see 'Choosing M'
    model = pulp.LpProblem("wT_disjunctive", pulp.LpMinimize)

    # Decision variables
    S = {j.id: model.add_variable(f"S_{j.id}", lowBound=j.r,
                                  upBound=H - j.p)
         for j in jobs}                                 # start times
    T = {j.id: model.add_variable(f"T_{j.id}", lowBound=0)
         for j in jobs}                                 # tardiness
    kind = pulp.LpContinuous if relax else pulp.LpBinary
    y = {(a.id, b.id): model.add_variable(f"y_{a.id}_{b.id}",
                                          0, 1, kind)
         for a, b in combinations(jobs, 2)}       # 1 if a before b

    # Objective: total weighted tardiness
    model += pulp.lpSum(j.w * T[j.id] for j in jobs)

    # Tardiness: T_j >= C_j - d_j  (and T_j >= 0 from the bound)
    for j in jobs:
        model += T[j.id] >= S[j.id] + j.p - j.d, f"tardy_{j.id}"

    # Disjunctions: either a before b, or b before a
    for a, b in combinations(jobs, 2):
        yab = y[a.id, b.id]
        model += S[a.id] + a.p <= S[b.id] + M * (1 - yab)  # a, b
        model += S[b.id] + b.p <= S[a.id] + M * yab        # b, a
    return model, S
# [end:model]


# [start:solve]
def solve_disjunctive(jobs: list[Job], time_limit: float = 60,
                      threads: int = 1,
                      msg: bool = False) -> SolveResult:
    model, S = build_disjunctive(jobs)
    solver = pulp.HiGHS(msg=msg, timeLimit=time_limit, threads=threads)
    t0 = time.perf_counter()
    stats = model.solve(solver)      # PuLP 4 returns statistics
    seconds = time.perf_counter() - t0
    if not stats.has_solution:
        return SolveResult(None, None, stats.best_bound, False,
                           seconds)
    schedule = []
    for j in jobs:
        s = round(S[j.id].value())
        schedule.append(Task(j.id, "M1", s, s + j.p))
    optimal = stats.status == pulp.LpSolveStatus.Optimal
    return SolveResult(schedule, stats.objective, stats.best_bound,
                       optimal, seconds)
# [end:solve]


if __name__ == "__main__":
    # [start:run]
    res = solve_disjunctive(JOBS)
    validate_single_machine(JOBS, res.schedule)
    order = [t.job for t in sorted(res.schedule, key=lambda t: t.start)]
    print("order:", " ".join(order))
    value = evaluate(JOBS, res.schedule)["sumwT"]
    print("total weighted tardiness:", value)
    print(f"proven optimal: {res.optimal}   time: {res.seconds:.2f} s")
    # [end:run]
