"""Chapter 7: CP-SAT models for the flow shop."""
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from ortools.sat.python import cp_model

from schedlib.status import check_cpsat


# [start:model]
def cpsat_flowshop(p, permutation=True, no_wait=False, time_limit=60,
                   hint=None, workers=8):
    m, n = len(p), len(p[0])
    H = sum(map(sum, p))
    model = cp_model.CpModel()
    s = {(i, j): model.new_int_var(0, H, f"s{i}_{j}")
         for i in range(m) for j in range(n)}
    iv = {(i, j): model.new_fixed_size_interval_var(s[i, j], p[i][j],
                                                     "")
          for i in range(m) for j in range(n)}
    for i in range(m):
        model.add_no_overlap([iv[i, j] for j in range(n)])
    for j in range(n):                    # route: machine 1, 2, ..., m
        for i in range(1, m):
            if no_wait:                     # straight on, no waiting
                model.add(s[i, j] == s[i - 1, j] + p[i - 1][j])
            else:
                model.add(s[i, j] >= s[i - 1, j] + p[i - 1][j])
    if permutation:                       # same order on every machine
        for a in range(n):
            for b in range(a + 1, n):
                before = model.new_bool_var(f"{a}<{b}")
                for i in range(m):
                    model.add(s[i, b] >= s[i, a] + p[i][a]) \
                        .only_enforce_if(before)
                    model.add(s[i, a] >= s[i, b] + p[i][b]) \
                        .only_enforce_if(before.Not())
    cmax = model.new_int_var(0, H, "cmax")
    model.add_max_equality(cmax, [s[m - 1, j] + p[m - 1][j]
                                  for j in range(n)])
    model.minimize(cmax)
    if hint is not None:                    # a sequence, e.g. from NEH
        t = [0] * m
        for j in hint:
            for i in range(m):
                start = max(t[i], t[i - 1] if i else 0)
                model.add_hint(s[i, j], start)
                t[i] = start + p[i][j]
    solver = cp_model.CpSolver()
    solver.parameters.max_time_in_seconds = time_limit
    solver.parameters.num_workers = workers
    t0 = time.perf_counter()
    status = solver.solve(model)
    seconds = time.perf_counter() - t0
    bound = int(solver.best_objective_bound)
    if status not in (cp_model.OPTIMAL, cp_model.FEASIBLE):
        return dict(cmax=None, bound=bound, optimal=False,
                    seconds=seconds, order=None)
    order = sorted(range(n), key=lambda j: solver.value(s[0, j]))
    return dict(cmax=int(solver.objective_value), bound=bound,
                optimal=status == cp_model.OPTIMAL,
                seconds=seconds, order=order)
# [end:model]


# [start:nowait]
def no_wait_tsp(p, time_limit=60):
    """No-wait permutation flow shop as an asymmetric TSP.

    If job b directly follows job a, b must start on machine 1 at least
    delay(a, b) after a so that it never waits between machines.  The
    makespan is the sum of the delays along the sequence plus the total
    processing time of the last job: a tour cost through a dummy node.
    """
    m, n = len(p), len(p[0])

    def delay(a, b):
        return max(sum(p[k][a] for k in range(i + 1)) -
                   sum(p[k][b] for k in range(i)) for i in range(m))
    model = cp_model.CpModel()
    arcs, cost = [], []
    for a in range(-1, n):                  # -1 is the dummy node
        for b in range(-1, n):
            if a == b:
                continue
            lit = model.new_bool_var("")
            arcs.append((a + 1, b + 1, lit))
            if a == -1:
                c = 0                       # first job starts at 0
            elif b == -1:
                c = sum(p[k][a] for k in range(m))  # last job finishes
            else:
                c = delay(a, b)
            cost.append(c * lit)
    model.add_circuit(arcs)
    model.minimize(sum(cost))
    solver = cp_model.CpSolver()
    solver.parameters.max_time_in_seconds = time_limit
    solver.parameters.num_workers = 8
    status = check_cpsat(solver, solver.solve(model))
    return dict(cmax=int(solver.objective_value),
                bound=int(solver.best_objective_bound),
                optimal=status == "OPTIMAL")
# [end:nowait]
