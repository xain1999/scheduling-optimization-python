"""Chapter 2 -- head-to-head comparison of the three models.

Writes results/ch02_compare.csv and the LaTeX table used in the book.
All solvers run single-threaded so the comparison is fair.
"""
import csv
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
sys.path.insert(0, str(Path(__file__).resolve().parent))

from cpsat_model import solve_cpsat
from instances import random_instance
from milp_disjunctive import solve_disjunctive
from milp_time_indexed import solve_time_indexed
from schedlib import evaluate, validate_single_machine

ROOT = Path(__file__).resolve().parents[2]
SIZES = [8, 10, 12, 15, 20, 30]
SEEDS = [0, 1, 2]
LIMIT = 30  # seconds per run

# [start:experiment]
METHODS = {
    "MILP big-M":   lambda J: solve_disjunctive(J, LIMIT, threads=1),
    "MILP time-ix": lambda J: solve_time_indexed(J, LIMIT, threads=1),
    "CP-SAT":       lambda J: solve_cpsat(J, LIMIT, workers=1),
}

rows = []
for n in SIZES:
    for seed in SEEDS:
        jobs = random_instance(n, seed)
        for name, solve in METHODS.items():
            res = solve(jobs)
            if res.schedule is not None:
                # trust, but verify
                validate_single_machine(jobs, res.schedule)
                value = evaluate(jobs, res.schedule)["sumwT"]
            else:
                value = None
            rows.append(dict(n=n, seed=seed, method=name,
                             value=value, optimal=res.optimal,
                             seconds=res.seconds))
            print(n, seed, f"{name:13}", value, res.optimal,
                  f"{res.seconds:.1f}s", flush=True)
# [end:experiment]

(ROOT / "results").mkdir(exist_ok=True)
with open(ROOT / "results" / "ch02_compare.csv", "w", newline="") as f:
    w = csv.DictWriter(f, fieldnames=rows[0].keys())
    w.writeheader()
    w.writerows(rows)

# ----- summarise into a LaTeX table ----------------------------------
best = {}
for r in rows:
    if r["value"] is not None:
        k = (r["n"], r["seed"])
        best[k] = min(best.get(k, float("inf")), r["value"])

lines = []
for n in SIZES:
    cells = [str(n)]
    for name in METHODS:
        rs = [r for r in rows if r["n"] == n and r["method"] == name]
        n_opt = sum(r["optimal"] for r in rs)
        avg_t = sum(r["seconds"] for r in rs) / len(rs)
        gaps = []
        for r in rs:
            b = best[(r["n"], r["seed"])]
            if r["value"] is None:
                gaps.append(None)
            else:
                gaps.append(0.0 if r["value"] == b else
                            100.0 * (r["value"] - b) / max(b, 1))
        gap_txt = ("--" if any(g is None for g in gaps)
                   else f"{sum(gaps) / len(gaps):.1f}")
        time_txt = f"{avg_t:.1f}" if avg_t >= 0.1 else "<0.1"
        cells += [f"{n_opt}/{len(rs)}", time_txt, gap_txt]
    lines.append(" & ".join(cells) + r" \\")

(ROOT / "tables").mkdir(exist_ok=True)
(ROOT / "tables" / "ch02_compare.tex").write_text("\n".join(lines) + "\n")
print("\n".join(lines))
