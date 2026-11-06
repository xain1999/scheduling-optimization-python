"""Chapter 5: Lawler's algorithm for 1 | prec | Lmax (and any f_max)."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from schedlib import Job, evaluate, sequence_to_schedule


# [start:lawler]
def lawler(jobs: list[Job], prec: list[tuple[str, str]], cost):
    """Build the sequence from the back.

    Among the jobs whose successors are all already placed, put last
    the one whose cost would be smallest if it finished at time P
    (the end of everything still unscheduled).  Optimal for any
    non-decreasing cost functions f_j(C_j) and objective max_j f_j.
    """
    succ = {j.id: set() for j in jobs}
    for a, b in prec:
        succ[a].add(b)
    remaining = {j.id: j for j in jobs}
    P = sum(j.p for j in jobs)
    tail = []
    while remaining:
        free = [j for j in remaining.values()
                if not (succ[j.id] & remaining.keys())]
        best = min(free, key=lambda j: cost(j, P))
        tail.append(best.id)
        del remaining[best.id]
        P -= best.p
    return tail[::-1]
# [end:lawler]


if __name__ == "__main__":
    # [start:run]
    jobs = [Job("A", p=3, d=6), Job("B", p=2, d=4), Job("C", p=4, d=9),
            Job("D", p=1, d=3), Job("E", p=3, d=14)]
    prec = [("A", "B"), ("A", "D"), ("C", "E")]   # B, D need A first
    lateness = lambda j, C: C - j.d
    order = lawler(jobs, prec, lateness)
    print("Lawler:", order, "Lmax =",
          evaluate(jobs, sequence_to_schedule(jobs, order))["Lmax"])
    edd = [j.id for j in sorted(jobs, key=lambda j: j.d)]
    print("EDD   :", edd, "(violates A before B and D)")
    # [end:run]
