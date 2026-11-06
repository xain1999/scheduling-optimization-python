"""Chapter 14: a genetic algorithm for the permutation flow shop."""
import random
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "ch07"))

from flowshop import makespan


# [start:ox]
def order_crossover(a, b, rng):
    """OX: copy a slice of parent a, fill the rest in b's order."""
    n = len(a)
    i, j = sorted(rng.sample(range(n + 1), 2))   # 0 <= i < j <= n
    middle = a[i:j]
    taken = set(middle)
    rest = [g for g in b if g not in taken]
    return rest[:i] + middle + rest[i:]
# [end:ox]


# [start:ga]
def genetic_algorithm(p, seconds=30, pop_size=40, mutation=0.3, seed=0,
                      seeds=()):
    end = time.perf_counter() + seconds       # includes initialisation
    rng = random.Random(seed)
    n = len(p[0])
    pop = [list(s) for s in seeds]
    while len(pop) < pop_size:
        pop.append(rng.sample(range(n), n))
    fit = [makespan(p, s) for s in pop]
    while time.perf_counter() < end:
        def pick():                                  # tournament of 2
            x, y = rng.sample(range(pop_size), 2)
            return pop[x] if fit[x] < fit[y] else pop[y]
        child = order_crossover(pick(), pick(), rng)
        if rng.random() < mutation:                # insertion mutation
            child.insert(rng.randrange(n), child.pop(rng.randrange(n)))
        value = makespan(p, child)
        worst = max(range(pop_size), key=fit.__getitem__)
        if value < fit[worst] and child not in pop:  # steady state
            pop[worst], fit[worst] = child, value
    k = min(range(pop_size), key=fit.__getitem__)
    return pop[k], fit[k]
# [end:ga]
