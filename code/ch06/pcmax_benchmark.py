"""Chapter 6: LPT versus exact models on random P || Cmax instances."""
import random

from lpt import lower_bound, lpt
from pcmax_models import cpsat_pcmax, milp_pcmax

# [start:bench]
print(f"{'n':>4} {'m':>3} {'LB':>5} {'LPT':>5} {'MILP':>11} "
      f"{'MILP+sym':>11} {'CP-SAT':>11}")
SIZES = [(20, 3), (20, 5), (50, 5), (50, 10), (100, 10), (100, 20)]
for n, m in SIZES:
    rng = random.Random(n * 100 + m)
    p = [rng.randint(10, 100) for _ in range(n)]
    lb, (ub, _) = lower_bound(p, m), lpt(p, m)
    cells = []
    for solve in (lambda: milp_pcmax(p, m),
                  lambda: milp_pcmax(p, m, symmetry_breaking=True),
                  lambda: cpsat_pcmax(p, m)):
        value, optimal, secs = solve()
        shown = "--" if value is None else value    # no solution found
        cells.append(f"{shown}{'*' if optimal else ' '} {secs:4.1f}s")
    print(f"{n:4} {m:3} {lb:5} {ub:5} " + " ".join(f"{c:>11}"
                                                  for c in cells))
# [end:bench]
