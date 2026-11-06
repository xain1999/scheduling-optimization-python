"""Chapter 12: appointments with time windows and a lunch break."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from ortools.sat.python import cp_model

from schedlib.status import check_cpsat


# [start:data]
# patient: (minutes needed, earliest, latest start, preferred start)
REQUESTS = {
    "Ali":    (30, 540, 600, 540), "Beth":  (20, 540, 720, 600),
    "Carl":   (45, 600, 660, 600), "Dina":  (15, 540, 960, 840),
    "Emre":   (30, 780, 900, 780), "Fay":   (60, 720, 960, 840),
    "Gus":    (20, 540, 600, 570), "Hana":  (30, 840, 990, 900),
    "Ivo":    (15, 600, 780, 690), "Jade":  (45, 540, 960, 600),
}
LUNCH = (750, 810)                    # 12:30-13:30, doctor unavailable
DAY_END = 1020                         # 17:00
# [end:data]


# [start:model]
def book(requests, lunch=LUNCH):
    m = cp_model.CpModel()
    start, ivs, booked, devs = {}, [], {}, []
    for p, (dur, lo, hi, pref) in requests.items():
        booked[p] = m.new_bool_var(f"book_{p}")
        start[p] = m.new_int_var(lo, hi, f"s_{p}")
        ivs.append(m.new_optional_interval_var(
            start[p], dur, start[p] + dur, booked[p], p))
        # every rule about the visit holds only if it is booked
        m.add(start[p] + dur <= DAY_END).only_enforce_if(booked[p])
        ub = max(abs(lo - pref), abs(hi - pref))
        dev = m.new_int_var(0, ub, f"dev_{p}")  # minutes off preferred
        m.add(dev >= start[p] - pref).only_enforce_if(booked[p])
        m.add(dev >= pref - start[p]).only_enforce_if(booked[p])
        devs.append((dev, ub))
    ivs.append(m.new_fixed_size_interval_var(
        lunch[0], lunch[1] - lunch[0], "lunch"))
    m.add_no_overlap(ivs)
    # turning one patient away costs more than all deviations together,
    # so the model first books as many patients as possible
    reject = 1 + sum(ub for _, ub in devs)
    m.minimize(sum(d for d, _ in devs)
               + reject * sum(b.Not() for b in booked.values()))
    solver = cp_model.CpSolver()
    solver.parameters.max_time_in_seconds = 10
    check_cpsat(solver, solver.solve(m))
    return {p: solver.value(start[p]) for p in requests
            if solver.value(booked[p])}
# [end:model]


if __name__ == "__main__":
    # [start:run]
    plan = book(REQUESTS)
    for p, s in sorted(plan.items(), key=lambda kv: kv[1]):
        dur, _, _, pref = REQUESTS[p]
        print(f"{p:5} {s // 60:02d}:{s % 60:02d}-"
              f"{(s + dur) // 60:02d}:{(s + dur) % 60:02d}"
              f"   ({s - pref:+d} min from preferred)")
    print("not booked:", [p for p in REQUESTS if p not in plan] or "none")
    # [end:run]
