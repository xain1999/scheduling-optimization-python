"""Chapter 2 -- model size and LP-relaxation strength of the two MILPs."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
sys.path.insert(0, str(Path(__file__).resolve().parent))

import pulp

from instances import JOBS
from milp_disjunctive import build_disjunctive
from milp_time_indexed import build_time_indexed
from schedlib.status import check_pulp

# [start:bounds]
for name, build in [("disjunctive", build_disjunctive),
                    ("time-indexed", build_time_indexed)]:
    model, _ = build(JOBS, relax=True)       # binaries -> [0, 1]
    stats = model.solve(pulp.HiGHS(msg=False, threads=1))
    check_pulp(stats)
    print(f"{name:13} variables={len(model.variables()):5}  "
          f"constraints={len(model.constraints()):4}  "
          f"LP bound={stats.objective:6.2f}")
# [end:bounds]
