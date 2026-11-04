"""Regression tests for edge cases and failure modes discussed in the book.

Each test feeds an input that a careless implementation would get
wrong or answer misleadingly, and checks that the code either fails
loudly with a clear error or answers correctly.
Run:  python tests/test_regressions.py   (from the code/ folder)
"""
import subprocess
import sys
from pathlib import Path

CODE = Path(__file__).resolve().parents[1]
for sub in ("", "ch02", "ch04", "ch08", "ch09", "ch11", "ch12", "ch13",
            "ch17"):
    sys.path.insert(0, str(CODE / sub))

from schedlib.status import NoSolution  # noqa: E402


def expect(exc, fn):
    try:
        fn()
    except exc:
        return
    raise AssertionError(f"expected {exc.__name__}")


def test_infeasible_crew_raises():
    import cumulative_crew as cc
    old = dict(cc.TASKS)
    cc.TASKS["BIG"] = (1, cc.CREW + 1)      # needs more people than exist
    try:
        expect(NoSolution, cc.solve_crew)
    finally:
        cc.TASKS.clear()
        cc.TASKS.update(old)


def test_optional_visit_can_be_declined():
    import clinic
    req = dict(clinic.REQUESTS)
    req["Late"] = (30, 1010, 1010, 1010)    # would end after 17:00
    plan = clinic.book(req)
    assert "Late" not in plan and len(plan) == len(clinic.REQUESTS)


def test_parallel_sgs_zero_duration():
    from sgs import parallel_sgs
    from rcpsp import serial_sgs
    project = {"src": (0, {}, []), "A": (1, {"R": 1}, ["src"])}
    makespan, start = parallel_sgs(project, {"R": 1}, priority=str)
    assert makespan == 1 and start["A"] == 0
    assert serial_sgs(project, {"R": 1}, priority=str)[0] == 1


def test_zero_duration_sink_and_empty_projects():
    from sgs import parallel_sgs
    from rcpsp import serial_sgs
    project = {"source": (0, {}, []), "A": (1, {"R": 1}, ["source"]),
               "sink": (0, {}, ["A"])}
    for sgs in (parallel_sgs, serial_sgs):
        makespan, start = sgs(project, {"R": 1}, priority=str)
        assert makespan == 1 and start == {"source": 0, "A": 0, "sink": 1}
        assert sgs({"only": (0, {}, [])}, {}, str) == (0, {"only": 0})
        assert sgs({}, {}, str) == (0, {})


def test_bad_projects_rejected():
    from renovation import critical_path_method
    from rcpsp import serial_sgs
    from sgs import parallel_sgs
    cycle = {"A": (1, {}, ["B"]), "B": (1, {}, ["A"])}
    expect(ValueError, lambda: critical_path_method(cycle))
    expect(ValueError, lambda: serial_sgs(cycle, {}, str))
    expect(ValueError, lambda: parallel_sgs(cycle, {}, str))
    too_big = {"A": (1, {"R": 2}, [])}
    expect(ValueError, lambda: serial_sgs(too_big, {"R": 1}, str))
    expect(ValueError, lambda: parallel_sgs(too_big, {"R": 1}, str))


def test_exact_rcpsp_rejects_unknown_resource():
    from rcpsp import solve_rcpsp
    project = {"A": (2, {"missing": 1}, [])}       # misspelled resource
    expect(ValueError, lambda: solve_rcpsp(project, {}, time_limit=2))
    assert solve_rcpsp({}, {}, time_limit=2)["makespan"] == 0


def test_milestone_with_demand_does_not_wait():
    from rcpsp import serial_sgs, solve_rcpsp
    from sgs import parallel_sgs
    project = {"A": (3, {"R": 1}, []), "Z": (0, {"R": 1}, []),
               "B": (3, {"S": 1}, ["Z"])}
    capacity = {"R": 1, "S": 1}
    for sgs in (serial_sgs, parallel_sgs):
        assert sgs(project, capacity, str) == (3, {"A": 0, "Z": 0,
                                                    "B": 0})
    assert solve_rcpsp(project, capacity, time_limit=5,
                       workers=1)["makespan"] == 3


def test_overdue_jobs_and_input_checks():
    from cpsat_model import solve_cpsat
    from milp_disjunctive import solve_disjunctive
    from schedlib import Job, Task, validate_single_machine
    overdue = [Job("A", p=2, d=-10)]                # tardiness 12
    assert round(solve_cpsat(overdue, time_limit=5).objective) == 12
    assert round(solve_disjunctive(overdue, time_limit=5).objective) == 12
    expect(ValueError, lambda: validate_single_machine(
        [Job("A", p=-2)], [Task("A", "M1", 0, -2)]))
    expect(ValueError, lambda: solve_cpsat([Job("A", p=1.5)]))


def test_critical_path_rejects_bad_orders():
    from jobshop import critical_path
    expect(ValueError, lambda: critical_path([[(0, 2)], [(0, 2)]], {}))
    jobs = [[(0, 1), (1, 1)], [(1, 1), (0, 1)]]
    cycle = {0: [(1, 1), (0, 0)], 1: [(0, 1), (1, 0)]}
    expect(ValueError, lambda: critical_path(jobs, cycle))


def test_exam_objective_counts_pairs():
    from exams import back_to_back_count, timetable
    # one student takes A, B, C: two back-to-back pairs, one student
    edges = {("A", "B"): 1, ("A", "C"): 1, ("B", "C"): 1}
    period, cost, _ = timetable(["A", "B", "C"], None, edges, 3,
                                time_limit=5)
    assert cost == back_to_back_count(period, edges) == 2


def test_validator_survives_python_O():
    code = ("from schedlib import Job, Task, validate_single_machine, "
            "InvalidSchedule\n"
            "try:\n"
            "    validate_single_machine([Job('A', p=3)], "
            "[Task('A', 'M1', 0, 1)])\n"
            "    print('MISSED')\n"
            "except InvalidSchedule:\n"
            "    print('CAUGHT')\n")
    out = subprocess.run([sys.executable, "-O", "-c", code], cwd=CODE,
                         capture_output=True, text=True, check=True)
    assert out.stdout.strip() == "CAUGHT", out.stdout


if __name__ == "__main__":
    tests = [v for k, v in dict(globals()).items() if k.startswith("test_")]
    for t in tests:
        t()
        print("passed:", t.__name__)
