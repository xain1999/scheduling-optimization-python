"""Chapter 4: a shared crew: the Cumulative constraint."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from ortools.sat.python import cp_model

from schedlib.results import save
from schedlib.status import check_cpsat


# [start:data]
# Finishing tasks after printing: (duration in hours, people needed)
TASKS = {
    "T1": (3, 2), "T2": (2, 1), "T3": (4, 2), "T4": (2, 3),
    "T5": (3, 1), "T6": (1, 2), "T7": (2, 2), "T8": (4, 1),
    "T9": (3, 2), "T10": (2, 1),
}
CREW = 3                                 # people on the finishing team
PRECEDENCES = [("T1", "T4"), ("T3", "T7")]  # T4 needs T1's output, ...
# [end:data]


# [start:model]
def solve_crew(tasks=TASKS, crew=CREW, prec=PRECEDENCES):
    horizon = sum(d for d, _ in tasks.values())
    m = cp_model.CpModel()
    start, end, iv = {}, {}, {}
    for t, (dur, _) in tasks.items():
        start[t] = m.new_int_var(0, horizon, f"s_{t}")
        end[t] = m.new_int_var(0, horizon, f"e_{t}")
        iv[t] = m.new_interval_var(start[t], dur, end[t], f"iv_{t}")

    # At every moment, the people in use must not exceed the crew size
    m.add_cumulative([iv[t] for t in tasks],
                     [need for _, need in tasks.values()], crew)
    for a, b in prec:
        m.add(start[b] >= end[a])

    makespan = m.new_int_var(0, horizon, "makespan")
    m.add_max_equality(makespan, [end[t] for t in tasks])
    m.minimize(makespan)

    solver = cp_model.CpSolver()
    solver.parameters.max_time_in_seconds = 10
    check_cpsat(solver, solver.solve(m))  # e.g. INFEASIBLE if n > CREW
    return {t: (solver.value(start[t]), solver.value(end[t]))
            for t in tasks}, solver.value(makespan)
# [end:model]


if __name__ == "__main__":
    # [start:run]
    plan, makespan = solve_crew()
    total = sum(d * n for d, n in TASKS.values())
    print(f"makespan {makespan} h, lower bound from workload: "
          f"{total}/{CREW} = {total / CREW:.1f} h")
    for t, (s, e) in sorted(plan.items(), key=lambda kv: kv[1]):
        print(f"  {t:4} {s:2}-{e:2}  people={TASKS[t][1]}")
    # [end:run]
    save("ch04_crew", {"plan": plan, "makespan": makespan})
