"""Chapter 5: rules, CP-SAT, MILP and DP on 1 || sum w_j T_j."""
import csv
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "ch02"))
sys.path.insert(0, str(Path(__file__).resolve().parent))

from milp_time_indexed import solve_time_indexed   # import before ortools
from cpsat_model import solve_cpsat
from atc import atc_order, best_atc
from dp_wt import dp_weighted_tardiness
from wt_instances import instance_seed, wt_instance
from schedlib import evaluate, sequence_to_schedule

ROOT = Path(__file__).resolve().parents[2]


def cost(jobs, order):
    return evaluate(jobs, sequence_to_schedule(jobs, order))["sumwT"]


def by_start(sched):
    return [t.job for t in sorted(sched, key=lambda t: t.start)]


def value_of(jobs, res):
    """Weighted tardiness of a solver result, or None if it found none."""
    if res.schedule is None:
        return None
    return cost(jobs, by_start(res.schedule))


# [start:small]
def small_benchmark(n=16):
    """Every method against the exact optimum from the DP."""
    rows = []
    for tf in (0.2, 0.4, 0.6, 0.8):
        for rdd in (0.2, 0.6, 1.0):
            for seed in (1, 2):
                seed_ = instance_seed(tf, rdd, seed)
                jobs = wt_instance(n, tf, rdd, seed_)
                t0 = time.perf_counter()
                opt, _ = dp_weighted_tardiness(jobs)
                res = {"DP": (opt, time.perf_counter() - t0)}
                for name, key in [("EDD", lambda j: j.d),
                                  ("WSPT", lambda j: j.p / j.w)]:
                    order = [j.id for j in sorted(jobs, key=key)]
                    res[name] = (cost(jobs, order), 0.0)
                t0 = time.perf_counter()
                res["ATC k=2"] = (cost(jobs, atc_order(jobs, 2)),
                                  time.perf_counter() - t0)
                t0 = time.perf_counter()
                res["ATC best k"] = (cost(jobs, best_atc(jobs)),
                                     time.perf_counter() - t0)
                r = solve_cpsat(jobs, time_limit=10, workers=8)
                res["CP-SAT 10s"] = (value_of(jobs, r), r.seconds)
                r = solve_time_indexed(jobs, time_limit=30, threads=1)
                res["MILP time-ix"] = (value_of(jobs, r), r.seconds)
                for method, (value, secs) in res.items():
                    rows.append(dict(tf=tf, rdd=rdd, seed=seed,
                                     method=method, value=value,
                                     opt=opt, seconds=secs))
                print(tf, rdd, seed, {k: v[0] for k, v in res.items()},
                      flush=True)
    return rows
# [end:small]


def large_benchmark(n=40):
    rows = []
    for tf in (0.4, 0.6, 0.8):
        for rdd in (0.2, 0.6, 1.0):
            jobs = wt_instance(n, tf, rdd, instance_seed(tf, rdd, 7))
            atc = cost(jobs, best_atc(jobs))
            r = solve_cpsat(jobs, time_limit=20, workers=8)
            cp = value_of(jobs, r)
            rows.append(dict(tf=tf, rdd=rdd, atc=atc, cpsat=cp,
                             bound=r.bound))
            print(tf, rdd, atc, cp, r.bound, flush=True)
    return rows


if __name__ == "__main__":
    (ROOT / "results").mkdir(exist_ok=True)
    small = small_benchmark()
    with open(ROOT / "results" / "ch05_small.csv", "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=small[0].keys())
        w.writeheader()
        w.writerows(small)
    large = large_benchmark()
    with open(ROOT / "results" / "ch05_large.csv", "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=large[0].keys())
        w.writeheader()
        w.writerows(large)
