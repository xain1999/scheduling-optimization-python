"""Chapter 5: Moore-Hodgson: minimise the number of late jobs."""
import itertools
import random
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from schedlib import Job, evaluate, sequence_to_schedule


# [start:mh]
def moore_hodgson(jobs: list[Job]) -> list[str]:
    """Optimal order for 1 || sum U_j.

    Go through the jobs in EDD order.  Whenever the current job would
    be late, throw out the longest job scheduled so far.  Thrown-out
    jobs are late anyway, so they go at the end in any order.
    """
    on_time, t, late = [], 0, []
    for job in sorted(jobs, key=lambda j: j.d):
        on_time.append(job)
        t += job.p
        if t > job.d:
            longest = max(on_time, key=lambda j: j.p)
            on_time.remove(longest)
            late.append(longest)
            t -= longest.p
    return [j.id for j in on_time] + [j.id for j in late]
# [end:mh]


if __name__ == "__main__":
    # [start:check]
    rng = random.Random(0)
    for trial in range(200):                 # compare with brute force
        n = rng.randint(3, 8)
        jobs = [Job(f"J{i}", p=rng.randint(1, 9), d=rng.randint(1, 25))
                for i in range(n)]
        mh = evaluate(jobs, sequence_to_schedule(
            jobs, moore_hodgson(jobs)))["nTardy"]
        best = min(evaluate(jobs, sequence_to_schedule(jobs, list(o)))
                   ["nTardy"] for o in itertools.permutations(
                       j.id for j in jobs))
        assert mh == best, (jobs, mh, best)
    print("Moore-Hodgson matched brute force on 200 random instances")
    # [end:check]
