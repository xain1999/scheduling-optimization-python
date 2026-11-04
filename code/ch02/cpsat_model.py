"""Chapter 2 -- the same problem as a constraint programming model (CP-SAT)."""
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
sys.path.insert(0, str(Path(__file__).resolve().parent))

from ortools.sat.python import cp_model

from instances import JOBS, horizon
from schedlib import (Job, SolveResult, Task, evaluate,
                      validate_single_machine)
from schedlib.results import save


# [start:model]
def build_cpsat(jobs: list[Job]):
    H = horizon(jobs)
    model = cp_model.CpModel()
    start, end, tardy, intervals = {}, {}, {}, []

    for j in jobs:
        start[j.id] = model.new_int_var(j.r, H - j.p, f"start_{j.id}")
        end[j.id] = model.new_int_var(j.r + j.p, H, f"end_{j.id}")
        # An interval variable ties start, duration and end together
        intervals.append(model.new_interval_var(
            start[j.id], j.p, end[j.id], f"job_{j.id}"))
        # tardy = max(0, end - due), stated exactly; it can reach
        # H - d (more than H if the job is already overdue, d < 0)
        tardy[j.id] = model.new_int_var(0, max(0, H - j.d),
                                        f"tardy_{j.id}")
        model.add_max_equality(tardy[j.id], [0, end[j.id] - j.d])

    # One global constraint replaces all n(n-1) big-M inequalities
    model.add_no_overlap(intervals)

    model.minimize(sum(j.w * tardy[j.id] for j in jobs))
    return model, start
# [end:model]


# [start:solve]
def solve_cpsat(jobs: list[Job], time_limit: float = 60,
                workers: int = 8, msg: bool = False) -> SolveResult:
    model, start = build_cpsat(jobs)
    solver = cp_model.CpSolver()
    solver.parameters.max_time_in_seconds = time_limit
    solver.parameters.num_workers = workers
    solver.parameters.log_search_progress = msg
    t0 = time.perf_counter()
    status = solver.solve(model)
    seconds = time.perf_counter() - t0
    if status not in (cp_model.OPTIMAL, cp_model.FEASIBLE):
        return SolveResult(None, None, solver.best_objective_bound,
                           False, seconds)
    schedule = []
    for j in jobs:
        s = solver.value(start[j.id])
        schedule.append(Task(j.id, "M1", s, s + j.p))
    return SolveResult(schedule, solver.objective_value,
                       solver.best_objective_bound,
                       status == cp_model.OPTIMAL, seconds)
# [end:solve]


if __name__ == "__main__":
    # [start:run]
    res = solve_cpsat(JOBS)
    validate_single_machine(JOBS, res.schedule)
    order = [t.job for t in sorted(res.schedule,
                                   key=lambda t: t.start)]
    print("order:", " ".join(order))
    value = evaluate(JOBS, res.schedule)["sumwT"]
    print("total weighted tardiness:", value)
    print(f"proven optimal: {res.optimal}   time: {res.seconds:.2f} s")
    # [end:run]
    save("ch02_single", order)               # the figure draws this one
