"""Chapter 4 -- case study: a paint line with colour changeovers.

Single machine, sequence-dependent changeover times, modelled with
AddCircuit.  Objectives: total weighted tardiness, then changeovers.
"""
import random
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from ortools.sat.python import cp_model

from schedlib.status import check_cpsat


# [start:data]
COLOURS = ["white", "yellow", "orange", "red", "blue", "black"]


def changeover(a: int, b: int) -> int:
    """Time to switch from colour a to colour b (indices, light->dark).

    Going darker needs a quick flush; going lighter needs a full clean.
    """
    if a == b:
        return 0
    return 1 if b > a else 3 + 2 * (a - b)


def paint_jobs(n=12, seed=1):
    rng = random.Random(seed)
    jobs = []
    total = 0
    for i in range(n):
        p = rng.randint(2, 8)
        total += p
        jobs.append(dict(name=f"J{i+1}", colour=rng.randrange(6), p=p,
                         w=rng.randint(1, 3)))
    for j in jobs:                      # due dates spread over the day
        j["due"] = rng.randint(j["p"], int(total * 0.8))
    return jobs
# [end:data]


def evaluate(jobs, order, start_colour=0):
    """Weighted tardiness and changeover time of a given order."""
    t, colour, wt, setup = 0, start_colour, 0, 0
    by = {j["name"]: j for j in jobs}
    for name in order:
        j = by[name]
        s = changeover(colour, j["colour"])
        t += s + j["p"]
        setup += s
        wt += j["w"] * max(0, t - j["due"])
        colour = j["colour"]
    return wt, setup


# [start:model]
def build(jobs, start_colour=0):
    n = len(jobs)
    H = sum(j["p"] for j in jobs) + n * changeover(5, 0)
    m = cp_model.CpModel()
    start = [m.new_int_var(0, H, f"s{i}") for i in range(n)]
    end = [m.new_int_var(0, H, f"e{i}") for i in range(n)]
    ivs = [m.new_interval_var(start[i], jobs[i]["p"], end[i], f"iv{i}")
           for i in range(n)]
    m.add_no_overlap(ivs)                 # redundant, but helps search

    # Node 0 is a dummy "start/end of day"; job i is node i + 1.
    arcs, setup_terms = [], []
    for i in range(n):
        first = m.new_bool_var(f"first{i}")
        last = m.new_bool_var(f"last{i}")
        arcs += [(0, i + 1, first), (i + 1, 0, last)]
        s0 = changeover(start_colour, jobs[i]["colour"])
        m.add(start[i] >= s0).only_enforce_if(first)
        setup_terms.append(s0 * first)
        for k in range(n):
            if i == k:
                continue
            lit = m.new_bool_var(f"{i}->{k}")
            arcs.append((i + 1, k + 1, lit))
            s = changeover(jobs[i]["colour"], jobs[k]["colour"])
            # if k directly follows i, it waits for the changeover
            m.add(start[k] >= end[i] + s).only_enforce_if(lit)
            setup_terms.append(s * lit)
    m.add_circuit(arcs)                   # one Hamiltonian tour

    tardy = []
    for i, j in enumerate(jobs):
        t = m.new_int_var(0, max(0, H - j["due"]), f"T{i}")
        m.add_max_equality(t, [0, end[i] - j["due"]])
        tardy.append(j["w"] * t)
    return m, start, sum(tardy), sum(setup_terms)
# [end:model]


# [start:lexico]
def solve_lexicographic(jobs, time_limit=30, workers=8):
    m, start, tardiness, setups = build(jobs)
    solver = cp_model.CpSolver()
    solver.parameters.max_time_in_seconds = time_limit
    solver.parameters.num_workers = workers

    m.minimize(tardiness)                       # 1st priority
    status1 = check_cpsat(solver, solver.solve(m))
    best_tardiness = int(solver.objective_value)
    bound1 = solver.best_objective_bound

    for v in start:                             # keep the solution
        m.add_hint(v, solver.value(v))          # as a starting point
    m.add(tardiness <= best_tardiness)          # don't get worse...
    m.minimize(setups)                          # ...then 2nd priority
    status = check_cpsat(solver, solver.solve(m))

    order = sorted(range(len(jobs)),
                   key=lambda i: solver.value(start[i]))
    info = dict(phase1=status1, bound1=bound1, phase2=status)
    return [jobs[i]["name"] for i in order], info
# [end:lexico]


# [start:callback]
class ProgressLogger(cp_model.CpSolverSolutionCallback):
    """Record every improving solution: (seconds, objective, bound)."""

    def __init__(self):
        super().__init__()
        self.history = []

    def on_solution_callback(self):
        self.history.append((self.wall_time, self.objective_value,
                             self.best_objective_bound))
# [end:callback]


def heuristic_order(jobs):
    """Group by colour from light to dark, EDD inside each group."""
    return [j["name"] for j in sorted(jobs,
                                      key=lambda j: (j["colour"], j["due"]))]


if __name__ == "__main__":
    # [start:run]
    jobs = paint_jobs()
    edd = [j["name"] for j in sorted(jobs, key=lambda j: j["due"])]
    print("EDD order        : tardiness %4d, changeovers %3d"
          % evaluate(jobs, edd))
    print("colour groups    : tardiness %4d, changeovers %3d"
          % evaluate(jobs, heuristic_order(jobs)))
    t0 = time.perf_counter()
    order, info = solve_lexicographic(jobs)
    print("CP-SAT lexicogr. : tardiness %4d, changeovers %3d"
          % evaluate(jobs, order))
    print(f"  tardiness: {info['phase1']}, lower bound "
          f"{info['bound1']:.0f}; changeovers: {info['phase2']}; "
          f"{time.perf_counter() - t0:.0f} s")
    seq = [f"{n}:{COLOURS[jobs[int(n[1:]) - 1]['colour']][:3]}"
           for n in order]
    print("  " + " ".join(seq[:8]))
    print("  " + " ".join(seq[8:]))
    # [end:run]
