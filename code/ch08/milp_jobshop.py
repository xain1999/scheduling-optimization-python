"""Chapter 8 -- the disjunctive MILP for the job shop (for comparison)."""
import time
from itertools import combinations

import pulp


# [start:milp]
def milp_jobshop(jobs, time_limit=60):
    H = sum(d for ops in jobs for _, d in ops)
    model = pulp.LpProblem("jobshop", pulp.LpMinimize)
    s = {(j, k): model.add_variable(f"s_{j}_{k}", 0, H)
         for j, ops in enumerate(jobs) for k in range(len(ops))}
    cmax = model.add_variable("cmax", 0, H)
    model += cmax
    on = {}
    for j, ops in enumerate(jobs):
        for k, (mach, dur) in enumerate(ops):
            on.setdefault(mach, []).append((j, k, dur))
            if k > 0:
                model += s[j, k] >= s[j, k - 1] + ops[k - 1][1]
        model += cmax >= s[j, len(ops) - 1] + ops[-1][1]
    for mach, ops in on.items():           # big-M disjunctions
        for (a, ka, da), (b, kb, db) in combinations(ops, 2):
            y = model.add_variable(f"y_{a}_{b}_{mach}", 0, 1,
                                   pulp.LpBinary)
            model += s[a, ka] + da <= s[b, kb] + H * (1 - y)
            model += s[b, kb] + db <= s[a, ka] + H * y
    t0 = time.perf_counter()
    st = model.solve(pulp.HiGHS(msg=False, timeLimit=time_limit,
                                threads=1))
    if not st.has_solution:              # no schedule within the limit
        return None
    return dict(makespan=round(st.objective), bound=st.best_bound,
                optimal=st.status == pulp.LpSolveStatus.Optimal,
                seconds=time.perf_counter() - t0)
# [end:milp]
