"""Chapter 16: schedules that survive uncertain durations."""
import math
import random
import statistics
import sys
from itertools import combinations
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from ortools.sat.python import cp_model

from schedlib import Job
from schedlib.results import save
from schedlib.status import check_cpsat


def instance(n=10, seed=8):
    rng = random.Random(seed)
    jobs = []
    for i in range(n):
        p = rng.randint(3, 12)
        jobs.append(Job(f"J{i+1}", p=p, d=rng.randint(p, 55),
                        w=rng.randint(1, 4)))
    return jobs


def uncertainty(jobs, seed=8):
    """Coefficient of variation per job: most jobs are routine (0.1),
    each job is risky (0.6) with probability 1/3: new customers, new materials."""
    rng = random.Random(seed)
    return {j.id: 0.6 if rng.random() < 1 / 3 else 0.1 for j in jobs}


# [start:simulate]
def sample_durations(jobs, rng, cv):
    """Actual durations: lognormal around the plan with coefficient of
    variation cv[job], rounded to whole time units (at least 1)."""
    out = {}
    for j in jobs:
        sigma = (math.log(1 + cv[j.id] ** 2)) ** 0.5
        mu = math.log(j.p) - sigma ** 2 / 2
        out[j.id] = max(1, round(rng.lognormvariate(mu, sigma)))
    return out


def simulate(jobs, order, scenarios):
    """Execute a fixed sequence in each scenario (jobs start as soon
    as the previous one ends).  Return each weighted tardiness."""
    by_id = {j.id: j for j in jobs}
    results = []
    for durations in scenarios:
        t = cost = 0
        for jid in order:
            t += durations[jid]
            cost += by_id[jid].w * max(0, t - by_id[jid].d)
        results.append(cost)
    return results
# [end:simulate]


# [start:saa]
def optimise_order(jobs, scenarios, time_limit=30):
    """One sequence, evaluated in every scenario: minimise the average
    weighted tardiness (sample average approximation).  With a single
    scenario equal to the plan, this is the deterministic problem."""
    m = cp_model.CpModel()
    ids = [j.id for j in jobs]
    before = {(a, b): m.new_bool_var(f"{a}<{b}")
              for a, b in combinations(ids, 2)}
    total = []
    for k, dur in enumerate(scenarios):
        H = sum(dur.values())
        s = {j: m.new_int_var(0, H, f"s{k}_{j}") for j in ids}
        for (a, b), lit in before.items():   # same order everywhere
            m.add(s[b] >= s[a] + dur[a]).only_enforce_if(lit)
            m.add(s[a] >= s[b] + dur[b]).only_enforce_if(lit.Not())
        for j in jobs:
            t = m.new_int_var(0, max(0, H - j.d), "")
            m.add_max_equality(t, [0, s[j.id] + dur[j.id] - j.d])
            total.append(j.w * t)
    m.minimize(sum(total))
    solver = cp_model.CpSolver()
    solver.parameters.max_time_in_seconds = time_limit
    solver.parameters.num_workers = 8
    check_cpsat(solver, solver.solve(m))
    first = {pair: solver.value(lit) for pair, lit in before.items()}
    wins = {j: sum(f if a == j else 1 - f              # jobs after j
                   for (a, b), f in first.items() if j in (a, b))
            for j in ids}
    return sorted(ids, key=lambda j: -wins[j])
# [end:saa]


if __name__ == "__main__":
    # [start:run]
    jobs = instance()
    cv = uncertainty(jobs)
    rng = random.Random(1)
    plan = [{j.id: j.p for j in jobs}]                   # no surprises
    train = [sample_durations(jobs, rng, cv) for _ in range(30)]
    test = [sample_durations(jobs, rng, cv) for _ in range(2000)]
    det = optimise_order(jobs, plan)
    rob = optimise_order(jobs, train, time_limit=60)
    for name, order in [("deterministic", det),
                        ("robust (30 sc.)", rob)]:
        planned = simulate(jobs, order, plan)[0]
        r = sorted(simulate(jobs, order, test))
        p90 = r[math.ceil(0.9 * len(r)) - 1]   # 90th pct, nearest rank
        print(f"{name:16} planned {planned:4}  simulated: mean "
              f"{statistics.mean(r):5.1f}  90th pct {p90}")
    # [end:run]
    save("ch16_robust", {"deterministic": det, "robust": rob})
