"""Chapter 15 -- rolling horizon for a long stream of jobs."""
import math
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "ch02"))

from ortools.sat.python import cp_model

from instances import random_instance
from schedlib import Task, evaluate, validate_single_machine
from schedlib.status import check_cpsat


# [start:window]
def solve_window(jobs, machine_free, time_limit):
    """Schedule `jobs` on a machine that is busy until machine_free."""
    H = (max(machine_free, max(j.r for j in jobs))
         + sum(j.p for j in jobs))
    m = cp_model.CpModel()
    start, ivs, cost = {}, [], []
    for j in jobs:
        start[j.id] = m.new_int_var(max(j.r, machine_free), H, "")
        ivs.append(m.new_fixed_size_interval_var(start[j.id], j.p, ""))
        t = m.new_int_var(0, max(0, H - j.d), "")
        m.add_max_equality(t, [0, start[j.id] + j.p - j.d])
        cost.append(j.w * t)
    m.add_no_overlap(ivs)
    m.minimize(sum(cost))
    for task in online_dispatch(jobs, machine_free):    # warm start
        m.add_hint(start[task.job], task.start)
    solver = cp_model.CpSolver()
    solver.parameters.max_time_in_seconds = time_limit
    solver.parameters.num_workers = 8
    check_cpsat(solver, solver.solve(m))
    return {j.id: solver.value(start[j.id]) for j in jobs}
# [end:window]


# [start:online]
def online_dispatch(jobs, t=0):
    """No look-ahead: whenever the machine is free, start the released
    job with the highest ATC-style index (WSPT discounted by slack)."""
    pending = sorted(jobs, key=lambda j: j.r)
    schedule = []
    while pending:
        ready = [j for j in pending if j.r <= t]
        if not ready:                        # idle until next release
            t = pending[0].r
            continue
        pbar = sum(j.p for j in ready) / len(ready)
        nxt = max(ready, key=lambda j: j.w / j.p * math.exp(
            -max(0, j.d - j.p - t) / (2 * pbar)))
        schedule.append(Task(nxt.id, "M1", t, t + nxt.p))
        t += nxt.p
        pending.remove(nxt)
    return schedule
# [end:online]


# [start:rolling]
def rolling_horizon(jobs, lookahead=60, commit=40, max_jobs=60,
                    time_limit=2):
    """At the time the machine becomes free, plan every pending job
    released within `lookahead` time units (at most `max_jobs` of them,
    the most urgent by due date), commit the jobs that start within the
    next `commit` time units, and roll forward."""
    pending = list(jobs)
    schedule, free = [], 0
    while pending:
        t = max(free, min(j.r for j in pending))
        batch = sorted((j for j in pending if j.r <= t + lookahead),
                       key=lambda j: j.d)[:max_jobs]
        starts = solve_window(batch, free, time_limit)
        ordered = sorted(batch, key=lambda j: starts[j.id])
        keep = [j for j in ordered if starts[j.id] < t + commit]
        keep = keep or ordered[:1]           # always make progress
        for j in keep:
            schedule.append(Task(j.id, "M1", starts[j.id],
                                 starts[j.id] + j.p))
            free = max(free, starts[j.id] + j.p)
        kept = {j.id for j in keep}
        pending = [j for j in pending if j.id not in kept]
    return schedule
# [end:rolling]


if __name__ == "__main__":
    # [start:run]
    # 200 jobs arriving over the whole horizon, with tight due dates
    jobs = random_instance(200, seed=5, spread=1.0, slack=0.05)
    by_id = {j.id: j for j in jobs}
    online = online_dispatch(jobs)
    print(f"online dispatching : {evaluate(jobs, online)['sumwT']:7}")
    t0 = time.perf_counter()
    rh = rolling_horizon(jobs)
    t_rh = time.perf_counter() - t0
    validate_single_machine(jobs, rh)
    print(f"rolling horizon    : {evaluate(jobs, rh)['sumwT']:7}  "
          f"({t_rh:.0f} s)")
    full = solve_window(jobs, 0, time_limit=round(t_rh))
    sched = [Task(j, "M1", s, s + by_id[j].p) for j, s in full.items()]
    print(f"one CP-SAT, all    : {evaluate(jobs, sched)['sumwT']:7}"
          f"  ({t_rh:.0f} s)")
    # [end:run]
