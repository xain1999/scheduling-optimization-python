"""Chapter 9: the RCPSP: CP-SAT model, serial SGS, random projects."""
import random
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from ortools.sat.python import cp_model

from schedlib.status import check_cpsat


# [start:model]
def solve_rcpsp(project, capacity, time_limit=30, workers=8,
                hint=None):
    """project[a] = (duration, {resource: demand}, [predecessors])."""
    check_project(project, capacity)     # e.g. a misspelled resource
    if not project:                      # same policy as the SGS
        return dict(makespan=0, bound=0, optimal=True, seconds=0.0,
                    starts={})
    H = sum(d for d, _, _ in project.values())
    m = cp_model.CpModel()
    start, end, iv = {}, {}, {}
    for a, (dur, _, _) in project.items():
        start[a] = m.new_int_var(0, H, f"s_{a}")
        end[a] = m.new_int_var(0, H, f"e_{a}")
        iv[a] = m.new_interval_var(start[a], dur, end[a], a)
    for a, (_, _, preds) in project.items():
        for p in preds:
            m.add(start[a] >= end[p])
    for r, cap in capacity.items():          # one cumulative per crew
        users = [a for a in project if project[a][1].get(r, 0) > 0]
        m.add_cumulative([iv[a] for a in users],
                         [project[a][1][r] for a in users], cap)
    makespan = m.new_int_var(0, H, "makespan")
    m.add_max_equality(makespan, list(end.values()))
    m.minimize(makespan)
    if hint:
        for a, s in hint.items():
            m.add_hint(start[a], s)
    solver = cp_model.CpSolver()
    solver.parameters.max_time_in_seconds = time_limit
    solver.parameters.num_workers = workers
    t0 = time.perf_counter()
    status = check_cpsat(solver, solver.solve(m))
    return dict(makespan=int(solver.objective_value),
                bound=int(solver.best_objective_bound),
                optimal=status == "OPTIMAL",
                seconds=time.perf_counter() - t0,
                starts={a: solver.value(start[a]) for a in project})
# [end:model]


# [start:check]
def check_project(project, capacity):
    """Reject inputs on which the schedule generators would fail."""
    for a, (dur, need, preds) in project.items():
        if dur < 0:
            raise ValueError(f"{a}: negative duration")
        for p in preds:
            if p not in project:
                raise ValueError(f"{a}: unknown predecessor {p}")
        for r, q in need.items():
            if r not in capacity:
                raise ValueError(f"{a}: unknown resource {r}")
            if not 0 <= q <= capacity[r]:
                raise ValueError(f"{a} needs {q} {r}, capacity "
                                 f"{capacity[r]}: it can never start")
    indeg = {a: len(set(project[a][2])) for a in project}
    ready = [a for a in project if indeg[a] == 0]
    seen = 0
    while ready:                     # Kahn's algorithm: any cycle?
        a = ready.pop()
        seen += 1
        for b in project:
            if a in project[b][2]:
                indeg[b] -= 1
                if indeg[b] == 0:
                    ready.append(b)
    if seen < len(project):
        raise ValueError("the precedences contain a cycle")
# [end:check]


# [start:sgs]
def serial_sgs(project, capacity, priority):
    """Serial schedule generation scheme.

    Repeatedly take the eligible activity (all predecessors scheduled)
    with the smallest priority value and start it at the earliest time
    when its predecessors are done and every resource has room for its
    whole duration.
    """
    check_project(project, capacity)
    H = sum(d for d, _, _ in project.values())
    usage = {r: [0] * (H + 1) for r in capacity}
    start, done = {}, set()
    while len(done) < len(project):
        eligible = [a for a in project if a not in done and
                    all(p in done for p in project[a][2])]
        a = min(eligible, key=priority)
        dur, need, preds = project[a]
        t = max((start[p] + project[p][0] for p in preds), default=0)
        while any(usage[r][u] + q > capacity[r]
                  for r, q in need.items() for u in range(t, t + dur)):
            t += 1
        for r, q in need.items():
            for u in range(t, t + dur):
                usage[r][u] += q
        start[a] = t
        done.add(a)
    makespan = max((start[a] + project[a][0] for a in project),
                   default=0)                  # empty project: 0
    return makespan, start
# [end:sgs]


# [start:random]
def random_project(n=30, resources=4, seed=0, strength=0.3):
    """A random project in the spirit of the PSPLIB generator.

    Durations 1-10.  Each activity uses each resource with probability
    0.5 (demand 1-10).  Capacities follow the PSPLIB "resource
    strength" RS: R = rmin + RS * (rmax - rmin), where rmin is the
    largest single
    demand and rmax the peak usage of the earliest-start schedule.
    RS = 0 is very tight, RS = 1 makes resources irrelevant.
    """
    rng = random.Random(seed)
    names = [f"A{i+1}" for i in range(n)]
    project = {}
    for i, a in enumerate(names):
        k = 0 if i < 3 else rng.choice([1, 1, 2, 3])
        preds = rng.sample(names[:i], min(k, i))
        need = {f"R{r+1}": rng.randint(1, 10) for r in range(resources)
                if rng.random() < 0.5}
        project[a] = (rng.randint(1, 10), need, preds)
    es = {}
    for a in names:                    # names are topologically sorted
        es[a] = max((es[p] + project[p][0] for p in project[a][2]),
                    default=0)
    horizon = max(es[a] + project[a][0] for a in names)
    capacity = {}
    for r in range(resources):
        res = f"R{r+1}"
        rmin = max(project[a][1].get(res, 0) for a in names)
        rmax = max(sum(project[a][1].get(res, 0) for a in names
                       if es[a] <= t < es[a] + project[a][0])
                   for t in range(horizon))
        capacity[res] = max(1, round(rmin + strength * (rmax - rmin)))
    return project, capacity
# [end:random]
