"""Chapter 2: extending the CP-SAT model to parallel machines."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
sys.path.insert(0, str(Path(__file__).resolve().parent))

from ortools.sat.python import cp_model

from instances import horizon, random_instance
from schedlib import Job, Task, evaluate
from schedlib.results import save
from schedlib.status import check_cpsat


# [start:model]
def solve_parallel(jobs: list[Job], machines: list[str],
                   time_limit: float = 30, workers: int = 8):
    """P | r_j | sum w_j T_j: identical parallel machines."""
    H = horizon(jobs)
    model = cp_model.CpModel()
    start, end, tardy = {}, {}, {}
    on = {}                                   # on[j, m]: j runs on m
    per_machine = {m: [] for m in machines}

    for j in jobs:
        start[j.id] = model.new_int_var(j.r, H - j.p, f"s_{j.id}")
        end[j.id] = model.new_int_var(j.r + j.p, H, f"e_{j.id}")
        for m in machines:
            on[j.id, m] = model.new_bool_var(f"on_{j.id}_{m}")
            # An *optional* interval exists only if on[j, m] is true
            per_machine[m].append(model.new_optional_interval_var(
                start[j.id], j.p, end[j.id], on[j.id, m],
                f"{j.id}@{m}"))
        model.add_exactly_one(on[j.id, m] for m in machines)
        tardy[j.id] = model.new_int_var(0, max(0, H - j.d),
                                        f"T_{j.id}")
        model.add_max_equality(tardy[j.id], [0, end[j.id] - j.d])

    for m in machines:              # one job at a time per machine
        model.add_no_overlap(per_machine[m])

    model.minimize(sum(j.w * tardy[j.id] for j in jobs))

    solver = cp_model.CpSolver()
    solver.parameters.max_time_in_seconds = time_limit
    solver.parameters.num_workers = workers
    status = check_cpsat(solver, solver.solve(model))
    schedule = [Task(j.id, m, solver.value(start[j.id]),
                     solver.value(end[j.id]))
                for j in jobs for m in machines
                if solver.value(on[j.id, m])]
    return schedule, status
# [end:model]


if __name__ == "__main__":
    # [start:run]
    jobs = random_instance(12, seed=7, spread=0.3, slack=0.2)
    schedule, status = solve_parallel(jobs, ["M1", "M2"])
    print(status, "total weighted tardiness =",
          evaluate(jobs, schedule)["sumwT"])
    for m in ["M1", "M2"]:
        seq = sorted((t for t in schedule if t.resource == m),
                     key=lambda t: t.start)
        print(m, " ".join(f"{t.job}@{t.start}" for t in seq))  # starts
    # [end:run]
    save("ch02_parallel", schedule)          # the figure draws this one
