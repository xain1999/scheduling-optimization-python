"""Chapter 4: a limited buffer between two machines: Reservoir."""
import random
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from ortools.sat.python import cp_model

from schedlib.status import check_cpsat


def instance(n=10, seed=7):
    rng = random.Random(seed)
    return [(rng.randint(1, 12), rng.randint(1, 12)) for _ in range(n)]


# [start:model]
def solve_line(jobs, buffer_size):
    """Two machines in series with a buffer of limited size between.

    jobs: list of (time on machine A, time on machine B).
    A finished pallet leaves A when there is room for it in the buffer
    (or B is ready). Until then it stays on A and blocks it.  It leaves
    the buffer when B starts it.
    """
    H = sum(a + b for a, b in jobs)
    m = cp_model.CpModel()
    sa, ea, out, sb, eb = {}, {}, {}, {}, {}
    occupyA, ivB = [], []
    for j, (pa, pb) in enumerate(jobs):
        sa[j], ea[j] = m.new_int_var(0, H, ""), m.new_int_var(0, H, "")
        out[j] = m.new_int_var(0, H, "")     # pallet leaves machine A
        sb[j], eb[j] = m.new_int_var(0, H, ""), m.new_int_var(0, H, "")
        m.add(ea[j] == sa[j] + pa)
        m.add(out[j] >= ea[j])               # may wait on A (blocking)
        occupyA.append(m.new_interval_var(  # A is busy until it leaves
            sa[j], m.new_int_var(pa, H, ""), out[j], f"A{j}"))
        ivB.append(m.new_interval_var(sb[j], pb, eb[j], f"B{j}"))
        m.add(sb[j] >= out[j])               # B after the transfer
    m.add_no_overlap(occupyA)
    m.add_no_overlap(ivB)

    if buffer_size is not None:              # +1 on leaving A, -1 at B
        times = [out[j] for j in range(len(jobs))] + \
                [sb[j] for j in range(len(jobs))]
        changes = [1] * len(jobs) + [-1] * len(jobs)
        m.add_reservoir_constraint(times, changes, 0, buffer_size)

    makespan = m.new_int_var(0, H, "makespan")
    m.add_max_equality(makespan, list(eb.values()))
    m.minimize(makespan)
    solver = cp_model.CpSolver()
    solver.parameters.max_time_in_seconds = 60
    solver.parameters.num_workers = 8
    status = check_cpsat(solver, solver.solve(m))
    return solver.value(makespan), status
# [end:model]


if __name__ == "__main__":
    # [start:run]
    jobs = instance()
    for b in [0, 1, 2, None]:
        makespan, status = solve_line(jobs, b)
        label = "unlimited" if b is None else b
        print(f"buffer {label!s:>9}: makespan {makespan}  ({status})")
    # [end:run]
