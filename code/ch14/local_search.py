"""Chapter 14: local search, simulated annealing and tabu search for
single-machine total weighted tardiness."""
import math
import random
import time


# [start:cost]
def total_wt(jobs, order):
    """jobs[i] = (p, d, w), and order = list of job indices."""
    t = cost = 0
    for i in order:
        p, d, w = jobs[i]
        t += p
        if t > d:
            cost += w * (t - d)
    return cost
# [end:cost]


# [start:descent]
def descent(jobs, order, neighbourhood="insert"):
    """First-improvement local search until no neighbour is better."""
    order, best = list(order), total_wt(jobs, order)
    n, improved = len(order), True
    while improved:
        improved = False
        for a in range(n):
            for b in range(n):
                if a == b:
                    continue
                cand = list(order)
                if neighbourhood == "swap":
                    cand[a], cand[b] = cand[b], cand[a]
                else:                                # move a to b
                    cand.insert(b, cand.pop(a))
                c = total_wt(jobs, cand)
                if c < best:
                    order, best, improved = cand, c, True
                    break
            if improved:
                break
    return order, best
# [end:descent]


# [start:annealing]
def simulated_annealing(jobs, order, seconds=5, t0=None, alpha=0.9995,
                        seed=0):
    """Accept a worse neighbour with probability exp(-delta / T).  The
    temperature T decreases geometrically.  Random insertion moves."""
    rng = random.Random(seed)
    cur, cur_cost = list(order), total_wt(jobs, order)
    best, best_cost = list(cur), cur_cost
    T = t0 if t0 is not None else 0.05 * max(cur_cost, 1)
    end, n = time.perf_counter() + seconds, len(order)
    while time.perf_counter() < end:
        a, b = rng.randrange(n), rng.randrange(n)
        cand = list(cur)
        cand.insert(b, cand.pop(a))
        delta = total_wt(jobs, cand) - cur_cost
        temp = max(T, 1e-9)
        if delta <= 0 or rng.random() < math.exp(-delta / temp):
            cur, cur_cost = cand, cur_cost + delta
            if cur_cost < best_cost:
                best, best_cost = list(cur), cur_cost
        T *= alpha
        if T < 1e-3:                       # reheat when frozen
            T = 0.02 * max(best_cost, 1)
    return best, best_cost
# [end:annealing]


# [start:tabu]
def tabu_search(jobs, order, seconds=5, tenure=7, sample=None, seed=0):
    """Move to the best non-tabu swap neighbour, even if it is worse.
    Swapped jobs may not be swapped again for `tenure` iterations,
    unless the move gives a new best solution (aspiration)."""
    rng = random.Random(seed)
    cur = list(order)
    best, best_cost = list(cur), total_wt(jobs, cur)
    tabu, it, n = {}, 0, len(order)
    pairs = [(a, b) for a in range(n) for b in range(a + 1, n)]
    if sample is not None and not 1 <= sample <= len(pairs):
        raise ValueError(f"sample must be in 1..{len(pairs)}")
    end = time.perf_counter() + seconds
    while time.perf_counter() < end:
        it += 1
        moves = pairs if sample is None else rng.sample(pairs, sample)
        choice = None
        for a, b in moves:
            cand = list(cur)
            cand[a], cand[b] = cand[b], cand[a]
            c = total_wt(jobs, cand)
            key = frozenset((cur[a], cur[b]))
            allowed = tabu.get(key, 0) < it or c < best_cost
            if allowed and (choice is None or c < choice[0]):
                choice = (c, cand, key)
        if choice is None:
            continue
        c, cur, key = choice
        tabu[key] = it + tenure
        if c < best_cost:
            best, best_cost = list(cur), c
    return best, best_cost
# [end:tabu]
