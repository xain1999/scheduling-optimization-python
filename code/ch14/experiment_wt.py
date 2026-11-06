"""Chapter 14: descent, annealing and tabu: 40-job weighted tardiness."""
import csv
import statistics
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "ch05"))

from atc import best_atc
from local_search import (descent, simulated_annealing, tabu_search,
                          total_wt)
from wt_instances import instance_seed, wt_instance

ROOT = Path(__file__).resolve().parents[2]
hint = {(r["tf"], r["rdd"]): float(r["hinted"]) for r in csv.DictReader(
    open(ROOT / "results" / "ch05_large_hint.csv"))}

# [start:experiment]
rows = []
for tf in ("0.4", "0.6", "0.8"):
    for rdd in ("0.2", "0.6", "1.0"):
        jobs_obj = wt_instance(40, float(tf), float(rdd),
                               instance_seed(float(tf), float(rdd), 7))
        ids = [j.id for j in jobs_obj]
        jobs = [(j.p, j.d, j.w) for j in jobs_obj]
        start = [ids.index(x) for x in best_atc(jobs_obj)]
        atc = total_wt(jobs, start)
        _, desc = descent(jobs, start)
        sa = [simulated_annealing(jobs, start, seconds=5, seed=s)[1]
              for s in range(5)]
        _, tabu = tabu_search(jobs, start, seconds=5)
        rows.append(dict(tf=tf, rdd=rdd, atc=atc, descent=desc,
                         sa_mean=statistics.mean(sa), sa_best=min(sa),
                         tabu=tabu, cpsat=hint[tf, rdd]))
        print(rows[-1], flush=True)
# [end:experiment]
with open(ROOT / "results" / "ch14_wt.csv", "w", newline="") as f:
    w = csv.DictWriter(f, fieldnames=rows[0].keys())
    w.writeheader()
    w.writerows(rows)
