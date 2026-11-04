"""Chapter 11 -- a school timetable, and repairing it after a change."""
from ortools.sat.python import cp_model

# [start:data]
DAYS, PERIODS = 5, 6
CLASSES = ["7A", "7B", "8A", "8B"]
CURRICULUM = {                 # subject: (lessons per week, room type)
    "math": (5, "std"), "english": (4, "std"), "science": (4, "lab"),
    "history": (3, "std"), "art": (2, "art"), "sport": (3, "gym"),
    "music": (2, "std"), "french": (3, "std"),
}                              # 26 lessons per class per week
TEACHER = {                    # (class, subject) -> teacher
    **{(c, "math"): ("Ms Ade" if c[0] == "7" else "Mr Brook")
       for c in CLASSES},
    **{(c, "english"): ("Ms Cruz" if c[1] == "A" else "Mr Dahl")
       for c in CLASSES},
    **{(c, "science"): "Dr Erin" for c in CLASSES},
    **{(c, "history"): "Mr Faye" for c in CLASSES},
    **{(c, "art"): "Ms Gil" for c in CLASSES},
    **{(c, "sport"): "Mr Hale" for c in CLASSES},
    **{(c, "music"): "Ms Iqbal" for c in CLASSES},
    **{(c, "french"): ("Ms Jouve" if c[0] == "7" else "Ms Iqbal")
       for c in CLASSES},
}
ROOMS = {"std": 3, "lab": 1, "art": 1, "gym": 1}   # rooms of each type
UNAVAILABLE = {"Dr Erin": [(4, p) for p in range(PERIODS)],   # Friday
               "Mr Hale": [(0, 0), (0, 1)]}                 # Mon early
# [end:data]


# [start:model]
def build(fixed=None, previous=None):
    m = cp_model.CpModel()
    x = {(c, s, d, p): m.new_bool_var(f"{c}_{s}_{d}_{p}")
         for c in CLASSES for s in CURRICULUM
         for d in range(DAYS) for p in range(PERIODS)}
    slots = [(d, p) for d in range(DAYS) for p in range(PERIODS)]
    for c in CLASSES:
        for s, (n, _) in CURRICULUM.items():   # weekly hours
            m.add(sum(x[c, s, d, p] for d, p in slots) == n)
            for d in range(DAYS):              # at most 2 per day,
                day = [x[c, s, d, p] for p in range(PERIODS)]
                m.add(sum(day) <= 2)
                for p in range(PERIODS - 1):   # and if 2, back to back
                    for q in range(p + 2, PERIODS):
                        m.add_bool_or([x[c, s, d, p].Not(),
                                       x[c, s, d, q].Not()])
        for d, p in slots:                     # one lesson at a time
            m.add_at_most_one(x[c, s, d, p] for s in CURRICULUM)
    teachers = set(TEACHER.values())
    for t in teachers:
        mine = [k for k, v in TEACHER.items() if v == t]
        for d, p in slots:
            lessons = [x[c, s, d, p] for c, s in mine]
            if (d, p) in UNAVAILABLE.get(t, []):
                m.add(sum(lessons) == 0)
            else:
                m.add_at_most_one(lessons)
    for rtype, count in ROOMS.items():         # enough rooms
        subj = [s for s, (_, r) in CURRICULUM.items() if r == rtype]
        for d, p in slots:
            m.add(sum(x[c, s, d, p] for c in CLASSES for s in subj)
                  <= count)

    cost = []                                  # soft: compact days
    for c in CLASSES:
        for d in range(DAYS):
            busy = [m.new_bool_var("") for _ in range(PERIODS)]
            for p in range(PERIODS):
                m.add(busy[p] == sum(x[c, s, d, p]
                                     for s in CURRICULUM))
            cost.append(2 * busy[PERIODS - 1])  # avoid the last period
            for p in range(PERIODS - 1):       # a free period followed
                hole = m.new_bool_var("")      # by a lesson: a gap or
                m.add(hole >= busy[p + 1] - busy[p])   # a late start
                cost.append(5 * hole)
    if fixed:                                  # pinned lessons
        for key in fixed:
            m.add(x[key] == 1)
    if previous:                               # stay close to old plan
        cost.append(sum(20 * x[k].Not() for k in previous))
    m.minimize(sum(cost))
    return m, x
# [end:model]


def solve(time_limit=30, **kw):
    m, x = build(**kw)
    solver = cp_model.CpSolver()
    solver.parameters.max_time_in_seconds = time_limit
    solver.parameters.num_workers = 8
    status = solver.solve(m)
    if status not in (cp_model.OPTIMAL, cp_model.FEASIBLE):
        return None, solver.status_name(status)
    plan = {k for k, v in x.items() if solver.value(v)}
    return plan, solver.status_name(status)


def show(plan, cls):
    names = {s: s[:4] for s in CURRICULUM}
    rows = []
    for p in range(PERIODS):
        cells = []
        for d in range(DAYS):
            s = next((s for (c, s, dd, pp) in plan
                      if c == cls and dd == d and pp == p), None)
            cells.append(f"{names[s] if s else '-':6}")
        rows.append(f"  P{p + 1}  " + "".join(cells))
    return "\n".join(rows)


if __name__ == "__main__":
    # [start:run]
    plan, status = solve()
    print(status)
    print("        Mon   Tue   Wed   Thu   Fri")
    print(show(plan, "7A"))
    # Ms Ade is ill on Wednesday: repair with few changes
    UNAVAILABLE["Ms Ade"] = [(2, p) for p in range(PERIODS)]
    new, status = solve(previous=plan)
    moved = len(plan - new)
    print(f"repair: {status}, {moved} of {len(plan)} lessons moved")
    # [end:run]
