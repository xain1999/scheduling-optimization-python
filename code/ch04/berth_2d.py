"""Chapter 4: berth allocation: intervals in time *and* space."""
import random
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from ortools.sat.python import cp_model

from schedlib.results import save
from schedlib.status import check_cpsat


QUAY = 30                       # quay length in 10-metre units


def ships(n=10, seed=4):
    rng = random.Random(seed)
    out = []
    for i in range(n):
        out.append(dict(name=f"S{i+1}", arrival=rng.randint(0, 20),
                        length=rng.randint(6, 14),
                        hours=rng.randint(6, 16), weight=rng.randint(1, 3)))
    return out


# [start:model]
def solve_berths(fleet, quay=QUAY, time_limit=20):
    H = (max(s["arrival"] for s in fleet)
         + sum(s["hours"] for s in fleet))
    m = cp_model.CpModel()
    t_iv, x_iv, start, pos = [], [], {}, {}
    for s in fleet:
        n = s["name"]
        start[n] = m.new_int_var(s["arrival"], H, f"t_{n}")
        pos[n] = m.new_int_var(0, quay - s["length"], f"x_{n}")
        # a rectangle: time interval x quay interval
        t_iv.append(m.new_fixed_size_interval_var(start[n], s["hours"],
                                                  f"time_{n}"))
        x_iv.append(m.new_fixed_size_interval_var(pos[n], s["length"],
                                                  f"quay_{n}"))
    m.add_no_overlap_2d(t_iv, x_iv)        # rectangles may not overlap
    m.minimize(sum(s["weight"] * (start[s["name"]] - s["arrival"])
                   for s in fleet))        # weighted waiting time
    solver = cp_model.CpSolver()
    solver.parameters.max_time_in_seconds = time_limit
    status = check_cpsat(solver, solver.solve(m))
    plan = {s["name"]: (solver.value(start[s["name"]]),
                        solver.value(pos[s["name"]])) for s in fleet}
    return plan, solver.objective_value, status
# [end:model]


if __name__ == "__main__":
    # [start:run]
    fleet = ships()
    plan, waiting, status = solve_berths(fleet)
    print(f"{status}: weighted waiting = {waiting:.0f} hours")
    for s in fleet:
        t, x = plan[s["name"]]
        print(f"  {s['name']:3} arrives {s['arrival']:2}  berths at "
              f"t={t:2}  quay {x:2}-{x + s['length']:2}")
    # [end:run]
    save("ch04_berths", plan)
