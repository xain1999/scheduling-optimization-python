"""Chapter 11 -- exam timetabling as graph colouring."""
import random
from itertools import combinations

from ortools.sat.python import cp_model


# [start:data]
def enrolments(n_students=600, seed=3):
    """Students belong to one of six programmes. Each takes 3-4 of the
    eight core exams of their programme and 1-2 of 12 shared electives,
    so the conflict graph has structure, as in a real university."""
    rng = random.Random(seed)
    programmes = {f"P{k+1}": [f"P{k+1}-{i+1}" for i in range(8)]
                  for k in range(6)}
    electives = [f"EL{i+1}" for i in range(12)]
    core_exams = [e for core in programmes.values() for e in core]
    exams = core_exams + electives
    students = {}
    for s in range(n_students):
        core = programmes[rng.choice(list(programmes))]
        taken = rng.sample(core, rng.randint(3, 4)) + \
            rng.sample(electives, rng.randint(1, 2))
        students[f"S{s+1}"] = sorted(taken)
    return exams, students


def conflict_graph(exams, students):
    """Edge (a, b) with weight = number of students taking both."""
    w = {}
    for taken in students.values():
        for a, b in combinations(sorted(taken), 2):
            w[a, b] = w.get((a, b), 0) + 1
    return w
# [end:data]


# [start:dsatur]
def dsatur(exams, edges):
    """Greedy colouring (Brelaz 1979): repeatedly colour the exam with
    the most differently-coloured neighbours, using the lowest period
    that causes no clash."""
    nbrs = {e: set() for e in exams}
    for a, b in edges:
        nbrs[a].add(b)
        nbrs[b].add(a)
    period = {}
    while len(period) < len(exams):
        def saturation(e):
            return (len({period[x] for x in nbrs[e] if x in period}),
                    len(nbrs[e]))
        e = max((e for e in exams if e not in period), key=saturation)
        used = {period[x] for x in nbrs[e] if x in period}
        period[e] = next(p for p in range(len(exams)) if p not in used)
    return period
# [end:dsatur]


# [start:clique]
def greedy_clique(exams, edges):
    """A large clique: exams that pairwise share a student.  Its size
    is a lower bound on the number of periods (all need different
    periods)."""
    nbrs = {e: set() for e in exams}
    for a, b in edges:
        nbrs[a].add(b)
        nbrs[b].add(a)
    best = []
    for start in exams:
        clique = [start]
        for e in sorted(nbrs[start], key=lambda x: -len(nbrs[x])):
            if all(e in nbrs[c] for c in clique):
                clique.append(e)
        best = max(best, clique, key=len)
    return best
# [end:clique]


# [start:cpsat]
def timetable(exams, students, edges, n_periods, time_limit=30):
    """Assign exams to periods without clashes, then minimise the
    back-to-back cases: pairs of exams in consecutive periods, each
    weighted by the number of students who take both.  A student with
    three exams in a row counts twice."""
    m = cp_model.CpModel()
    x = {(e, p): m.new_bool_var(f"{e}@{p}")
         for e in exams for p in range(n_periods)}
    for e in exams:
        m.add_exactly_one(x[e, p] for p in range(n_periods))
    for (a, b) in edges:                         # no student clash
        for p in range(n_periods):
            m.add_at_most_one([x[a, p], x[b, p]])
    back_to_back = []
    for (a, b), w in edges.items():              # consecutive periods
        for p in range(n_periods - 1):
            for e1, e2 in ((a, b), (b, a)):
                both = m.new_bool_var("")
                m.add_bool_and([x[e1, p], x[e2, p + 1]]) \
                    .only_enforce_if(both)
                m.add_bool_or([x[e1, p].Not(), x[e2, p + 1].Not(),
                               both])
                back_to_back.append(w * both)
    m.minimize(sum(back_to_back))
    solver = cp_model.CpSolver()
    solver.parameters.max_time_in_seconds = time_limit
    solver.parameters.num_workers = 8
    status = solver.solve(m)
    if status not in (cp_model.OPTIMAL, cp_model.FEASIBLE):
        return None, None, solver.status_name(status)
    period = {e: p for (e, p), v in x.items() if solver.value(v)}
    status = solver.status_name(status)
    return period, int(solver.objective_value), status
# [end:cpsat]


def back_to_back_count(period, edges):
    return sum(w for (a, b), w in edges.items()
               if abs(period[a] - period[b]) == 1)


if __name__ == "__main__":
    # [start:run]
    exams, students = enrolments()
    edges = conflict_graph(exams, students)
    print(f"{len(exams)} exams, {len(students)} students, "
          f"{len(edges)} conflicting pairs")
    greedy = dsatur(exams, edges)
    k = max(greedy.values()) + 1
    print(f"largest clique found: {len(greedy_clique(exams, edges))} "
          f"exams -> at least that many periods")
    print(f"DSatur: {k} periods, back-to-back cases: "
          f"{back_to_back_count(greedy, edges)}")
    for periods in (k, k + 2, k + 4):
        period, cost, status = timetable(exams, students, edges,
                                         periods)
        print(f"CP-SAT with {periods} periods: {status}"
              + (f", back-to-back cases: {cost}" if period else ""))
    # [end:run]
