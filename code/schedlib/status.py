"""The book's solver-status policy: read values only after a solution.

CP-SAT, HiGHS and the routing solver all return *something* when asked
for a variable's value after a failed solve. Those values are garbage.
Every solve in the book goes through one of these checks first.
"""


class NoSolution(RuntimeError):
    """The solver stopped without a feasible solution.

    The message is the solver's status: INFEASIBLE (proven: none exists),
    MODEL_INVALID (a bug in the model), or UNKNOWN (the time limit was
    reached before any solution was found -- nothing is proven).
    """


# [start:check]
def check_cpsat(solver, status) -> str:
    """Return the status name; raise NoSolution if there is none."""
    from ortools.sat.python import cp_model
    name = solver.status_name(status)
    if status not in (cp_model.OPTIMAL, cp_model.FEASIBLE):
        raise NoSolution(name)
    return name                       # "OPTIMAL" or "FEASIBLE"


def check_pulp(stats) -> str:
    """The same check for a PuLP 4 solve (HiGHS or another)."""
    if not stats.has_solution:
        raise NoSolution(stats.status_str)
    return stats.status_str
# [end:check]
