"""Chapter 10 -- nurse rostering with CP-SAT."""
import random
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from ortools.sat.python import cp_model

from schedlib.status import check_cpsat


# [start:data]
SHIFTS = ["D", "E", "N"]                 # day, evening, night
DAYS = 28                                # four weeks, day 0 = Monday
NURSES = {                             # name: (senior?, target shifts)
    "Ana": (True, 20), "Ben": (True, 20), "Chloe": (True, 20),
    "Dev": (True, 20), "Eva": (False, 20), "Farid": (False, 20),
    "Grace": (False, 20), "Hugo": (True, 16), "Iris": (False, 16),
    "Jon": (False, 12), "Kemi": (False, 12), "Leo": (False, 12),
}


def demand(day: int, shift: str) -> int:
    weekend = day % 7 >= 5
    return {"D": 3, "E": 2, "N": 2}[shift] - (1 if weekend and
                                              shift == "D" else 0)


def day_off_requests(seed=2):
    """Each nurse asks for a few specific days off."""
    rng = random.Random(seed)
    return {n: rng.sample(range(DAYS), 3) for n in NURSES}
# [end:data]


# [start:variables]
def build(requests, max_nights_in_row=3, max_days_in_row=6,
          night_cover=2, assumptions=False, soft=True):
    m = cp_model.CpModel()
    work = {(n, d, s): m.new_bool_var(f"{n}_{d}_{s}")
            for n in NURSES for d in range(DAYS) for s in SHIFTS}
    groups = {}                          # name -> enforcement literal

    def group(name):
        """Constraints of a group hold only if its literal is true,
        so the solver can tell us which groups conflict."""
        if not assumptions:
            return []
        if name not in groups:
            groups[name] = m.new_bool_var(name)
        return [groups[name]]
# [end:variables]

    # [start:hard]
    for n in NURSES:
        for d in range(DAYS):            # at most one shift per day
            m.add_at_most_one(work[n, d, s] for s in SHIFTS)

    for d in range(DAYS):                # coverage, with a senior
        for s in SHIFTS:
            need = night_cover if s == "N" else demand(d, s)
            m.add(sum(work[n, d, s] for n in NURSES) >= need) \
                .only_enforce_if(group("coverage"))
            m.add(sum(work[n, d, s] for n in NURSES
                      if NURSES[n][0]) >= 1) \
                .only_enforce_if(group("senior on every shift"))

    for n in NURSES:
        for d in range(DAYS - 1):        # 11 hours rest: no N->D,
            for a, b in [("N", "D"), ("N", "E"), ("E", "D")]:
                m.add_bool_or([work[n, d, a].Not(),
                               work[n, d + 1, b].Not()]) \
                    .only_enforce_if(group("rest between shifts"))
        k = max_nights_in_row + 1        # sliding windows
        for d in range(DAYS - k + 1):
            m.add(sum(work[n, d + i, "N"] for i in range(k))
                  <= max_nights_in_row) \
                .only_enforce_if(group("max nights in a row"))
        k = max_days_in_row + 1
        for d in range(DAYS - k + 1):
            m.add(sum(work[n, d + i, s] for i in range(k)
                      for s in SHIFTS) <= max_days_in_row) \
                .only_enforce_if(group("max days in a row"))
        total = sum(work[n, d, s] for d in range(DAYS) for s in SHIFTS)
        target = NURSES[n][1]            # contract: target +-1 shifts
        m.add(total >= target - 1).only_enforce_if(group("contracts"))
        m.add(total <= target + 1).only_enforce_if(group("contracts"))
    # [end:hard]

    # [start:soft]
    if not soft:                         # hard rules only (to explain)
        return m, work, groups
    penalties = []
    for n, days in requests.items():     # honour day-off requests
        for d in days:
            for s in SHIFTS:
                penalties.append(10 * work[n, d, s])

    nights = {}                          # share nights fairly
    for n in NURSES:
        nights[n] = m.new_int_var(0, DAYS, f"nights_{n}")
        m.add(nights[n] == sum(work[n, d, "N"] for d in range(DAYS)))
    max_nights = m.new_int_var(0, DAYS, "max_nights")
    m.add_max_equality(max_nights, list(nights.values()))
    penalties.append(5 * max_nights)

    for n in NURSES:                     # avoid split weekends
        for w in range(DAYS // 7):
            sat, sun = 7 * w + 5, 7 * w + 6
            on_sat = sum(work[n, sat, s] for s in SHIFTS)
            on_sun = sum(work[n, sun, s] for s in SHIFTS)
            split = m.new_bool_var(f"split_{n}_{w}")
            m.add(on_sat - on_sun <= split)
            m.add(on_sun - on_sat <= split)
            penalties.append(3 * split)
    m.minimize(sum(penalties))
    return m, work, groups
    # [end:soft]


# [start:solve]
def solve(requests, time_limit=60, **kw):
    m, work, _ = build(requests, **kw)
    solver = cp_model.CpSolver()
    solver.parameters.max_time_in_seconds = time_limit
    solver.parameters.num_workers = 8
    status = check_cpsat(solver, solver.solve(m))
    roster = {n: "".join(next((s for s in SHIFTS
                               if solver.value(work[n, d, s])), ".")
                         for d in range(DAYS)) for n in NURSES}
    return roster, solver.objective_value, status
# [end:solve]


# [start:explain]
def explain_infeasibility(requests, **kw):
    """Which groups of rules cannot all hold together?

    Returns (status, conflict).  The conflict is a list of group
    names, only after a proven INFEASIBLE; FEASIBLE/OPTIMAL means the
    rules are compatible, and UNKNOWN (time limit) or MODEL_INVALID
    mean that nothing is known -- never read them as "no conflict".
    """
    m, _, groups = build(requests, assumptions=True, soft=False, **kw)
    m.add_assumptions(list(groups.values()))
    solver = cp_model.CpSolver()
    solver.parameters.num_workers = 1    # needed for core extraction
    solver.parameters.max_time_in_seconds = 120
    solver.parameters.linearization_level = 2   # stronger LP
    status = solver.solve(m)
    if status != cp_model.INFEASIBLE:
        return solver.status_name(status), None
    core = solver.sufficient_assumptions_for_infeasibility()
    names = {lit.index: name for name, lit in groups.items()}
    return "INFEASIBLE", [names[i] for i in core]
# [end:explain]


if __name__ == "__main__":
    # [start:run]
    req = day_off_requests()
    roster, cost, status = solve(req)
    print(f"{status}, penalty {cost:.0f}")
    print(" " * 6 + "".join("MTWTFSS" for _ in range(4)))
    for n, row in roster.items():
        print(f"{n:6}{row}  nights={row.count('N'):2} "
              f"shifts={len(row) - row.count('.'):2}")
    broken = [(n, d) for n, ds in req.items() for d in ds
              if roster[n][d] != "."]
    print("day-off requests not granted:", broken)
    # [end:run]
