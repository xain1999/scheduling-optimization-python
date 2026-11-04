"""Chapter 7 -- the NEH heuristic for permutation flow shops."""
from flowshop import makespan


# [start:neh]
def neh(p: list[list[int]]) -> list[int]:
    """Nawaz, Enscore and Ham (1983).

    1. Sort jobs by decreasing total processing time.
    2. Insert them one at a time, each at the position of the partial
       sequence that gives the smallest partial makespan.
    """
    if not p or not p[0]:
        raise ValueError("NEH needs at least one machine and one job")
    n = len(p[0])
    jobs = sorted(range(n), key=lambda j: -sum(row[j] for row in p))
    seq = [jobs[0]]
    for j in jobs[1:]:
        best_pos, best_val = 0, float("inf")
        for pos in range(len(seq) + 1):
            trial = seq[:pos] + [j] + seq[pos:]
            val = makespan(p, trial)
            if val < best_val:
                best_pos, best_val = pos, val
        seq.insert(best_pos, j)
    return seq
# [end:neh]


def lower_bound(p: list[list[int]]) -> int:
    """Simple bound: the busiest machine, plus the unavoidable time
    before its first and after its last job."""
    m, n = len(p), len(p[0])
    lb = 0
    for i in range(m):
        head = min(sum(p[k][j] for k in range(i)) for j in range(n))
        tail = min(sum(p[k][j] for k in range(i + 1, m)) for j in range(n))
        lb = max(lb, head + sum(p[i]) + tail)
    lb = max(lb, max(sum(p[i][j] for i in range(m)) for j in range(n)))
    return lb
