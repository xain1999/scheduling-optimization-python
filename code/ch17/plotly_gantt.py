"""Chapter 17 -- an interactive Gantt chart with Plotly."""
import sys
from datetime import datetime, timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "ch06"))

import plotly.express as px

from gpu_cluster import greedy, training_jobs

# [start:plotly]
def gantt_html(plan, path, day_start=datetime(2026, 11, 2, 8, 0)):
    rows = [dict(job=t.job, resource=t.resource,
                 start=day_start + timedelta(hours=t.start),
                 end=day_start + timedelta(hours=t.end)) for t in plan]
    fig = px.timeline(rows, x_start="start", x_end="end", y="resource",
                      color="job", text="job", hover_data=["job"])
    fig.update_yaxes(categoryorder="category descending")
    fig.update_layout(showlegend=False, height=350,
                      title="GPU cluster plan (hover for details)")
    fig.write_html(path, include_plotlyjs="cdn")
# [end:plotly]


if __name__ == "__main__":
    out = Path(__file__).resolve().parents[2] / "results" / "gpu_plan.html"
    gantt_html(greedy(training_jobs()), out)
    print("wrote", out)
