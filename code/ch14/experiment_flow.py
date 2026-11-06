"""Chapter 14: NEH, iterated greedy and a GA on flow-shop instances."""
import csv
import statistics
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "ch07"))

from flowshop import makespan, taillard_instance
from genetic import genetic_algorithm
from iterated_greedy import iterated_greedy
from neh import neh

ROOT = Path(__file__).resolve().parents[2]
cp = {r["name"]: r for r in csv.DictReader(
    open(ROOT / "results" / "ch07_bench.csv"))}
CASES = [("ta001", 873654221, 20, 5), ("rnd20x10-1", 20101, 20, 10),
         ("rnd20x10-2", 20102, 20, 10), ("rnd20x20-1", 20201, 20, 20),
         ("rnd50x10-2", 50102, 50, 10)]
rows = []
for name, seed, n, m in CASES:
    p = taillard_instance(seed, n, m)
    nseq = neh(p)
    ig = [iterated_greedy(p, seconds=30, seed=s)[1] for s in range(3)]
    ga = [genetic_algorithm(p, seconds=30, seed=s, seeds=[nseq])[1]
          for s in range(3)]
    rows.append(dict(name=name, neh=makespan(p, nseq),
                     ig_mean=statistics.mean(ig), ig_best=min(ig),
                     ga_mean=statistics.mean(ga), ga_best=min(ga),
                     cpsat=cp[name]["cpsat"], bound=cp[name]["bound"]))
    print(rows[-1], flush=True)
with open(ROOT / "results" / "ch14_flow.csv", "w", newline="") as f:
    w = csv.DictWriter(f, fieldnames=rows[0].keys())
    w.writeheader()
    w.writerows(rows)
