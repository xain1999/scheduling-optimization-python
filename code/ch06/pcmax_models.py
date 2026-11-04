"""Chapter 6 -- exact models for P || Cmax: MILP and CP-SAT."""
import time

import pulp                                  # import before ortools
from ortools.sat.python import cp_model

from lpt import lower_bound, lpt


# [start:milp]
def milp_pcmax(p, m, symmetry_breaking=False, time_limit=10):
    n = len(p)
    model = pulp.LpProblem("P_Cmax", pulp.LpMinimize)
    x = {(j, i): model.add_variable(f"x_{j}_{i}", 0, 1, pulp.LpBinary)
         for j in range(n) for i in range(m)}
    cmax = model.add_variable("Cmax", lower_bound(p, m))
    model += cmax
    for j in range(n):                       # every job on one machine
        model += pulp.lpSum(x[j, i] for i in range(m)) == 1
    load = [pulp.lpSum(p[j] * x[j, i] for j in range(n))
            for i in range(m)]
    for i in range(m):
        model += load[i] <= cmax
    if symmetry_breaking:                    # machines are identical:
        for i in range(m - 1):               # order them by load
            model += load[i] >= load[i + 1]
    t0 = time.perf_counter()
    st = model.solve(pulp.HiGHS(msg=False, timeLimit=time_limit,
                                threads=1))
    secs = time.perf_counter() - t0
    if not st.has_solution:                   # nothing found in time
        return None, False, secs
    optimal = st.status == pulp.LpSolveStatus.Optimal
    return round(st.objective), optimal, secs
# [end:milp]


# [start:cpsat]
def cpsat_pcmax(p, m, time_limit=10, workers=8, hint=True):
    """No intervals needed: with all jobs available at time 0, only
    the loads matter, and the order on each machine is irrelevant."""
    n = len(p)
    model = cp_model.CpModel()
    x = {(j, i): model.new_bool_var(f"x_{j}_{i}")
         for j in range(n) for i in range(m)}
    cmax = model.new_int_var(lower_bound(p, m), sum(p), "Cmax")
    for j in range(n):
        model.add_exactly_one(x[j, i] for i in range(m))
    loads = []
    for i in range(m):
        load = model.new_int_var(0, sum(p), f"load_{i}")
        model.add(load == sum(p[j] * x[j, i] for j in range(n)))
        model.add(load <= cmax)
        loads.append(load)
    for i in range(m - 1):                    # symmetry breaking
        model.add(loads[i] >= loads[i + 1])
    if hint:                                  # start from LPT
        _, assign = lpt(p, m)
        by_load = sorted(range(m), key=lambda i: -sum(
            p[j] for j in range(n) if assign[j] == i))
        rank = {mach: r for r, mach in enumerate(by_load)}
        for j in range(n):
            for i in range(m):
                model.add_hint(x[j, i], rank[assign[j]] == i)
    model.minimize(cmax)
    solver = cp_model.CpSolver()
    solver.parameters.max_time_in_seconds = time_limit
    solver.parameters.num_workers = workers
    t0 = time.perf_counter()
    status = solver.solve(model)
    secs = time.perf_counter() - t0
    if status not in (cp_model.OPTIMAL, cp_model.FEASIBLE):
        return None, False, secs
    optimal = status == cp_model.OPTIMAL
    return int(solver.objective_value), optimal, secs
# [end:cpsat]
