"""Chapter 9: a house renovation project: data and the critical path."""

# [start:data]
# activity: (duration in days, {crew: people}, [predecessors])
PROJECT = {
    "survey":      (2, {"carp": 1},            []),
    "demolition":  (4, {"carp": 2},            ["survey"]),
    "plumb_rough": (5, {"plumb": 1},           ["demolition"]),
    "elec_rough":  (6, {"elec": 2},            ["demolition"]),
    "framing":     (5, {"carp": 3},            ["demolition"]),
    "windows":     (3, {"carp": 2},            ["framing"]),
    "insulation":  (3, {"carp": 1},            ["plumb_rough",
                                                "elec_rough",
                                                "framing"]),
    "drywall":     (6, {"carp": 2},            ["insulation"]),
    "kitchen":     (7, {"carp": 2, "plumb": 1}, ["drywall"]),
    "bathroom":    (6, {"plumb": 1, "elec": 1}, ["drywall"]),
    "elec_finish": (3, {"elec": 2},            ["drywall"]),
    "painting":    (5, {"carp": 2},            ["kitchen", "bathroom",
                                                "elec_finish",
                                                "windows"]),
    "flooring":    (4, {"carp": 2},            ["painting"]),
    "cleanup":     (1, {"carp": 1},            ["flooring"]),
}
CREWS = {"carp": 3, "plumb": 1, "elec": 2}       # people available
# [end:data]


# [start:cpm]
def critical_path_method(project):
    """Forward pass: earliest start (ES).  Backward pass: latest start
    (LS) without delaying the project.  Slack = LS - ES."""
    order, seen, active = [], set(), set()

    def visit(a):                       # topological order (DFS)
        if a in seen:
            return
        if a in active:
            raise ValueError(f"precedence cycle through {a}")
        active.add(a)
        for p in project[a][2]:
            if p not in project:
                raise ValueError(f"{a}: unknown predecessor {p}")
            visit(p)
        active.discard(a)
        seen.add(a)
        order.append(a)
    for a in project:
        visit(a)

    es = {}
    for a in order:
        es[a] = max((es[p] + project[p][0] for p in project[a][2]),
                    default=0)
    length = max(es[a] + project[a][0] for a in project)
    succ = {a: [b for b in project if a in project[b][2]]
            for a in project}
    ls = {}
    for a in reversed(order):
        lf = min((ls[s] for s in succ[a]), default=length)
        ls[a] = lf - project[a][0]
    return length, {a: (es[a], ls[a], ls[a] - es[a]) for a in order}
# [end:cpm]


if __name__ == "__main__":
    # [start:run]
    length, table = critical_path_method(PROJECT)
    print(f"project length ignoring crews: {length} days")
    print(f"{'activity':12} {'ES':>3} {'LS':>3} {'slack':>5}")
    for a, (es, ls, slack) in table.items():
        mark = "  <- critical" if slack == 0 else ""
        print(f"{a:12} {es:3} {ls:3} {slack:5}{mark}")
    # [end:run]
