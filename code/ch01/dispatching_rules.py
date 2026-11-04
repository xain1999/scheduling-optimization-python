"""Chapter 1 -- compare simple dispatching rules on one machine."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
sys.path.insert(0, str(Path(__file__).resolve().parent))

from print_shop import JOBS
from schedlib import evaluate, sequence_to_schedule

# [start:rules]
RULES = {
    "FIFO": lambda j: JOBS.index(j),   # first come, first served
    "SPT":  lambda j: j.p,             # shortest processing time
    "LPT":  lambda j: -j.p,            # longest processing time
    "EDD":  lambda j: j.d,             # earliest due date
    "WSPT": lambda j: (j.p / j.w if j.w > 0  # weighted SPT;
                       else float("inf")),   # weight 0 goes last
}


def apply_rule(rule) -> list[str]:
    """Return the job order produced by a priority rule."""
    return [j.id for j in sorted(JOBS, key=rule)]
# [end:rules]


# [start:compare]
if __name__ == "__main__":
    cols = ["Cmax", "sumC", "sumwC", "Lmax", "sumT", "sumwT", "nTardy"]
    print(f"{'rule':6}" + "".join(f"{c:>8}" for c in cols))
    for name, rule in RULES.items():
        order = apply_rule(rule)
        kpi = evaluate(JOBS, sequence_to_schedule(JOBS, order))
        print(f"{name:6}" + "".join(f"{kpi[c]:>8}" for c in cols))
# [end:compare]
