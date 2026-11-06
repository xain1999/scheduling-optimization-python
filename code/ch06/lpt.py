"""Chapter 6: list scheduling and LPT for P || Cmax."""
import heapq


# [start:list]
def list_schedule(p: list[int], m: int, order=None):
    """Give each job, in the given order, to the machine free first.

    Returns (makespan, assignment) where assignment[j] is the machine.
    """
    order = range(len(p)) if order is None else order
    free = [(0, i) for i in range(m)]           # (time free, machine)
    heapq.heapify(free)
    assign = [None] * len(p)
    for j in order:
        t, i = heapq.heappop(free)
        assign[j] = i
        heapq.heappush(free, (t + p[j], i))
    return max(t for t, _ in free), assign


def lpt(p: list[int], m: int):
    """Longest Processing Time: list scheduling, longest job first."""
    order = sorted(range(len(p)), key=lambda j: -p[j])
    return list_schedule(p, m, order)


def lower_bound(p: list[int], m: int) -> int:
    """No schedule beats the average load or the longest job."""
    return max(-(-sum(p) // m), max(p))
# [end:list]


if __name__ == "__main__":
    # [start:worst]
    from itertools import product
    p, m = [3, 3, 2, 2, 2], 2            # the classic bad case for LPT
    best = min(max(sum(p[j] for j in range(len(p)) if a[j] == i)
                   for i in range(m))
               for a in product(range(m), repeat=len(p)))  # try all
    print("LPT               :", lpt(p, m)[0])
    print("optimal           :", best, "  (3+3 on one machine, 2+2+2)")
    print("Graham's bound 4/3 - 1/(3m) =",
          round(4 / 3 - 1 / (3 * m), 3),
          " ratio here =", round(lpt(p, m)[0] / best, 3))
    # [end:worst]
