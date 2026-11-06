"""Chapter 13: ATCS: the ATC rule extended to sequence-dependent setups."""
import math
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "ch04"))

from paint_shop import changeover, evaluate, heuristic_order, paint_jobs


# [start:atcs]
def atcs_order(jobs, k1=2.0, k2=1.0, start_colour=0):
    """A variant of the ATCS rule of Lee, Bhaskaran and Pinedo (1997).

    I_j = (w_j/p_j) exp(-slack_j / (k1 pbar)) exp(-s_lj / (k2 sbar))
    where s_lj is the changeover from the current colour l to job j,
    slack_j = max(0, d_j - p_j - s_lj - t), and sbar is the mean
    changeover from the current colour (the original uses the slack
    without s_lj and the instance-wide mean setup time).
    """
    remaining = list(jobs)
    t, colour, order = 0, start_colour, []
    while remaining:
        pbar = sum(j["p"] for j in remaining) / len(remaining)
        setups = [changeover(colour, j["colour"]) for j in remaining]
        sbar = max(1e-9, sum(setups) / len(setups))

        def index(j):
            s = changeover(colour, j["colour"])
            slack = max(0, j["due"] - j["p"] - s - t)
            return (j["w"] / j["p"] * math.exp(-slack / (k1 * pbar))
                    * math.exp(-s / (k2 * sbar)))
        nxt = max(remaining, key=index)
        t += changeover(colour, nxt["colour"]) + nxt["p"]
        colour = nxt["colour"]
        order.append(nxt["name"])
        remaining.remove(nxt)
    return order
# [end:atcs]


if __name__ == "__main__":
    # [start:run]
    jobs = paint_jobs()
    print("colour groups (planner):  tardiness %d, changeovers %d"
          % evaluate(jobs, heuristic_order(jobs)))
    print("ATCS k1=2, k2=1        :  tardiness %d, changeovers %d"
          % evaluate(jobs, atcs_order(jobs)))
    grid = [(k1, k2) for k1 in (0.5, 1, 2, 3, 4, 6)
            for k2 in (0.25, 0.5, 1, 2, 4)]
    best = min(grid,
               key=lambda k: evaluate(jobs, atcs_order(jobs, *k)))
    print(f"ATCS tuned k1={best[0]}, k2={best[1]}:  tardiness %d, "
          f"changeovers %d" % evaluate(jobs, atcs_order(jobs, *best)))
    # [end:run]
