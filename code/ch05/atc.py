"""Chapter 5 -- the Apparent Tardiness Cost (ATC) dispatching rule."""
import math
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from schedlib import Job, evaluate, sequence_to_schedule


# [start:atc]
def atc_order(jobs: list[Job], k: float = 2.0) -> list[str]:
    """Dynamic rule: each time the machine is free, pick the job with
    the largest index

        I_j(t) = (w_j / p_j) * exp(-max(0, d_j - p_j - t) / (k * pbar))

    WSPT for jobs that are already (nearly) late, discounted
    exponentially for jobs whose slack is still large.  k sets how far
    ahead the rule looks; pbar is the mean processing time.
    Requires k > 0 and every p_j > 0.
    """
    if k <= 0 or any(j.p <= 0 for j in jobs):
        raise ValueError("ATC needs k > 0 and positive durations")
    remaining = list(jobs)
    t, order = 0, []
    while remaining:
        pbar = sum(j.p for j in remaining) / len(remaining)
        def index(j):
            slack = max(0.0, j.d - j.p - t)
            return j.w / j.p * math.exp(-slack / (k * pbar))
        nxt = max(remaining, key=index)
        order.append(nxt.id)
        remaining.remove(nxt)
        t += nxt.p
    return order


def best_atc(jobs, ks=(0.5, 1, 1.5, 2, 3, 4, 5)):
    """Try several look-ahead values and keep the best schedule."""
    def cost(order):
        schedule = sequence_to_schedule(jobs, order)
        return evaluate(jobs, schedule)["sumwT"]
    return min((atc_order(jobs, k) for k in ks), key=cost)
# [end:atc]
