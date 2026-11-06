"""schedlib: small helper library for 'Scheduling Optimization with Python'."""
from .diagnostics import apply_environment as _apply_environment
from .core import (InvalidSchedule, Job, SolveResult, Task, check_jobs,
                   completion_times, evaluate, sequence_to_schedule,
                   validate_single_machine)

__all__ = ["InvalidSchedule", "Job", "SolveResult", "Task", "check_jobs",
           "completion_times", "evaluate", "sequence_to_schedule",
           "validate_single_machine"]

_apply_environment()          # SCHEDBOOK_WORKERS=1: see diagnostics.py
