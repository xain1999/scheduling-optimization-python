"""Chapter 6: case study: training jobs on a small, mixed GPU cluster."""
import random
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from ortools.sat.python import cp_model

from schedlib import Task
from schedlib.results import save
from schedlib.status import check_cpsat

# [start:data]
GPUS = {                    # name: (memory in GB, relative speed)
    "fast-1": (80, 2.0), "fast-2": (80, 2.0),
    "old-1": (24, 1.0), "old-2": (24, 1.0), "old-3": (24, 1.0),
}


def training_jobs(n=24, seed=5):
    """Each job: submit time, work (hours on an old GPU), memory need,
    how much it gains from a fast GPU, and a priority weight."""
    rng = random.Random(seed)
    jobs = []
    for i in range(n):
        jobs.append(dict(
            name=f"J{i+1}", release=rng.randint(0, 20),
            work=rng.randint(2, 12),
            memory=rng.choice([8, 16, 16, 40, 60]),
            gain=rng.uniform(1.2, 2.0),
            weight=rng.choice([1, 1, 2, 3])))
    return jobs


def duration(job, gpu):
    """Hours job needs on gpu, or None if it does not fit in memory."""
    memory, speed = GPUS[gpu]
    if job["memory"] > memory:
        return None
    factor = job["gain"] if speed > 1 else 1.0   # unrelated machines
    return max(1, round(job["work"] / factor))
# [end:data]


# [start:greedy]
def greedy(jobs):
    """FIFO by submit time.  Each job goes where it finishes first."""
    free = {g: 0 for g in GPUS}
    plan = []
    for job in sorted(jobs, key=lambda j: j["release"]):
        options = []
        for g in GPUS:
            d = duration(job, g)
            if d is not None:
                s = max(free[g], job["release"])
                options.append((s + d, s, g))
        end, start, g = min(options)
        free[g] = end
        plan.append(Task(job["name"], g, start, end))
    return plan
# [end:greedy]


def weighted_flow(jobs, plan):
    end = {t.job: t.end for t in plan}
    return sum(j["weight"] * (end[j["name"]] - j["release"]) for j in jobs)


# [start:model]
def optimise(jobs, time_limit=30, hint_plan=None):
    H = max(j["release"] for j in jobs) + sum(j["work"] for j in jobs)
    m = cp_model.CpModel()
    start, end, on, per_gpu = {}, {}, {}, {g: [] for g in GPUS}
    flow = []
    for j in jobs:
        n = j["name"]
        start[n] = m.new_int_var(j["release"], H, f"s_{n}")
        end[n] = m.new_int_var(j["release"], H, f"e_{n}")
        choices = []
        for g in GPUS:
            d = duration(j, g)
            if d is None:
                continue                        # not eligible
            on[n, g] = m.new_bool_var(f"{n}@{g}")
            per_gpu[g].append(m.new_optional_interval_var(
                start[n], d, end[n], on[n, g], f"iv_{n}_{g}"))
            choices.append(on[n, g])
        m.add_exactly_one(choices)
        flow.append(j["weight"] * (end[n] - j["release"]))
    for g in GPUS:
        m.add_no_overlap(per_gpu[g])
    m.minimize(sum(flow))
    if hint_plan:
        for t in hint_plan:
            m.add_hint(start[t.job], t.start)
            for g in GPUS:
                if (t.job, g) in on:
                    m.add_hint(on[t.job, g], g == t.resource)
    solver = cp_model.CpSolver()
    solver.parameters.max_time_in_seconds = time_limit
    solver.parameters.num_workers = 8
    status = check_cpsat(solver, solver.solve(m))
    plan = [Task(j["name"], g, solver.value(start[j["name"]]),
                 solver.value(end[j["name"]]))
            for j in jobs for g in GPUS
            if (j["name"], g) in on and solver.value(on[j["name"], g])]
    return plan, status, solver.best_objective_bound
# [end:model]


if __name__ == "__main__":
    # [start:run]
    jobs = training_jobs()
    base = greedy(jobs)
    print("greedy  : weighted flow time", weighted_flow(jobs, base))
    plan, status, bound = optimise(jobs, hint_plan=base)
    print(f"CP-SAT  : weighted flow time {weighted_flow(jobs, plan)} "
          f"({status}, lower bound {bound:.0f})")
    for g in GPUS:
        mine = sorted((t for t in plan if t.resource == g),
                      key=lambda t: t.start)
        print(f"  {g:7}", " ".join(t.job for t in mine))
    # [end:run]
    save("ch06_gpu", {"greedy": base, "cpsat": plan})   # for the figure
