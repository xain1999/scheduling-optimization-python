"""Chapter 5 -- weighted-tardiness instances in the classic style."""
import random
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from schedlib import Job


# [start:generator]
def wt_instance(n: int, tf: float, rdd: float, seed: int) -> list[Job]:
    """Instance generator in the style of Potts and Van Wassenhove.

    p_j ~ U[1, 100], w_j ~ U[1, 10] and due dates
    d_j ~ U[P(1 - TF - RDD/2), P(1 - TF + RDD/2)] with P = sum of p_j.
    TF (tardiness factor) controls how many jobs are late; RDD (range
    of due dates) controls how spread out the due dates are.
    """
    rng = random.Random(seed)
    p = [rng.randint(1, 100) for _ in range(n)]
    w = [rng.randint(1, 10) for _ in range(n)]
    P = sum(p)
    lo = max(0, int(P * (1 - tf - rdd / 2)))
    hi = int(P * (1 - tf + rdd / 2))
    return [Job(f"J{i+1}", p=p[i], d=rng.randint(lo, hi), w=w[i])
            for i in range(n)]
# [end:generator]


def instance_seed(tf: float, rdd: float, rep: int) -> int:
    """A different random seed for every (TF, RDD, replicate), so that
    instances of a benchmark never share processing times or weights."""
    return 10_000 * rep + 100 * round(10 * tf) + round(10 * rdd)
