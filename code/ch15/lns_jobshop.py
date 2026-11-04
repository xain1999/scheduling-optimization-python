"""Chapter 15 -- large neighbourhood search around CP-SAT (job shop)."""
import random
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "ch08"))

from ortools.sat.python import cp_model

from giffler_thompson import giffler_thompson, rules


def random_jobshop(n=50, m=15, seed=1):
    rng = random.Random(seed)
    return [[(mc, rng.randint(1, 99)) for mc in rng.sample(range(m), m)]
            for _ in range(n)]


def makespan_of(jobs, starts):
    return max(starts[j, len(ops) - 1] + ops[-1][1]
               for j, ops in enumerate(jobs))


# [start:repair]
def reoptimise(jobs, starts, free_jobs, seconds, workers=8):
    """Keep the machine order of all operations of the *other* jobs;
    let the operations of `free_jobs` move anywhere.  Minimise makespan
    starting from the current schedule as a hint."""
    H = sum(d for ops in jobs for _, d in ops)
    m = cp_model.CpModel()
    s, e, per_machine = {}, {}, {}
    for j, ops in enumerate(jobs):
        for k, (mc, d) in enumerate(ops):
            s[j, k] = m.new_int_var(0, H, "")
            e[j, k] = m.new_int_var(0, H, "")
            per_machine.setdefault(mc, []).append(
                ((j, k), m.new_interval_var(s[j, k], d, e[j, k], "")))
            if k:
                m.add(s[j, k] >= e[j, k - 1])
            m.add_hint(s[j, k], starts[j, k])
    for mc, items in per_machine.items():
        m.add_no_overlap([iv for _, iv in items])
        fixed = sorted((op for op, _ in items
                        if op[0] not in free_jobs),
                       key=lambda op: starts[op])
        for a, b in zip(fixed, fixed[1:]):  # keep their relative order
            m.add(s[b] >= e[a])
    cmax = m.new_int_var(0, H, "cmax")
    m.add_max_equality(cmax, [e[j, len(ops) - 1]
                              for j, ops in enumerate(jobs)])
    m.minimize(cmax)
    solver = cp_model.CpSolver()
    solver.parameters.max_time_in_seconds = seconds
    solver.parameters.num_workers = workers
    status = solver.solve(m)
    if status not in (cp_model.OPTIMAL, cp_model.FEASIBLE):
        return starts
    return {op: solver.value(v) for op, v in s.items()}
# [end:repair]


# [start:lns]
def lns(jobs, seconds=60, fraction=0.2, step=3, seed=0, history=None):
    rng = random.Random(seed)
    _, starts = giffler_thompson(jobs, rules(jobs)["MWKR"])
    best = makespan_of(jobs, starts)
    t0 = time.perf_counter()
    if history is not None:
        history.append((0.0, best))
    while (left := seconds - (time.perf_counter() - t0)) > 0.1:
        k = min(len(jobs), max(2, int(fraction * len(jobs))))
        free = set(rng.sample(range(len(jobs)), k))      # destroy
        new = reoptimise(jobs, starts, free, min(step, left))  # repair
        value = makespan_of(jobs, new)
        if value <= best:                                # accept
            starts, best = new, value
        if history is not None:
            history.append((time.perf_counter() - t0, best))
    return best, starts
# [end:lns]
