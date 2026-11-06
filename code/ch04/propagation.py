"""Chapter 4: constraint propagation by hand on a precedence network."""

# [start:propagate]
def propagate(tasks, precedences, release, deadline):
    """Shrink [earliest start, latest start] windows until stable.

    tasks:       {name: duration}
    precedences: list of (a, b) meaning b cannot start before a ends
    release:     earliest start of every task
    deadline:    every task must end by this time
    """
    est = {t: release for t in tasks}                 # earliest start
    lst = {t: deadline - d for t, d in tasks.items()}  # latest start
    changed, rounds = True, 0
    while changed:
        changed, rounds = False, rounds + 1
        for a, b in precedences:
            if est[a] + tasks[a] > est[b]:       # push b to the right
                est[b] = est[a] + tasks[a]
                changed = True
            if lst[b] - tasks[a] < lst[a]:       # pull a to the left
                lst[a] = lst[b] - tasks[a]
                changed = True
        for t in tasks:
            if est[t] > lst[t]:
                return None, rounds          # empty domain: infeasible
    return {t: (est[t], lst[t]) for t in tasks}, rounds
# [end:propagate]


if __name__ == "__main__":
    # [start:run]
    tasks = {"design": 3, "proof": 2, "plates": 2, "print": 4,
             "fold": 2, "bind": 3, "ship": 1}
    prec = [("design", "proof"), ("proof", "plates"),
            ("plates", "print"), ("print", "fold"), ("print", "bind"),
            ("fold", "ship"), ("bind", "ship")]
    for deadline in (20, 15, 14):
        windows, rounds = propagate(tasks, prec, 0, deadline)
        word = "round" if rounds == 1 else "rounds"
        print(f"deadline {deadline} ({rounds} {word}):")
        if windows is None:
            print("   INFEASIBLE")
            continue
        items = [f"{t} [{e},{l}]" for t, (e, l) in windows.items()]
        print("  ", ", ".join(items[:4]))
        print("  ", ", ".join(items[4:]))
    # [end:run]
