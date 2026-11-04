"""Chapter 17 -- testing the engine: examples, properties, the API."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "ch02"))

from fastapi.testclient import TestClient
from hypothesis import given, settings, strategies as st

from cpsat_model import solve_cpsat
from schedlib import Job, evaluate, sequence_to_schedule, \
    validate_single_machine
from service import app

client = TestClient(app)


# [start:example]
def test_busy_day_regression():
    """A known instance with a known optimum guards regressions."""
    from instances import JOBS
    res = solve_cpsat(JOBS, time_limit=10)
    assert res.optimal and round(res.objective) == 44
# [end:example]


# [start:property]
jobs_strategy = st.lists(
    st.tuples(st.integers(1, 9), st.integers(0, 20),
              st.integers(0, 40), st.integers(0, 3)),
    min_size=1, max_size=8)


@settings(max_examples=40, deadline=None)
@given(jobs_strategy)
def test_solver_properties(raw):
    jobs = [Job(f"J{i}", p=p, r=r, d=d, w=w)
            for i, (p, r, d, w) in enumerate(raw)]
    res = solve_cpsat(jobs, time_limit=5, workers=1)
    validate_single_machine(jobs, res.schedule)    # 1. always feasible
    value = evaluate(jobs, res.schedule)["sumwT"]
    assert res.bound <= value + 1e-6              # 2. bound is a bound
    edd = sorted(jobs, key=lambda j: (j.d, j.r))
    baseline = evaluate(jobs, sequence_to_schedule(
        jobs, [j.id for j in edd]))["sumwT"]
    if res.optimal:                                  # 3. beats a rule
        assert value <= baseline
# [end:property]


# [start:api]
def test_api_round_trip():
    payload = {"jobs": [{"id": "A", "p": 3, "d": 4, "w": 2},
                        {"id": "B", "p": 2, "d": 2},
                        {"id": "C", "p": 4, "r": 1, "d": 10}],
               "time_limit": 5}
    resp = client.post("/schedule", json=payload)
    assert resp.status_code == 200
    body = resp.json()
    assert {t["job"] for t in body["tasks"]} == {"A", "B", "C"}
    assert body["proven_optimal"]


def test_api_rejects_bad_input():
    bad = {"jobs": [{"id": "A", "p": 0, "d": 4}]}   # zero duration
    assert client.post("/schedule", json=bad).status_code == 422
    dup = {"jobs": [{"id": "A", "p": 1, "d": 4},
                    {"id": "A", "p": 2, "d": 5}]}
    assert client.post("/schedule", json=dup).status_code == 422
    huge = {"jobs": [{"id": "A", "p": 1, "r": 10**30, "d": 4}]}
    assert client.post("/schedule", json=huge).status_code == 422
# [end:api]


if __name__ == "__main__":
    for test in [test_busy_day_regression, test_solver_properties,
                 test_api_round_trip, test_api_rejects_bad_input]:
        test()
        print("passed:", test.__name__)
