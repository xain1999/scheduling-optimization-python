"""Chapter 5 -- turn benchmark CSVs into the table and figure."""
import csv
import statistics
import sys
from collections import defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))


ROOT = Path(__file__).resolve().parents[2]
rows = list(csv.DictReader(open(ROOT / "results" / "ch05_small.csv")))
methods = ["EDD", "WSPT", "ATC k=2", "ATC best k", "MILP time-ix",
           "CP-SAT 10s", "DP"]
gap, nopt, secs = defaultdict(list), defaultdict(int), defaultdict(list)
missing = defaultdict(int)
for r in rows:
    secs[r["method"]].append(float(r["seconds"]))
    if r["value"] in ("", "None"):         # no schedule within the limit
        missing[r["method"]] += 1
        continue
    v, opt = float(r["value"]), float(r["opt"])
    if opt > 0:                    # gaps only where the optimum is > 0
        gap[r["method"]].append(100 * (v - opt) / opt)
    nopt[r["method"]] += v == opt
lines = []
for mth in methods:
    g = sorted(gap[mth])
    t = secs[mth]
    note = f"$^{{{missing[mth]}}}$" if missing[mth] else ""
    if g:                          # mean, (conventional) median, worst
        stats = (f"{statistics.mean(g):.1f} & "
                 f"{statistics.median(g):.1f} & {max(g):.1f}")
    else:                          # no usable instance: say so
        stats = "-- & -- & --"
    lines.append(f"{mth}{note} & {stats} & {nopt[mth]}/{len(t)} & "
                 f"{statistics.mean(t):.2f} \\\\")
print("instances without a schedule:", dict(missing))
(ROOT / "tables").mkdir(exist_ok=True)
(ROOT / "tables" / "ch05_small.tex").write_text("\n".join(lines) + "\n")
print("\n".join(lines))

large = list(csv.DictReader(open(ROOT / "results" / "ch05_large.csv")))
hint = list(csv.DictReader(open(ROOT / "results" / "ch05_large_hint.csv")))
lines = []
for r, h in zip(large, hint):
    lines.append(f"{r['tf']} & {r['rdd']} & {float(r['atc']):.0f} & "
                 f"{float(r['cpsat']):.0f} & {float(h['hinted']):.0f} & "
                 f"{float(h['bound']):.0f} \\\\")
(ROOT / "tables" / "ch05_large.tex").write_text("\n".join(lines) + "\n")
print("\n".join(lines))
