"""Chapter 16 -- a machine breaks down: repair or re-optimise?"""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "ch08"))
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from ortools.sat.python import cp_model

from cpsat_jobshop import solve_jobshop
from jobshop import read_instance
from schedlib.status import check_cpsat

RESULTS = Path(__file__).resolve().parents[2] / "results"


# [start:rightshift]
def right_shift(jobs, starts, machine, t_down, t_up):
    """Keep every sequence; push operations later only as far as
    needed.  Operations on `machine` cannot run in [t_down, t_up); an
    interrupted operation restarts from scratch after the repair."""
    order = sorted(starts, key=lambda op: starts[op])
    new, job_end, mach_end = {}, {}, {}
    for (j, k) in order:
        mc, d = jobs[j][k]
        s = max(starts[j, k], job_end.get(j, 0), mach_end.get(mc, 0))
        if mc == machine and s < t_up and s + d > t_down:
            s = t_up                          # wait for the repair
        new[j, k] = s
        job_end[j] = mach_end[mc] = s + d
    return new
# [end:rightshift]


# [start:reopt]
def reoptimise(jobs, starts, machine, t_down, t_up, stability=0,
               time_limit=30):
    """Re-solve from time t_down.  Operations already started stay
    put, except one interrupted on the failed machine: it restarts
    from scratch after the repair (its progress is lost).  The
    breakdown is a fixed interval on the machine.  With stability > 0,
    each time unit an operation moves costs `stability`.
    """
    H = sum(d for ops in jobs for _, d in ops) + t_up
    m = cp_model.CpModel()
    s, ends, per_machine, moves, free = {}, [], {}, [], []
    for j, ops in enumerate(jobs):
        for k, (mc, d) in enumerate(ops):
            done_before = starts[j, k] + d <= t_down
            hit = mc == machine and not done_before   # interrupted
            if starts[j, k] < t_down and not hit:    # history is fixed
                s[j, k] = m.new_constant(starts[j, k])
            else:
                s[j, k] = m.new_int_var(t_down, H, "")
                free.append((j, k))
                dev = m.new_int_var(0, H, "")
                m.add_abs_equality(dev, s[j, k] - starts[j, k])
                moves.append(dev)
            per_machine.setdefault(mc, []).append(
                m.new_fixed_size_interval_var(s[j, k], d, ""))
            if k:
                m.add(s[j, k] >= s[j, k - 1] + ops[k - 1][1])
        ends.append(s[j, len(ops) - 1] + ops[-1][1])
    per_machine[machine].append(
        m.new_fixed_size_interval_var(t_down, t_up - t_down, "down"))
    for ivs in per_machine.values():
        m.add_no_overlap(ivs)
    cmax = m.new_int_var(0, H, "cmax")
    m.add_max_equality(cmax, ends)
    m.minimize(100 * cmax + stability * sum(moves))
    for op in free:                     # hint only the free variables
        m.add_hint(s[op], max(t_down, starts[op]))
    solver = cp_model.CpSolver()
    solver.parameters.max_time_in_seconds = time_limit
    solver.parameters.num_workers = 8
    status = check_cpsat(solver, solver.solve(m))
    return {op: solver.value(v) for op, v in s.items()}, status
# [end:reopt]


def load_or_solve_plan(jobs, path=RESULTS / "ch16_base_plan.json"):
    """ft10 has many optimal schedules and a multi-worker solve may
    return any of them, so the plan used in the book is stored once."""
    if path.exists():
        return {tuple(map(int, k.split(","))): v
                for k, v in json.loads(path.read_text()).items()}
    plan = solve_jobshop(jobs, time_limit=60)["starts"]
    path.write_text(json.dumps({f"{j},{k}": v
                                for (j, k), v in plan.items()}))
    return plan


def summary(jobs, old, new):
    cmax = max(new[j, len(o) - 1] + o[-1][1] for j, o in enumerate(jobs))
    moved = sum(1 for op in old if new[op] != old[op])
    shift = sum(abs(new[op] - old[op]) for op in old)
    return cmax, moved, shift


if __name__ == "__main__":
    # [start:run]
    jobs = read_instance("ft10")
    plan = load_or_solve_plan(jobs)           # the published schedule
    print("original plan: makespan", summary(jobs, plan, plan)[0])
    machine, t_down, t_up = 4, 200, 300       # machine 4 down 200-300
    for name, (new, status) in [
            ("right-shift repair", (right_shift(jobs, plan, machine,
                                                t_down, t_up), "-")),
            ("re-optimise", reoptimise(jobs, plan, machine,
                                       t_down, t_up)),
            ("re-optimise + stability", reoptimise(
                jobs, plan, machine, t_down, t_up, stability=1))]:
        cmax, moved, shift = summary(jobs, plan, new)
        print(f"{name:24} makespan {cmax:4}  moved {moved:3}  "
              f"shift {shift:5}  {status}")
    # [end:run]
