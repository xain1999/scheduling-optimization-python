"""Chapter 8: case study: a flexible machining workshop with operators.

Each operation can run on one of several machines (with different
durations) and needs one operator for its whole duration.
"""
import random
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from ortools.sat.python import cp_model

from schedlib import Task
from schedlib.status import check_cpsat


# [start:data]
def workshop(n_jobs=10, n_machines=6, ops_per_job=5, seed=11):
    """Flexible job shop: each operation lists (machine, duration)
    alternatives, between one and three of them."""
    rng = random.Random(seed)
    jobs = []
    for _ in range(n_jobs):
        ops = []
        for _ in range(ops_per_job):
            base = rng.randint(3, 12)
            machines = rng.sample(range(n_machines), rng.randint(1, 3))
            ops.append([(mc, base + rng.randint(0, 4))
                        for mc in machines])
        jobs.append(ops)
    return jobs
# [end:data]


# [start:model]
def solve_workshop(jobs, operators=None, time_limit=30):
    machines = {mc for ops in jobs for alts in ops for mc, _ in alts}
    H = sum(max(d for _, d in alts) for ops in jobs for alts in ops)
    m = cp_model.CpModel()
    start, end, all_ops = {}, {}, []
    per_machine = {k: [] for k in machines}
    choice = {}
    for j, ops in enumerate(jobs):
        for k, alts in enumerate(ops):
            lo = min(d for _, d in alts)
            hi = max(d for _, d in alts)
            start[j, k] = m.new_int_var(0, H, f"s{j}_{k}")
            end[j, k] = m.new_int_var(0, H, f"e{j}_{k}")
            dur = m.new_int_var(lo, hi, f"d{j}_{k}")
            # the operation as a whole (variable duration) ...
            all_ops.append(m.new_interval_var(start[j, k], dur,
                                              end[j, k], ""))
            lits = []
            for mc, d in alts:         # ... and one option per machine
                lit = m.new_bool_var(f"x{j}_{k}_{mc}")
                per_machine[mc].append(m.new_optional_interval_var(
                    start[j, k], d, end[j, k], lit, ""))
                m.add(dur == d).only_enforce_if(lit)
                lits.append(lit)
                choice[j, k, mc] = lit
            m.add_exactly_one(lits)
            if k > 0:
                m.add(start[j, k] >= end[j, k - 1])
    for mc in machines:
        m.add_no_overlap(per_machine[mc])
    if operators is not None:           # each operation needs a person
        m.add_cumulative(all_ops, [1] * len(all_ops), operators)
    makespan = m.new_int_var(0, H, "makespan")
    m.add_max_equality(makespan, [end[j, len(ops) - 1]
                                  for j, ops in enumerate(jobs)])
    m.minimize(makespan)
    solver = cp_model.CpSolver()
    solver.parameters.max_time_in_seconds = time_limit
    solver.parameters.num_workers = 8
    status = check_cpsat(solver, solver.solve(m))
    plan = [Task(f"{j+1}.{k+1}", f"M{mc+1}", solver.value(start[j, k]),
                 solver.value(end[j, k]))
            for (j, k, mc), lit in choice.items() if solver.value(lit)]
    return int(solver.objective_value), status, plan
# [end:model]


if __name__ == "__main__":
    # [start:run]
    jobs = workshop()
    for ops in (2, 3, 4, 5, None):
        mk, status, _ = solve_workshop(jobs, operators=ops)
        label = "unlimited" if ops is None else ops
        print(f"operators {label!s:>9}: makespan {mk:3}  ({status})")
    # [end:run]
