"""Chapter 8 -- benchmark table."""
import csv
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
rows = list(csv.DictReader(open(ROOT / "results" / "ch08_bench.csv")))
lines = []
for r in rows:
    star = "*" if r["cp_opt"] == "True" else ""
    milp = (f"{r['milp']}{'*' if r['milp_opt'] == 'True' else ''}"
            if r["milp"] else "--")
    lines.append(f"{r['name']} & ${r['n']} \\times {r['m']}$ & {r['opt']} "
                 f"& {r['rule']} & {r['cpsat']}{star} & {r['cp_sec']} "
                 f"& {milp} \\\\")
(ROOT / "tables" / "ch08_bench.tex").write_text("\n".join(lines) + "\n")
print("\n".join(lines))
