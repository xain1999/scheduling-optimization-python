"""Chapter 12 -- map of the field-service routes."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import matplotlib.pyplot as plt

import schedlib.gantt  # noqa: F401
from schedlib.results import load
from field_service import DEPOT, plan_routes, visits

OUT = Path(__file__).resolve().parents[2] / "figures"
jobs = visits()
where = {j["name"]: j["xy"] for j in jobs}
saved = load("ch12_routes")                # same routes as the console
if saved:
    routes, skipped = saved["routes"], saved["skipped"]
else:
    routes, skipped, _ = plan_routes(jobs)
styles = ["-", "--", ":", "-."]
fig, ax = plt.subplots(figsize=(4.0, 4.0))
for (tech, stops), ls in zip(routes.items(), styles):
    pts = [DEPOT] + [where[n] for n, _ in stops] + [DEPOT]
    ax.plot([p[0] for p in pts], [p[1] for p in pts], ls, color="black",
            lw=1.0, label=tech)
LO, HI = -9, 109                       # padding keeps labels inside
CW, CH = 1.9, 3.4                      # one label character, data units
points = [j["xy"] for j in jobs] + [DEPOT]
boxes = []                             # labels already placed


def free(box):
    x0, y0, x1, y1 = box
    if x0 < LO or x1 > HI or y0 < LO or y1 > HI:
        return False
    if any(x0 < b[2] and b[0] < x1 and y0 < b[3] and b[1] < y1
           for b in boxes):
        return False
    return not any(x0 - 1 < px < x1 + 1 and y0 - 1 < py < y1 + 1
                   for px, py in points)


for j in jobs:
    x, y = j["xy"]
    done = j["name"] not in skipped
    ax.plot(x, y, "o" if done else "x", ms=4 if done else 6,
            color="#555" if done else "black",
            mfc="white" if j["skill"] == "boiler" else "#555")
    w = CW * len(j["name"])
    for dx, dy in [(1.5, 1.5), (-1.5, 1.5), (1.5, -1.5), (-1.5, -1.5),
                   (3, 0), (-3, 0), (0, 3.5), (0, -3.5)]:
        x0 = x + dx if dx > 0 else (x + dx - w if dx < 0 else x - w / 2)
        y0 = y + dy if dy > 0 else (y + dy - CH if dy < 0 else y - CH / 2)
        if free((x0, y0, x0 + w, y0 + CH)):
            break                      # else keep the last candidate
    boxes.append((x0, y0, x0 + w, y0 + CH))
    ax.text(x0, y0, j["name"], fontsize=8, ha="left", va="bottom")
ax.plot(*DEPOT, "s", color="black", ms=7)
ax.legend(fontsize=8, frameon=False, loc="lower left",
          bbox_to_anchor=(0, 1.0), ncol=4)
ax.set_xlim(LO, HI); ax.set_ylim(LO, HI)
ax.set_aspect("equal")
ax.set_xticks([]); ax.set_yticks([])
fig.tight_layout()
fig.savefig(OUT / "ch12_routes.pdf", bbox_inches="tight")
print(routes, skipped)
