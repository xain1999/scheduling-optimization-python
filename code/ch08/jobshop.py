"""Chapter 8: job shop data, reading benchmarks, and critical paths."""
import json
from pathlib import Path

DATA = Path(__file__).resolve().parents[1] / "data" / "jobshop"


# [start:read]
def read_instance(name: str):
    """Read a benchmark in the standard format: a line 'n m', then one
    line per job with pairs (machine, duration) in route order."""
    text = (DATA / f"{name}.txt").read_text()
    lines = [ln for ln in text.splitlines()
             if ln.strip() and not ln.startswith("#")]
    n, m = map(int, lines[0].split())
    jobs = []
    for line in lines[1:n + 1]:
        v = list(map(int, line.split()))
        jobs.append([(v[k], v[k + 1]) for k in range(0, 2 * m, 2)])
    return jobs


def known_optimum(name: str):
    return json.loads((DATA / "optima.json").read_text()).get(name)
# [end:read]


# [start:critical]
def critical_path(jobs, sequences):
    """Earliest start times and a critical path of the disjunctive
    graph.  sequences[machine] = list of (job, operation index) in
    processing order.  Each operation waits for its job predecessor and
    its machine predecessor.  The makespan is the longest path through
    this graph.  Raises ValueError if a machine order is incomplete or
    the orders create a cycle (no schedule can follow them).
    """
    ops = [(j, k) for j, o in enumerate(jobs) for k in range(len(o))]
    for mach in {m for o in jobs for m, _ in o}:
        need = sorted(op for op in ops
                      if jobs[op[0]][op[1]][0] == mach)
        if sorted(sequences.get(mach, [])) != need:
            raise ValueError(f"machine {mach}: the sequence must list "
                             "each of its operations exactly once")
    succ, indeg = {op: [] for op in ops}, dict.fromkeys(ops, 0)
    for j, o in enumerate(jobs):                     # job arcs
        for k in range(1, len(o)):
            succ[j, k - 1].append((j, k))
            indeg[j, k] += 1
    for seq in sequences.values():                   # machine arcs
        for a, b in zip(seq, seq[1:]):
            succ[a].append(b)
            indeg[b] += 1
    start, came_from = dict.fromkeys(ops, 0), dict.fromkeys(ops)
    ready, done = [op for op in ops if indeg[op] == 0], 0
    while ready:                     # longest paths, topological order
        a = ready.pop()
        done += 1
        end_a = start[a] + jobs[a[0]][a[1]][1]
        for b in succ[a]:
            if end_a > start[b] or (end_a == start[b] > 0
                                    and a[0] == b[0]):
                start[b], came_from[b] = end_a, a
            indeg[b] -= 1
            if indeg[b] == 0:
                ready.append(b)
    if done < len(ops):
        raise ValueError("the machine orders create a cycle")
    ends = {op: start[op] + jobs[op[0]][op[1]][1] for op in ops}
    op = max(ends, key=ends.get)
    path = []
    while op is not None:              # walk back along tight arcs
        path.append(op)
        op = came_from[op]
    return ends[path[0]], start, path[::-1]
# [end:critical]
