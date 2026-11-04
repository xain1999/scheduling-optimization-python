"""Diagnostic switch: cap the number of CP-SAT search workers.

The book's examples run CP-SAT with 8 parallel workers.  If CP-SAT
misbehaves on a particular machine (for example, a crash inside the
native solver), rerun with fewer workers without editing any example:

    SCHEDBOOK_WORKERS=1 python ch04/paint_shop.py        (macOS/Linux)
    set SCHEDBOOK_WORKERS=1  &  python ch04\\paint_shop.py (Windows)
    python run.py examples --workers 1                    (any system)

Results can differ from the book with fewer workers: CP-SAT then runs a
single search strategy instead of a portfolio, so time-limited runs may
end with another schedule, a weaker bound, or FEASIBLE instead of
OPTIMAL.  Always read the printed status.
"""
import os


def limit_cpsat_workers(n: int) -> None:
    """Make every CpSolver in this process use at most n workers."""
    from ortools.sat.python import cp_model
    original = cp_model.CpSolver.solve
    if getattr(original, "_capped", False):
        return

    def solve(self, model, *args, **kwargs):
        if not 0 < self.parameters.num_workers <= n:
            self.parameters.num_workers = n
        return original(self, model, *args, **kwargs)

    solve._capped = True
    cp_model.CpSolver.solve = solve


def apply_environment() -> None:
    """Honour SCHEDBOOK_WORKERS if it is set (called by schedlib)."""
    value = os.environ.get("SCHEDBOOK_WORKERS", "").strip()
    if value:
        limit_cpsat_workers(int(value))
