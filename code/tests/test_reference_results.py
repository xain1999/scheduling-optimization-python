"""Independent validation of the stored solutions shown in the book.

The case-study scripts check the solver status; these tests check the
solutions themselves against the rules of each problem, with code that
does not share anything with the models (only the input data).
Run:  python tests/test_reference_results.py   (from the code/ folder)
"""
import json
import sys
from pathlib import Path

CODE = Path(__file__).resolve().parents[1]
RESULTS = CODE.parent / "results"
for sub in ("", "ch02", "ch04", "ch06", "ch08", "ch12"):
    sys.path.insert(0, str(CODE / sub))

from schedlib import evaluate, sequence_to_schedule  # noqa: E402
from schedlib import validate_single_machine  # noqa: E402
from schedlib.results import load  # noqa: E402


def no_overlap(intervals):
    """intervals: list of (start, end); True if none overlap."""
    s = sorted(intervals)
    return all(a[1] <= b[0] for a, b in zip(s, s[1:]))


def test_ch02_single_machine():
    from instances import JOBS
    sched = sequence_to_schedule(JOBS, load("ch02_single"))
    validate_single_machine(JOBS, sched)
    assert evaluate(JOBS, sched)["sumwT"] == 44


def test_ch02_two_machines():
    from instances import random_instance
    jobs = random_instance(12, seed=7, spread=0.3, slack=0.2)
    plan = load("ch02_parallel")
    by_id = {j.id: j for j in jobs}
    assert sorted(t.job for t in plan) == sorted(by_id)
    for t in plan:
        assert t.end - t.start == by_id[t.job].p
        assert t.start >= by_id[t.job].r
    for m in {t.resource for t in plan}:
        assert no_overlap([(t.start, t.end) for t in plan
                           if t.resource == m])
    assert sum(j.w * max(0, {t.job: t.end for t in plan}[j.id] - j.d)
               for j in jobs) == 40


def test_ch04_crew():
    from cumulative_crew import CREW, PRECEDENCES, TASKS
    saved = load("ch04_crew")
    plan = {t: tuple(v) for t, v in saved["plan"].items()}
    assert set(plan) == set(TASKS)
    for t, (s, e) in plan.items():
        assert e - s == TASKS[t][0] and s >= 0
    for a, b in PRECEDENCES:
        assert plan[b][0] >= plan[a][1]
    for u in range(saved["makespan"]):
        assert sum(TASKS[t][1] for t, (s, e) in plan.items()
                   if s <= u < e) <= CREW
    assert max(e for _, e in plan.values()) == saved["makespan"] == 15


def test_ch04_berths():
    from berth_2d import QUAY, ships
    fleet = ships()
    plan = load("ch04_berths")
    rects = []
    for s in fleet:
        t, x = plan[s["name"]]
        assert t >= s["arrival"] and 0 <= x and x + s["length"] <= QUAY
        rects.append((t, t + s["hours"], x, x + s["length"]))
    for i, a in enumerate(rects):
        for b in rects[i + 1:]:
            apart = (a[1] <= b[0] or b[1] <= a[0] or a[3] <= b[2]
                     or b[3] <= a[2])
            assert apart, (a, b)
    assert sum(s["weight"] * (plan[s["name"]][0] - s["arrival"])
               for s in fleet) == 78


def test_ch06_gpu_plans():
    from gpu_cluster import GPUS, duration, training_jobs
    jobs = training_jobs()
    saved = load("ch06_gpu")
    for name, value in (("greedy", 365), ("cpsat", 237)):
        plan = saved[name]
        by_job = {t.job: t for t in plan}
        assert sorted(by_job) == sorted(j["name"] for j in jobs)
        for j in jobs:
            t = by_job[j["name"]]
            assert t.resource in GPUS
            d = duration(j, t.resource)
            assert d is not None, "job does not fit in this GPU's memory"
            assert t.end - t.start == d and t.start >= j["release"]
        for g in GPUS:
            assert no_overlap([(t.start, t.end) for t in plan
                               if t.resource == g])
        flow = sum(j["weight"] * (by_job[j["name"]].end - j["release"])
                   for j in jobs)
        assert flow == value, (name, flow)


def test_ch12_routes():
    from field_service import DEPOT, SHIFT, TECHS, minutes, visits
    jobs = {j["name"]: j for j in visits()}
    saved = load("ch12_routes")
    served = [n for stops in saved["routes"].values() for n, _ in stops]
    assert len(served) == len(set(served)) == 25
    assert sorted(saved["skipped"]) == sorted(set(jobs) - set(served))
    for tech, stops in saved["routes"].items():
        t, here = SHIFT[0], DEPOT
        for name, start in stops:
            job = jobs[name]
            assert job["skill"] in TECHS[tech]
            arrival = t + minutes(here, job["xy"])
            lo, hi = job["window"]
            assert arrival <= start and lo <= start <= hi
            t, here = start + job["service"], job["xy"]
        assert t + minutes(here, DEPOT) <= SHIFT[1]   # home by 17:00


def test_ch16_base_plan():
    from jobshop import read_instance
    jobs = read_instance("ft10")
    plan = {tuple(map(int, k.split(","))): v for k, v in json.loads(
        (RESULTS / "ch16_base_plan.json").read_text()).items()}
    for j, ops in enumerate(jobs):
        for k in range(1, len(ops)):
            assert plan[j, k] >= plan[j, k - 1] + ops[k - 1][1]
    machines = {m for ops in jobs for m, _ in ops}
    for m in machines:
        assert no_overlap([(plan[j, k], plan[j, k] + d)
                           for j, ops in enumerate(jobs)
                           for k, (mc, d) in enumerate(ops) if mc == m])
    assert max(plan[j, len(o) - 1] + o[-1][1]
               for j, o in enumerate(jobs)) == 930


if __name__ == "__main__":
    tests = [v for k, v in dict(globals()).items() if k.startswith("test_")]
    for test in tests:
        test()
        print("passed:", test.__name__)
