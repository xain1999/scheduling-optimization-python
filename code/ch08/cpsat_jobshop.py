"""Chapter 8: the classic CP-SAT job-shop model."""
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from ortools.sat.python import cp_model

from schedlib.status import check_cpsat


# [start:model]
def solve_jobshop(jobs, time_limit=60, workers=8, hint=None):
    """jobs[j] = [(machine, duration), ...] in route order."""
    machines = {mach for ops in jobs for mach, _ in ops}
    H = sum(d for ops in jobs for _, d in ops)
    m = cp_model.CpModel()
    start, end, per_machine = {}, {}, {k: [] for k in machines}
    for j, ops in enumerate(jobs):
        for k, (mach, dur) in enumerate(ops):
            start[j, k] = m.new_int_var(0, H, f"s{j}_{k}")
            end[j, k] = m.new_int_var(0, H, f"e{j}_{k}")
            per_machine[mach].append(
                m.new_interval_var(start[j, k], dur, end[j, k], ""))
            if k > 0:                      # follow the job's route
                m.add(start[j, k] >= end[j, k - 1])
    for mach in machines:                  # one operation at a time
        m.add_no_overlap(per_machine[mach])
    makespan = m.new_int_var(0, H, "makespan")
    m.add_max_equality(makespan, [end[j, len(ops) - 1]
                                  for j, ops in enumerate(jobs)])
    m.minimize(makespan)
    if hint:
        for op, s in hint.items():
            m.add_hint(start[op], s)

    solver = cp_model.CpSolver()
    solver.parameters.max_time_in_seconds = time_limit
    solver.parameters.num_workers = workers
    t0 = time.perf_counter()
    status = check_cpsat(solver, solver.solve(m))
    starts = {op: solver.value(v) for op, v in start.items()}
    return dict(makespan=int(solver.objective_value),
                bound=int(solver.best_objective_bound),
                optimal=status == "OPTIMAL",
                seconds=time.perf_counter() - t0, starts=starts)
# [end:model]


def sequences_from_starts(jobs, starts):
    seq = {}
    for (j, k), s in sorted(starts.items(), key=lambda kv: kv[1]):
        seq.setdefault(jobs[j][k][0], []).append((j, k))
    return seq
