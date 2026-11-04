"""Chapter 8 -- Giffler-Thompson: active schedules with a priority rule."""


# [start:gt]
def giffler_thompson(jobs, priority):
    """Build an *active* schedule (no operation could start earlier
    without delaying another).  priority(job, op_index, ready) -> key,
    where ready is the time the operation became available (its job
    predecessor ended); the smallest key wins in the conflict set.
    """
    n = len(jobs)
    nxt = [0] * n                      # next operation of each job
    job_ready = [0] * n                # when each job's last op ends
    mach_ready = {}
    starts = {}
    while any(nxt[j] < len(jobs[j]) for j in range(n)):
        # earliest completion among all schedulable operations
        cand = []
        for j in range(n):
            if nxt[j] < len(jobs[j]):
                mach, dur = jobs[j][nxt[j]]
                s = max(job_ready[j], mach_ready.get(mach, 0))
                cand.append((s + dur, s, j, mach))
        c_star, _, _, m_star = min(cand)
        # conflict set: ops on that machine that could start before c*
        conflict = [(s, j) for _, s, j, mach in cand
                    if mach == m_star and s < c_star]
        s, j = min(conflict, key=lambda sj: priority(
            sj[1], nxt[sj[1]], job_ready[sj[1]]))
        dur = jobs[j][nxt[j]][1]
        starts[j, nxt[j]] = s
        job_ready[j] = mach_ready[m_star] = s + dur
        nxt[j] += 1
    makespan = max(job_ready)
    return makespan, starts
# [end:gt]


# [start:rules]
def rules(jobs):
    """Classic priority rules; each returns a key (smaller = first)."""
    remaining = lambda j, k: sum(d for _, d in jobs[j][k:])
    return {
        "SPT":  lambda j, k, ready: jobs[j][k][1],
        "LPT":  lambda j, k, ready: -jobs[j][k][1],
        "MWKR": lambda j, k, ready: -remaining(j, k),  # most work left
        "LWKR": lambda j, k, ready: remaining(j, k),
        "FIFO": lambda j, k, ready: (ready, j),  # first come first
    }
# [end:rules]
