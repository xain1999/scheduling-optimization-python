"""Chapter 7 -- NEH and CP-SAT on Taillard-style flow-shop instances."""
import csv
from pathlib import Path

from cpsat_flowshop import cpsat_flowshop
from flowshop import makespan, taillard_instance
from neh import lower_bound, neh

ROOT = Path(__file__).resolve().parents[2]

# [start:bench]
INSTANCES = [("ta001", 873654221, 20, 5)] + [
    (f"rnd{n}x{m}-{k}", 1000 * n + 10 * m + k, n, m)
    for n, m in [(20, 5), (20, 10), (20, 20), (50, 10)]
    for k in (1, 2)]

rows = []
for name, seed, n, m in INSTANCES:
    p = taillard_instance(seed, n, m)
    seq = neh(p)
    res = cpsat_flowshop(p, permutation=True, time_limit=60, hint=seq)
    rows.append(dict(name=name, n=n, m=m, lb=lower_bound(p),
                     neh=makespan(p, seq), cpsat=res["cmax"],
                     bound=res["bound"], optimal=res["optimal"],
                     seconds=round(res["seconds"], 1)))
    print(rows[-1], flush=True)
# [end:bench]

with open(ROOT / "results" / "ch07_bench.csv", "w", newline="") as f:
    w = csv.DictWriter(f, fieldnames=rows[0].keys())
    w.writeheader(); w.writerows(rows)
