"""Chapter 5: just-in-time: penalise earliness as well as tardiness."""
import random
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from ortools.sat.python import cp_model

from schedlib import Job, Task
from schedlib.status import check_cpsat


def jit_instance(n=10, seed=3):
    rng = random.Random(seed)
    jobs = []
    for i in range(n):
        p = rng.randint(2, 9)
        jobs.append(Job(f"J{i+1}", p=p, d=rng.randint(p, 60),
                        w=rng.randint(1, 3)))
    return jobs


# [start:model]
def solve_et(jobs, alpha=1, idle_allowed=True, time_limit=20):
    """min sum alpha*w_j*E_j + w_j*T_j.  alpha weights earliness
    (holding cost), and w_j weights tardiness (lateness penalty)."""
    H = max(j.d for j in jobs) + sum(j.p for j in jobs)
    m = cp_model.CpModel()
    start, end, ivs, cost = {}, {}, [], []
    for j in jobs:
        start[j.id] = m.new_int_var(0, H, f"s_{j.id}")
        end[j.id] = m.new_int_var(0, H, f"e_{j.id}")
        ivs.append(m.new_interval_var(start[j.id], j.p, end[j.id],
                                      j.id))
        early = m.new_int_var(0, H, f"E_{j.id}")
        late = m.new_int_var(0, max(0, H - j.d), f"T_{j.id}")
        m.add_max_equality(early, [0, j.d - end[j.id]])
        m.add_max_equality(late, [0, end[j.id] - j.d])
        cost += [alpha * j.w * early, j.w * late]
    m.add_no_overlap(ivs)
    if not idle_allowed:     # all jobs inside [0, sum p]: no idle time
        total = sum(j.p for j in jobs)
        for j in jobs:
            m.add(end[j.id] <= total)
    m.minimize(sum(cost))
    solver = cp_model.CpSolver()
    solver.parameters.max_time_in_seconds = time_limit
    solver.parameters.num_workers = 8
    status = check_cpsat(solver, solver.solve(m))
    sched = [Task(j.id, "M1", solver.value(start[j.id]),
                  solver.value(end[j.id])) for j in jobs]
    return sched, solver.objective_value, status
# [end:model]


if __name__ == "__main__":
    # [start:run]
    jobs = jit_instance()
    for idle in (False, True):
        sched, value, status = solve_et(jobs, idle_allowed=idle)
        busy = sum(j.p for j in jobs)
        span = max(t.end for t in sched)
        print(f"idle allowed={idle!s:5}: cost {value:4.0f} "
              f"({status}), idle time {span - busy} of {span}")
    # [end:run]
