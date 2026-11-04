"""Chapter 3 -- a two-variable LP: the print shop's weekly product mix."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import pulp

from schedlib.status import check_pulp


# [start:lp]
model = pulp.LpProblem("product_mix", pulp.LpMaximize)
a = model.add_variable("brochures", lowBound=0)    # batches per week
b = model.add_variable("catalogues", lowBound=0)

model += 30 * a + 40 * b                           # profit per batch
model += 2 * a + 3 * b <= 120, "press_hours"
model += 2 * a + 1 * b <= 80, "cutter_hours"
model += b <= 30, "catalogue_demand"

stats = model.solve(pulp.HiGHS(msg=False, threads=1))
check_pulp(stats)                 # read values only after a solution
print(f"brochures={a.value():.1f}  catalogues={b.value():.1f}  "
      f"profit={stats.objective:.0f}")
for c in model.constraints():
    print(f"{c.name:17} slack={abs(c.slack):5.1f}  "
          f"shadow price={c.pi:5.2f}")
# [end:lp]
