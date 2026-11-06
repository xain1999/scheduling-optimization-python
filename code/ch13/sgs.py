"""Chapter 13: serial and parallel schedule generation schemes."""
import random
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "ch09"))

from rcpsp import check_project, serial_sgs


# [start:parallel]
def parallel_sgs(project, capacity, priority):
    """Time-oriented: at each decision time t, start as many eligible
    activities as fit (in priority order), then jump to the next
    completion time.  Produces *non-delay* schedules.  Zero-duration
    activities (milestones) use no capacity, as in the serial scheme
    and in CP-SAT: they start once their predecessors are done."""
    check_project(project, capacity)
    if not project:                    # explicit policy: empty project
        return 0, {}
    start, finish = {}, {}
    t, running = 0, []
    while len(start) < len(project):
        running = [a for a in running if finish[a] > t]
        free = {r: cap - sum(project[a][1].get(r, 0) for a in running)
                for r, cap in capacity.items()}
        progress = True
        while progress:          # zero-duration activities finish at t
            progress = False     # and can release successors at once
            eligible = sorted((a for a in project if a not in start
                               and all(p in finish and finish[p] <= t
                                       for p in project[a][2])),
                              key=priority)
            for a in eligible:
                need, dur = project[a][1], project[a][0]
                if dur == 0 or all(need.get(r, 0) <= free[r]
                                   for r in capacity):
                    start[a], finish[a] = t, t + dur
                    progress = True
                    if dur > 0:
                        running.append(a)
                        for r in need:
                            free[r] -= need[r]
        if len(start) == len(project):   # e.g. a zero-duration sink
            break
        future = [f for f in finish.values() if f > t]
        if not future:           # cannot happen after check_project
            raise RuntimeError(f"no progress possible at time {t}")
        t = min(future)
    return max(finish.values()), start
# [end:parallel]


# [start:rules]
def priority_rules(project):
    """LFT: latest finish time (backward pass, ignoring crews).
    MTS: most total successors.
    GRPW: greatest rank positional weight."""
    succ = {a: [b for b in project if a in project[b][2]]
            for a in project}
    memo = {}

    def all_succ(a):
        if a not in memo:
            s = set(succ[a])
            for b in succ[a]:
                s |= all_succ(b)
            memo[a] = s
        return memo[a]
    lft, horizon = {}, sum(d for d, _, _ in project.values())

    def latest_finish(a):
        if a not in lft:
            lft[a] = min((latest_finish(b) - project[b][0]
                          for b in succ[a]), default=horizon)
        return lft[a]
    return {
        "LFT":  lambda a: latest_finish(a),
        "MTS":  lambda a: -len(all_succ(a)),
        "GRPW": lambda a: -(project[a][0] +
                            sum(project[b][0] for b in succ[a])),
        "SPT":  lambda a: project[a][0],
    }
# [end:rules]


# [start:sampling]
def random_sampling(project, capacity, base, n=200, seed=0,
                    scheme=None):
    """Regret-free biased sampling: perturb a good priority rule with
    random noise many times and keep the best schedule."""
    scheme = scheme or serial_sgs
    rng = random.Random(seed)
    values = {a: base(a) for a in project}
    spread = (max(values.values()) - min(values.values())) or 1
    best = (float("inf"), None)
    for _ in range(n):
        noise = {a: values[a] + rng.gauss(0, 0.1 * spread)
                 for a in project}
        result = scheme(project, capacity, lambda a: noise[a])
        best = min(best, result, key=lambda r: r[0])
    return best
# [end:sampling]
