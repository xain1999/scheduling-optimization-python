"""Cross-checks: every exact method against brute force on small random
instances, and every heuristic against the rules of its problem.

These tests do not look at the book's numbers.  They check that the
algorithms are right on inputs nobody chose by hand (random releases,
zero weights, negative due dates, zero-duration project activities).
Run:  python tests/test_crosscheck.py   (from the code/ folder, about 2 min)
"""
import itertools
import random
import sys
from pathlib import Path

CODE = Path(__file__).resolve().parents[1]
for sub in ("", "ch01", "ch02", "ch05", "ch06", "ch07", "ch08", "ch09",
            "ch13", "ch14"):
    sys.path.insert(0, str(CODE / sub))

from schedlib import Job, evaluate, sequence_to_schedule  # noqa: E402


def best(jobs, objective, prec=()):
    """Brute-force optimum over all orders (respecting precedences)."""
    values = []
    for perm in itertools.permutations(j.id for j in jobs):
        pos = {a: i for i, a in enumerate(perm)}
        if all(pos[a] < pos[b] for a, b in prec):
            sched = sequence_to_schedule(jobs, list(perm))
            values.append(evaluate(jobs, sched)[objective])
    return min(values)


def value(jobs, order, objective):
    return evaluate(jobs, sequence_to_schedule(jobs, order))[objective]


def random_jobs(rng, n, releases=True):
    return [Job(f"J{i}", p=rng.randint(1, 5),
                r=rng.randint(0, 6) if releases else 0,
                d=rng.randint(-3, 15), w=rng.randint(0, 3))
            for i in range(n)]


def test_single_machine_models():
    from cpsat_model import solve_cpsat
    from milp_disjunctive import solve_disjunctive
    from milp_time_indexed import solve_time_indexed
    rng = random.Random(1)
    for _ in range(15):
        jobs = random_jobs(rng, 5)
        opt = best(jobs, "sumwT")
        for solve in (solve_cpsat, solve_disjunctive, solve_time_indexed):
            res = solve(jobs, time_limit=20)
            assert res.optimal and round(res.objective) == opt, \
                (solve.__name__, jobs, res.objective, opt)


def test_exact_single_machine_algorithms():
    from dp_wt import dp_weighted_tardiness
    from lawler_prec import lawler
    from moore_hodgson import moore_hodgson
    rng = random.Random(2)
    for _ in range(40):
        jobs = random_jobs(rng, 6, releases=False)
        v, order = dp_weighted_tardiness(jobs)
        assert v == best(jobs, "sumwT") == value(jobs, order, "sumwT")
        assert value(jobs, moore_hodgson(jobs), "nTardy") == \
            best(jobs, "nTardy")
        ids = [j.id for j in jobs]
        prec = [(a, b) for a, b in itertools.combinations(ids, 2)
                if rng.random() < 0.2]
        order = lawler(jobs, prec, lambda j, c: c - j.d)
        pos = {a: i for i, a in enumerate(order)}
        assert all(pos[a] < pos[b] for a, b in prec)
        assert value(jobs, order, "Lmax") == best(jobs, "Lmax", prec)


def test_flow_shop():
    from cpsat_flowshop import cpsat_flowshop, no_wait_tsp
    from fast_neh import neh_fast
    from flowshop import johnson, makespan
    from neh import neh
    rng = random.Random(3)
    for _ in range(30):
        n = rng.randint(2, 6)
        p2 = [[rng.randint(1, 9) for _ in range(n)] for _ in range(2)]
        assert makespan(p2, johnson(p2)) == min(
            makespan(p2, list(o)) for o in itertools.permutations(range(n)))
        p = [[rng.randint(1, 9) for _ in range(n)] for _ in range(3)]
        assert neh(p) == neh_fast(p)
    for _ in range(6):
        n = 5
        p = [[rng.randint(1, 9) for _ in range(n)] for _ in range(3)]
        perm = min(makespan(p, list(o))
                   for o in itertools.permutations(range(n)))
        r = cpsat_flowshop(p, time_limit=20, workers=1)
        assert r["optimal"] and r["cmax"] == perm

        def no_wait(order):                    # earliest no-wait starts
            c = [0] * 3
            for j in order:
                s = max(max(c[i] - sum(p[k][j] for k in range(i)), 0)
                        for i in range(3))
                c = [s + sum(p[k][j] for k in range(i + 1))
                     for i in range(3)]
            return c[-1]
        nw = min(no_wait(o) for o in itertools.permutations(range(n)))
        r = no_wait_tsp(p, time_limit=20)
        assert r["optimal"] and r["cmax"] == nw


