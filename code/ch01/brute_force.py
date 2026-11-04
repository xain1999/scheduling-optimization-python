"""Chapter 1 -- exhaustive search, and why it does not scale."""
import itertools
import math
import random
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
sys.path.insert(0, str(Path(__file__).resolve().parent))

from print_shop import JOBS
from schedlib import Job, evaluate, sequence_to_schedule


# [start:brute]
def brute_force(jobs: list[Job], objective: str):
    """Try every permutation and keep the best one."""
    best_value, best_order = math.inf, None
    for perm in itertools.permutations(j.id for j in jobs):
        schedule = sequence_to_schedule(jobs, list(perm))
        value = evaluate(jobs, schedule)[objective]
        if value < best_value:
            best_value, best_order = value, perm
    return best_value, list(best_order)
# [end:brute]


def human(seconds: float) -> str:
    """Format a duration in the most readable unit."""
    for unit, size in [("years", 3.15e7), ("days", 86400),
                       ("hours", 3600), ("minutes", 60)]:
        if seconds >= size:
            return f"{seconds / size:,.0f} {unit}"
    return f"{seconds:.1f} seconds"


def random_jobs(n: int, seed: int = 0) -> list[Job]:
    rng = random.Random(seed)
    jobs = []
    for i in range(n):
        p = rng.randint(1, 10)
        jobs.append(Job(f"J{i+1}", p=p, d=rng.randint(p, 5 * n),
                        w=rng.randint(1, 3)))
    return jobs


if __name__ == "__main__":
    print("Optimal values for the print shop (8 jobs, 40,320 orders):")
    for obj in ["sumC", "sumwC", "Lmax", "sumwT"]:
        value, order = brute_force(JOBS, obj)
        print(f"  {obj:6} = {value:4}   e.g. {' '.join(order)}")

    # [start:timing]
    print("\n n        n!   seconds")
    rate = None
    for n in range(4, 10):
        jobs = random_jobs(n)
        t0 = time.perf_counter()
        brute_force(jobs, "sumwT")
        dt = time.perf_counter() - t0
        rate = math.factorial(n) / dt          # schedules per second
        print(f"{n:2} {math.factorial(n):>9,} {dt:9.3f}")
    for n in (12, 15, 20, 25):
        secs = math.factorial(n) / rate
        print(f"{n:2} {math.factorial(n):>9.1e}  ~{human(secs)}")
    # [end:timing]
