"""Chapter 14: iterated greedy for the permutation flow shop."""
import math
import random
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "ch07"))
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "ch13"))

from flowshop import makespan
from fast_neh import neh_fast


def best_insertion(p, seq, job):
    best_pos, best_val = 0, float("inf")
    for pos in range(len(seq) + 1):
        val = makespan(p, seq[:pos] + [job] + seq[pos:])
        if val < best_val:
            best_pos, best_val = pos, val
    return seq[:best_pos] + [job] + seq[best_pos:], best_val


def insertion_local_search(p, seq, deadline=math.inf):
    """Remove each job in turn and reinsert it at its best position,
    until no move improves or the clock passes `deadline`."""
    cur, cur_val = list(seq), makespan(p, seq)
    improved = True
    while improved:
        improved = False
        for job in list(cur):
            if time.perf_counter() > deadline:
                return cur, cur_val
            rest = [j for j in cur if j != job]
            cand, val = best_insertion(p, rest, job)
            if val < cur_val:
                cur, cur_val, improved = cand, val, True
    return cur, cur_val


# [start:ig]
def iterated_greedy(p, seconds=30, d=4, temp_factor=0.4, seed=0,
                    history=None):
    """Ruiz and Stuetzle (2007).

    Repeat: destroy (remove d random jobs), reconstruct (reinsert each
    at its best position, NEH-style), improve (insertion local search),
    accept the result if better, or with a small probability if worse.
    """
    t_start = time.perf_counter()            # the budget covers it all
    deadline = t_start + seconds
    rng = random.Random(seed)
    m, n = len(p), len(p[0])
    if not 1 <= d < n:
        raise ValueError(f"need 1 <= d < n (d={d}, n={n} jobs)")
    T = temp_factor * sum(map(sum, p)) / (n * m * 10)
    cur, cur_val = insertion_local_search(p, neh_fast(p), deadline)
    best, best_val = list(cur), cur_val
    while time.perf_counter() < deadline:
        removed = rng.sample(cur, d)                     # destruction
        partial = [j for j in cur if j not in removed]
        for job in removed:                              # construction
            partial, _ = best_insertion(p, partial, job)
        cand, val = insertion_local_search(p, partial,   # local search
                                           deadline)
        worse = val - cur_val
        if worse < 0 or rng.random() < math.exp(-worse / T):
            cur, cur_val = cand, val                     # acceptance
        if cur_val < best_val:
            best, best_val = list(cur), cur_val
            if history is not None:
                elapsed = time.perf_counter() - t_start
                history.append((elapsed, best_val))
    return best, best_val
# [end:ig]
