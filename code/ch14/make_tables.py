"""Chapter 14: tables from the experiment CSVs."""
import csv
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
rows = list(csv.DictReader(open(ROOT / "results" / "ch14_wt.csv")))
lines = []
for r in rows:
    lines.append(f"{r['tf']} & {r['rdd']} & {r['atc']} & {r['descent']} & "
                 f"{float(r['sa_mean']):.0f} & {r['sa_best']} & "
                 f"{r['tabu']} & {float(r['cpsat']):.0f} \\\\")
(ROOT / "tables" / "ch14_wt_rows.tex").write_text("\n".join(lines) + "\n")
print("\n".join(lines))
rows = list(csv.DictReader(open(ROOT / "results" / "ch14_flow.csv")))
lines = []
for r in rows:
    lines.append(f"{r['name']} & {r['neh']} & {float(r['ig_mean']):.0f} & "
                 f"{r['ig_best']} & {float(r['ga_mean']):.0f} & "
                 f"{r['ga_best']} & {r['cpsat']} & {r['bound']} \\\\")
(ROOT / "tables" / "ch14_flow_rows.tex").write_text("\n".join(lines) + "\n")
print("\n".join(lines))
