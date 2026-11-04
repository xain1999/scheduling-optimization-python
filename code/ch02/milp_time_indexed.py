"""Chapter 2 -- MILP model 2: time-indexed formulation."""
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
sys.path.insert(0, str(Path(__file__).resolve().parent))

import pulp

from instances import JOBS, horizon
from schedlib import (Job, SolveResult, Task, evaluate,
                      validate_single_machine)


# [start:model]
def build_time_indexed(jobs: list[Job], relax: bool = False):
    H = horizon(jobs)
    model = pulp.LpProblem("wT_time_indexed", pulp.LpMinimize)
    kind = pulp.LpContinuous if relax else pulp.LpBinary

    # x[j, t] = 1 if job j starts at time t (only feasible start times)
    x = {(j.id, t): model.add_variable(f"x_{j.id}_{t}", 0, 1, kind)
         for j in jobs for t in range(j.r, H - j.p + 1)}

    # Objective: the tardiness of each (job, start) pair is a constant!
    cost = {(j.id, t): j.w * max(0, t + j.p - j.d)
            for j in jobs for t in range(j.r, H - j.p + 1)}
    model += pulp.lpSum(cost[k] * x[k] for k in x)

    # Every job starts exactly once
    for j in jobs:
        starts = range(j.r, H - j.p + 1)
        model += pulp.lpSum(x[j.id, t] for t in starts) == 1

    # Capacity: in each unit period [u, u+1) at most one job runs.
    # Job j occupies period u if it started in (u - p_j, u].
    for u in range(H):
        model += pulp.lpSum(
            x[j.id, t] for j in jobs
            for t in range(max(j.r, u - j.p + 1), u + 1)
            if (j.id, t) in x) <= 1, f"cap_{u}"
    return model, x
# [end:model]


# [start:solve]
def solve_time_indexed(jobs: list[Job], time_limit: float = 60,
                       threads: int = 1,
                       msg: bool = False) -> SolveResult:
    model, x = build_time_indexed(jobs)
    solver = pulp.HiGHS(msg=msg, timeLimit=time_limit, threads=threads)
    t0 = time.perf_counter()
    stats = model.solve(solver)
    seconds = time.perf_counter() - t0
    if not stats.has_solution:
        return SolveResult(None, None, stats.best_bound, False, seconds)
    by_id = {j.id: j for j in jobs}
    schedule = [Task(jid, "M1", t, t + by_id[jid].p)
                for (jid, t), var in x.items() if var.value() > 0.5]
    optimal = stats.status == pulp.LpSolveStatus.Optimal
    return SolveResult(schedule, stats.objective, stats.best_bound,
                       optimal, seconds)
# [end:solve]


if __name__ == "__main__":
    # [start:run]
    res = solve_time_indexed(JOBS)
    validate_single_machine(JOBS, res.schedule)
    order = [t.job for t in sorted(res.schedule, key=lambda t: t.start)]
    print("order:", " ".join(order))
    value = evaluate(JOBS, res.schedule)["sumwT"]
    print("total weighted tardiness:", value)
    print(f"proven optimal: {res.optimal}   time: {res.seconds:.2f} s")
    # [end:run]
