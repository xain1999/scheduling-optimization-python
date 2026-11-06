"""Chapter 17: a scheduling engine behind a web API (FastAPI)."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "ch02"))

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field, model_validator

from cpsat_model import solve_cpsat
from schedlib import InvalidSchedule, Job, evaluate, validate_single_machine


# [start:schemas]
MAX_TIME = 10_000_000          # minutes, about 19 years: plenty


class JobIn(BaseModel):
    # Every number is bounded, so the horizon (max r + sum p) and the
    # objective (sum w * T) stay far inside CP-SAT's 64-bit integers.
    id: str = Field(min_length=1, max_length=40)
    p: int = Field(gt=0, le=10_000, description="processing time")
    r: int = Field(0, ge=0, le=MAX_TIME, description="release date")
    d: int = Field(ge=0, le=MAX_TIME, description="due date")
    w: int = Field(1, ge=0, le=1000, description="weight")


class ScheduleRequest(BaseModel):
    jobs: list[JobIn] = Field(min_length=1, max_length=500)
    time_limit: float = Field(10, gt=0, le=120)

    @model_validator(mode="after")
    def unique_ids(self):
        ids = [j.id for j in self.jobs]
        if len(ids) != len(set(ids)):
            raise ValueError("job ids must be unique")
        return self


class TaskOut(BaseModel):
    job: str
    start: int
    end: int


class ScheduleResponse(BaseModel):
    tasks: list[TaskOut]
    weighted_tardiness: int
    proven_optimal: bool
    lower_bound: float
    seconds: float
# [end:schemas]


app = FastAPI(title="Inkwell scheduling engine", version="1.0")


# [start:endpoint]
@app.post("/schedule", response_model=ScheduleResponse)
def schedule(req: ScheduleRequest) -> ScheduleResponse:
    jobs = [Job(j.id, p=j.p, r=j.r, d=j.d, w=j.w) for j in req.jobs]
    res = solve_cpsat(jobs, time_limit=req.time_limit)
    if res.schedule is None:
        raise HTTPException(503, "no schedule within the time limit")
    try:
        validate_single_machine(jobs, res.schedule)  # never ship junk
    except InvalidSchedule as err:                  # a bug on our side
        raise HTTPException(500, f"invalid schedule: {err}") from err
    tasks = sorted(res.schedule, key=lambda t: t.start)
    return ScheduleResponse(
        tasks=[TaskOut(job=t.job, start=t.start, end=t.end)
               for t in tasks],
        weighted_tardiness=evaluate(jobs, res.schedule)["sumwT"],
        proven_optimal=res.optimal, lower_bound=res.bound,
        seconds=round(res.seconds, 3))


@app.get("/health")
def health():
    return {"status": "ok"}
# [end:endpoint]
