"""Chapter 2: instances for 1 | r_j | sum w_j T_j."""
import random
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from schedlib import Job, check_jobs

# [start:instance]
# The print shop on a busy day: jobs now arrive over time (r_j).
JOBS = [
    Job("J1", p=4, r=0,  d=8,  w=3),
    Job("J2", p=7, r=2,  d=16, w=1),
    Job("J3", p=2, r=5,  d=9,  w=3),
    Job("J4", p=9, r=0,  d=25, w=2),
    Job("J5", p=3, r=8,  d=14, w=2),
    Job("J6", p=6, r=10, d=22, w=2),
    Job("J7", p=5, r=3,  d=12, w=1),
    Job("J8", p=8, r=12, d=34, w=1),
]
# [end:instance]


# [start:horizon]
def horizon(jobs: list[Job]) -> int:
    """An upper bound on the end of any sensible schedule.

    Wait for the last release, then run every job back to back: some
    optimal schedule always finishes by then, because it never pays to
    leave the machine idle when every job has already arrived.
    Every model of this chapter calls it first, so it also rejects bad
    input (see check_jobs in schedlib).
    """
    check_jobs(jobs)
    return max(j.r for j in jobs) + sum(j.p for j in jobs)
# [end:horizon]


# [start:random]
def random_instance(n: int, seed: int, spread: float = 0.5,
                    slack: float = 0.5) -> list[Job]:
    """Random 1|r_j|sum w_j T_j instance in the style of the literature.

    Releases are spread over `spread` x total work. Each due date gives
    the job a random amount of slack after its earliest finish.
    """
    rng = random.Random(seed)
    p = [rng.randint(1, 10) for _ in range(n)]
    total = sum(p)
    jobs = []
    for i in range(n):
        r = rng.randint(0, int(spread * total))
        d = r + p[i] + rng.randint(0, int(slack * total))
        w = rng.randint(1, 5)
        jobs.append(Job(f"J{i+1}", p=p[i], r=r, d=d, w=w))
    return jobs
# [end:random]