def test_parallel_machines():
    from lpt import lower_bound, lpt
    from pcmax_models import cpsat_pcmax, milp_pcmax
    rng = random.Random(4)
    for _ in range(10):
        m = 3
        p = [rng.randint(1, 12) for _ in range(7)]
        opt = min(max(sum(p[j] for j in range(7) if a[j] == i)
                      for i in range(m))
                  for a in itertools.product(range(m), repeat=7))
        assert lower_bound(p, m) <= opt <= lpt(p, m)[0]
        assert lpt(p, m)[0] <= (4 / 3 - 1 / (3 * m)) * opt + 1e-9
        for model in (lambda: milp_pcmax(p, m),
                      lambda: milp_pcmax(p, m, symmetry_breaking=True),
                      lambda: cpsat_pcmax(p, m, workers=1)):
            v, optimal, _ = model()
            assert optimal and v == opt, (p, v, opt)


def feasible(project, capacity, start):
    for a, (d, need, preds) in project.items():
        assert all(start[a] >= start[q] + project[q][0] for q in preds)
    horizon = max(start[a] + project[a][0] for a in project)
    for r, cap in capacity.items():
        for t in range(horizon):
            use = sum(project[a][1].get(r, 0) for a in project
                      if start[a] <= t < start[a] + project[a][0])
            assert use <= cap


def test_project_scheduling():
    from rcpsp import serial_sgs, solve_rcpsp
    from sgs import parallel_sgs
    rng = random.Random(5)
    for _ in range(25):
        names = [f"A{i}" for i in range(7)]
        project = {}
        for i, a in enumerate(names):
            preds = rng.sample(names[:i], min(i, rng.randint(0, 2)))
            need = {r: rng.randint(1, 2) for r in ("R", "S")
                    if rng.random() < 0.6}
            dur = 0 if rng.random() < 0.2 else rng.randint(1, 5)
            project[a] = (dur, need, preds)
        capacity = {"R": 2, "S": 2}
        opt = solve_rcpsp(project, capacity, time_limit=20, workers=1)
        assert opt["optimal"]
        feasible(project, capacity, opt["starts"])
        for sgs in (serial_sgs, parallel_sgs):
            mk, start = sgs(project, capacity, priority=str)
            feasible(project, capacity, start)
            assert mk == max(start[a] + project[a][0] for a in project)
            assert mk >= opt["makespan"]


def test_job_shop_critical_path():
    from giffler_thompson import giffler_thompson, rules
    from jobshop import critical_path
    rng = random.Random(6)
    for _ in range(20):
        jobs = [[(mc, rng.randint(1, 9))
                 for mc in rng.sample(range(4), 4)] for _ in range(4)]
        for rule in rules(jobs).values():
            mk, starts = giffler_thompson(jobs, rule)
            seq = {}
            for op, s in sorted(starts.items(), key=lambda kv: kv[1]):
                seq.setdefault(jobs[op[0]][op[1]][0], []).append(op)
            m2, s2, path = critical_path(jobs, seq)
            assert m2 == mk and s2 == starts
            for a, b in zip(path, path[1:]):    # a tight chain of arcs
                assert s2[a] + jobs[a[0]][a[1]][1] == s2[b]
            assert s2[path[0]] == 0


def test_metaheuristic_moves():
    from genetic import order_crossover
    from local_search import descent, total_wt
    rng = random.Random(7)
    for _ in range(200):
        n = rng.randint(2, 9)
        a, b = rng.sample(range(n), n), rng.sample(range(n), n)
        assert sorted(order_crossover(a, b, rng)) == list(range(n))
    for _ in range(20):
        jobs = [(rng.randint(1, 5), rng.randint(0, 15), rng.randint(1, 3))
                for _ in range(6)]
        order, cost = descent(jobs, list(range(6)))
        assert sorted(order) == list(range(6))
        assert cost == total_wt(jobs, order) <= total_wt(jobs, range(6))


if __name__ == "__main__":
    tests = [v for k, v in dict(globals()).items() if k.startswith("test_")]
    for t in tests:
        t()
        print("passed:", t.__name__)
