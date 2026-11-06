"""Chapter 5: exact dynamic programming over subsets for 1||sum wT."""
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
sys.path.insert(0, str(Path(__file__).resolve().parent))

from wt_instances import wt_instance
from schedlib import Job, evaluate, sequence_to_schedule


# [start:dp]
def dp_weighted_tardiness(jobs: list[Job]):
    """Optimal 1 || sum w_j T_j by dynamic programming over subsets.

    f[S] = best cost of scheduling the set S *first*.  The last job j
    of S finishes at P(S) = total processing time of S, whatever the
    order of the others, so
        f[S] = min_j  f[S - j] + w_j * max(0, P(S) - d_j).
    Time O(2^n * n), memory O(2^n): exact up to about 20 jobs.
    """
    n = len(jobs)
    full = 1 << n
    p = [j.p for j in jobs]
    INF = float("inf")
    f = [INF] * full
    last = [-1] * full
    P = [0] * full
    f[0] = 0
    for S in range(1, full):
        low = S & -S                         # lowest set bit
        P[S] = P[S ^ low] + p[low.bit_length() - 1]
        best, arg = INF, -1
        T = S
        while T:
            bit = T & -T
            j = bit.bit_length() - 1
            c = f[S ^ bit] + jobs[j].w * max(0, P[S] - jobs[j].d)
            if c < best:
                best, arg = c, j
            T ^= bit
        f[S], last[S] = best, arg
    order, S = [], full - 1                # walk back to get the order
    while S:
        j = last[S]
        order.append(jobs[j].id)
        S ^= 1 << j
    return f[full - 1], order[::-1]
# [end:dp]


if __name__ == "__main__":
    # [start:run]
    for n in (10, 12, 14, 16, 18, 20):
        jobs = wt_instance(n, tf=0.6, rdd=0.6, seed=n)
        t0 = time.perf_counter()
        value, order = dp_weighted_tardiness(jobs)
        dt = time.perf_counter() - t0
        schedule = sequence_to_schedule(jobs, order)
        check = evaluate(jobs, schedule)["sumwT"]
        assert check == value
        print(f"n={n:2}  optimum={value:6}  states={2**n:>9,}  "
              f"{dt:6.2f} s")
    # [end:run]
