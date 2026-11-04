"""Core data structures and objectives used throughout the book."""
from __future__ import annotations

from dataclasses import dataclass


# [start:job]
@dataclass(frozen=True)
class Job:
    """A job to be processed. All times are integers (e.g. minutes)."""
    id: str
    p: int            # processing time
    r: int = 0        # release date: earliest possible start
    d: int = 0        # due date
    w: int = 1        # weight (importance)


@dataclass(frozen=True)
class Task:
    """One block of work placed on a resource in a schedule."""
    job: str
    resource: str
    start: int
    end: int


@dataclass
class SolveResult:
    """What every solve_* function in the book returns."""
    schedule: list[Task] | None   # None if nothing feasible found
    objective: float | None       # value of the best solution found
    bound: float                  # proven lower bound (minimisation)
    optimal: bool                 # True if optimality was proven
    seconds: float                # wall-clock solve time
# [end:job]


# [start:sequence]
def sequence_to_schedule(jobs: list[Job], order: list[str],
                         resource: str = "M1") -> list[Task]:
    """Place jobs on one machine in the given order, as early as
    possible.

    A job can start only when the machine is free *and* the job has
    been released.
    """
    by_id = {j.id: j for j in jobs}
    t = 0
    schedule = []
    for job_id in order:
        job = by_id[job_id]
        start = max(t, job.r)
        end = start + job.p
        schedule.append(Task(job_id, resource, start, end))
        t = end
    return schedule
# [end:sequence]


# [start:metrics]
def completion_times(schedule: list[Task]) -> dict[str, int]:
    """C_j: the time the last piece of job j finishes."""
    c: dict[str, int] = {}
    for task in schedule:
        c[task.job] = max(c.get(task.job, 0), task.end)
    return c


def evaluate(jobs: list[Job],
             schedule: list[Task]) -> dict[str, float]:
    """Compute the classic scheduling objectives for a schedule."""
    c = completion_times(schedule)
    lateness = {j.id: c[j.id] - j.d for j in jobs}
    tardiness = {k: max(0, v) for k, v in lateness.items()}
    return {
        "Cmax":   max(c.values()),               # makespan
        "sumC":   sum(c.values()),               # total completion
        "sumwC":  sum(j.w * c[j.id] for j in jobs),
        "Lmax":   max(lateness.values()),        # maximum lateness
        "sumT":   sum(tardiness.values()),       # total tardiness
        "sumwT":  sum(j.w * tardiness[j.id] for j in jobs),
        "nTardy": sum(1 for t in tardiness.values() if t > 0),
    }
# [end:metrics]


# [start:checkjobs]
def check_jobs(jobs: list[Job]) -> None:
    """Reject input outside the single-machine models' assumptions.

    Integer data, unique ids, p > 0, r >= 0, w >= 0.  Due dates may be
    any integer: d < 0 means a job is already overdue at time 0.
    (Type hints are not checked at run time; this function is.)
    """
    if len({j.id for j in jobs}) != len(jobs):
        raise ValueError("job ids must be unique")
    for j in jobs:
        if not all(isinstance(v, int) for v in (j.p, j.r, j.d, j.w)):
            raise ValueError(f"{j.id}: times and weights must be ints")
        if j.p <= 0 or j.r < 0 or j.w < 0:
            raise ValueError(f"{j.id}: need p > 0, r >= 0, w >= 0")
# [end:checkjobs]


# [start:validate]
class InvalidSchedule(ValueError):
    """A schedule that breaks a rule of the problem."""


def validate_single_machine(jobs: list[Job],
                            schedule: list[Task]) -> None:
    """Raise InvalidSchedule if the schedule breaks any rule.

    Never trust a solver blindly: an independent checker catches
    modelling mistakes that the solver happily "optimises".  (Plain
    if-tests, not assert: `python -O` silently removes asserts.)
    """
    def fail(msg):
        raise InvalidSchedule(msg)
    check_jobs(jobs)                     # bad input is not a schedule
    by_id = {j.id: j for j in jobs}      # error: ValueError, raised
    if schedule is None:
        fail("no schedule")
    if len({t.resource for t in schedule}) > 1:
        fail("a single-machine schedule uses one resource")
    if sorted(t.job for t in schedule) != sorted(by_id):
        fail("every job must appear exactly once")
    for t in schedule:
        job = by_id[t.job]
        if t.end - t.start != job.p:
            fail(f"{t.job}: wrong duration")
        if t.start < job.r:
            fail(f"{t.job}: starts before release")
    ordered = sorted(schedule, key=lambda t: t.start)
    for a, b in zip(ordered, ordered[1:]):
        if a.end > b.start:
            fail(f"{a.job} and {b.job} overlap")
# [end:validate]
