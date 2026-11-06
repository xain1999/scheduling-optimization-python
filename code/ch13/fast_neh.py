"""Chapter 13: making NEH fast: Taillard's acceleration with NumPy."""
import sys
import time
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "ch07"))

from flowshop import makespan, taillard_instance
from neh import neh


# [start:fast]
def neh_fast(p):
    """NEH where all insertion positions of a job are evaluated at
    once.  e[i, k]: earliest completion of the k-th job of the partial
    sequence on machine i (heads).  q[i, k]: tail from k to the end.
    Inserting job j at position k gives makespan
    max_i (f[i,k] + q[i,k])
    where f is the completion of j itself placed after position k-1.
    Cost per job: O(n m) instead of O(n^2 m).
    """
    P = np.asarray(p, dtype=np.int64)         # shape (m, n)
    m, n = P.shape
    jobs = sorted(range(n), key=lambda j: -P[:, j].sum())
    seq = [jobs[0]]
    for j in jobs[1:]:
        k = len(seq)
        S = P[:, seq]                          # (m, k)
        e = np.zeros((m + 1, k + 1), dtype=np.int64)
        for pos in range(1, k + 1):            # heads
            for i in range(1, m + 1):
                e[i, pos] = (max(e[i - 1, pos], e[i, pos - 1])
                             + S[i - 1, pos - 1])
        q = np.zeros((m + 2, k + 2), dtype=np.int64)
        for pos in range(k, 0, -1):            # tails
            for i in range(m, 0, -1):
                q[i, pos] = (max(q[i + 1, pos], q[i, pos + 1])
                             + S[i - 1, pos - 1])
        f = np.zeros((m + 1, k + 1), dtype=np.int64)
        for i in range(1, m + 1):             # job j at every position
            f[i, :] = np.maximum(f[i - 1, :], e[i, :]) + P[i - 1, j]
        cand = (f[1:, :] + q[1:m + 1, 1:k + 2]).max(axis=0)
        seq.insert(int(np.argmin(cand)), j)
    return seq
# [end:fast]


if __name__ == "__main__":
    # [start:run]
    for n, m in [(20, 5), (50, 10), (100, 20), (200, 20)]:
        p = taillard_instance(12345 + n, n, m)
        t0 = time.perf_counter()
        s1 = neh(p)
        t1 = time.perf_counter()
        s2 = neh_fast(p)
        t2 = time.perf_counter()
        print(f"{n:3}x{m:<2}  naive {t1 - t0:6.2f} s  "
              f"fast {t2 - t1:5.2f} s  "
              f"makespans {makespan(p, s1)} / {makespan(p, s2)}")
    # [end:run]
