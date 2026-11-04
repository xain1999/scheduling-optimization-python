"""Chapter 1 -- the Inkwell print shop instance."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from schedlib import Job

# [start:instance]
# Eight print jobs waiting at 8:00. Times are in hours of press time;
# due dates are hours from now; weight = how much the customer matters.
JOBS = [
    Job("J1", p=4, d=10, w=3),
    Job("J2", p=7, d=17, w=1),
    Job("J3", p=2, d=8,  w=3),
    Job("J4", p=9, d=29, w=2),
    Job("J5", p=3, d=15, w=1),
    Job("J6", p=6, d=21, w=2),
    Job("J7", p=5, d=8,  w=1),
    Job("J8", p=8, d=33, w=1),
]
# [end:instance]
