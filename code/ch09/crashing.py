"""Chapter 9: multiple modes and the time-cost trade-off."""
from ortools.sat.python import cp_model

from renovation import CREWS, PROJECT

# [start:modes]
# Crash modes: (duration, crew, extra cost). Normal mode costs nothing
# extra.  E.g. framing in 4 days with overtime, or 3 with a subcontractor.
CRASH = {
    "demolition": [(3, {"carp": 3}, 1200)],
    "elec_rough": [(4, {"elec": 2}, 1500)],     # overtime
    "framing":    [(4, {"carp": 3}, 1000), (3, {"carp": 3}, 2600)],
    "drywall":    [(4, {"carp": 3}, 1400)],
    "kitchen":    [(5, {"carp": 3, "plumb": 1}, 2200)],
    "painting":   [(3, {"carp": 3}, 1300)],
    "flooring":   [(3, {"carp": 2}, 900)],      # faster material
}
OVERHEAD = 900                                   # site cost per day
# [end:modes]


# [start:model]
def cheapest_plan(deadline, time_limit=20):
    H = sum(p[0] for p in PROJECT.values())
    m = cp_model.CpModel()
    start, end, extra = {}, {}, []
    use = {r: ([], []) for r in CREWS}           # intervals, demands
    for a, (dur, need, _) in PROJECT.items():
        modes = [(dur, need, 0)] + CRASH.get(a, [])
        start[a] = m.new_int_var(0, H, f"s_{a}")
        end[a] = m.new_int_var(0, H, f"e_{a}")
        lits = []
        for k, (d, crew, cost) in enumerate(modes):
            lit = m.new_bool_var(f"{a}_mode{k}")
            iv = m.new_optional_interval_var(start[a], d, end[a], lit,
                                             "")
            for r, q in crew.items():
                use[r][0].append(iv)
                use[r][1].append(q)
            extra.append(cost * lit)
            lits.append(lit)
        m.add_exactly_one(lits)
    for a, (_, _, preds) in PROJECT.items():
        for p in preds:
            m.add(start[a] >= end[p])
    for r, (ivs, dem) in use.items():
        m.add_cumulative(ivs, dem, CREWS[r])
    for a in PROJECT:
        m.add(end[a] <= deadline)
    m.minimize(sum(extra))
    solver = cp_model.CpSolver()
    solver.parameters.max_time_in_seconds = time_limit
    solver.parameters.num_workers = 8
    status = solver.status_name(solver.solve(m))
    if status in ("OPTIMAL", "FEASIBLE"):
        return status, int(solver.objective_value)
    return status, None     # INFEASIBLE: proven, UNKNOWN: out of time
# [end:model]


if __name__ == "__main__":
    # [start:run]
    print("deadline  crash cost  overhead  total")
    for deadline in range(44, 30, -1):
        status, cost = cheapest_plan(deadline)
        if status == "INFEASIBLE":                # proven impossible
            print(f"{deadline:8}  infeasible")
            break
        if cost is None:                          # UNKNOWN: no verdict
            print(f"{deadline:8}  unresolved within the time limit")
            continue
        mark = "" if status == "OPTIMAL" else "  (best found)"
        total = cost + OVERHEAD * deadline
        print(f"{deadline:8}  {cost:10}  {OVERHEAD * deadline:8}  "
              f"{total:5}{mark}")
    # [end:run]
