# Scheduling Optimization with Python — companion code

Tested code for the book **Scheduling Optimization with Python: From
Dispatching Rules to Constraint Programming, Mathematical Optimization,
and Metaheuristics** by Mohammed Hadjoudj (First Edition, 2026).

Every listing printed in the book is taken from these files, between
markers of the form `# [start:name]` and `# [end:name]`. A listing's
label in the book (for example `code/ch10/roster.py · soft`) tells you
which file and block it comes from. The files here are complete and
runnable.

## Quick start

You need **Python 3.12 or newer**.

Get the code in one of two ways:

- **With git:** copy the address shown under the green **Code** button
  on this page, then run `git clone <that address>`.
- **Without git:** choose **Code → Download ZIP** and unzip it. The
  release `v1.0` (under **Releases**) is the exact code printed in the
  first edition of the book.

Then create a virtual environment inside the `code` folder:

```bash
cd scheduling-optimization-python/code
python -m venv .venv
```

Activate the environment:

| System | Command |
|---|---|
| macOS / Linux | `source .venv/bin/activate` |
| Windows, Command Prompt | `.venv\Scripts\activate.bat` |
| Windows, PowerShell | `.\.venv\Scripts\Activate.ps1` |

Then install the pinned versions and run the first example:

```bash
pip install -r requirements.txt
python ch01/dispatching_rules.py
```

## Running everything

From the `code/` folder, on any operating system:

```bash
python run.py test           # quick examples and all test suites, minutes
python run.py examples       # every other example script, about an hour
python run.py figures        # regenerate every figure into ../figures
python run.py experiments    # rerun all benchmarks, several hours
```

Together the four jobs run every runnable script in the repository.
Add `--workers 1` to any of them to cap CP-SAT at one search worker
(see *If CP-SAT crashes*).

If you have `make`, `make test`, `make examples`, `make figures` and
`make experiments` run from the repository root do the same.

## Layout

| Path | Contents |
|---|---|
| `code/schedlib/` | Shared helpers: jobs and tasks, objectives, the schedule validator, Gantt charts, solver-status checks (`status.py`), stored results (`results.py`) |
| `code/ch01/` – `code/ch17/` | One folder per chapter (see below) |
| `code/tests/` | `test_crosscheck.py`: selected exact methods (single machine, flow shop, parallel machines, projects) against brute force on random small instances, heuristics against the rules of their problem. `test_reference_results.py`: independent validation of the stored schedules and routes shown in the book. `test_regressions.py`: edge cases (infeasible inputs, optional visits, zero-duration activities, unknown resources, cyclic precedences and machine orders, overdue jobs, validator under `python -O`) |
| `code/data/jobshop/` | Classic job-shop benchmark instances and their known optima |
| `code/run.py` | Cross-platform runner for tests, figures and experiments |
| `code/requirements.txt` | Exact package versions used for every result in the book |
| `results/` | Raw benchmark results (CSV/JSON) and the reference solutions shown in the book |
| `figures/`, `tables/` | Output folders for `run.py figures` and the table scripts |

### Chapters

| Folder | Chapter | Main files |
|---|---|---|
| `ch01` | What Is Scheduling? | `print_shop.py`, `dispatching_rules.py`, `brute_force.py` |
| `ch02` | Modeling Scheduling Problems | `milp_disjunctive.py`, `milp_time_indexed.py`, `cpsat_model.py`, `parallel_cpsat.py`, `compare.py` |
| `ch03` | Mathematical Programming for Scheduling | `lp_example.py`, `branch_and_bound.py`, `lot_sizing.py`, `lot_sizing_pyomo.py`, `read_log.py` |
| `ch04` | Constraint Programming with CP-SAT | `propagation.py`, `cumulative_crew.py`, `reservoir_buffer.py`, `berth_2d.py`, `paint_shop.py` |
| `ch05` | Single-Machine Scheduling | `moore_hodgson.py`, `lawler_prec.py`, `dp_wt.py`, `atc.py`, `earliness_tardiness.py`, `benchmark.py` |
| `ch06` | Parallel Machine Scheduling | `lpt.py`, `pcmax_models.py`, `pcmax_benchmark.py`, `gpu_cluster.py` |
| `ch07` | Flow Shop Scheduling | `flowshop.py`, `neh.py`, `cpsat_flowshop.py`, `variants.py`, `benchmark.py` |
| `ch08` | Job Shop Scheduling | `jobshop.py`, `giffler_thompson.py`, `cpsat_jobshop.py`, `milp_jobshop.py`, `workshop_operators.py` |
| `ch09` | Project Scheduling with Limited Resources | `renovation.py`, `rcpsp.py`, `crashing.py`, `random_experiment.py` |
| `ch10` | Employee Shift Scheduling and Rostering | `roster.py` |
| `ch11` | Timetabling | `exams.py`, `school.py` |
| `ch12` | Scheduling with Time Windows and Travel | `clinic.py`, `field_service.py` |
| `ch13` | Dispatching Rules and Constructive Heuristics | `atcs.py`, `fast_neh.py`, `sgs.py`, `sgs_experiment.py` |
| `ch14` | Metaheuristics | `local_search.py`, `iterated_greedy.py`, `genetic.py`, `experiment_wt.py`, `experiment_flow.py` |
| `ch15` | Large-Scale Scheduling | `lns_jobshop.py`, `rolling_horizon.py`, `lns_experiment.py` |
| `ch16` | Uncertainty and Rescheduling | `robust.py`, `reschedule.py` |
| `ch17` | Deploying a Scheduling Engine | `service.py`, `test_service.py`, `plotly_gantt.py` |

Each folder also has a `make_figures.py` (and, for the benchmarks,
`make_tables.py`) that regenerates the book's figures and tables.

## Reproducibility notes

- **Seeds.** All random instances come from fixed seeds.
- **Stored solutions.** Many examples have several optimal solutions, and
  CP-SAT with several workers or a time limit may return a different one
  on each run.
  - The solution shown in the book is stored in `results/`, and the
    figures are drawn from it.
  - A rerun may print another, equally good solution. Delete the stored
    file to make the new one the reference.
- **Hardware.** Timings in the book were measured on a two-core cloud
  machine (Intel Xeon, 2.8 GHz, 8 GB, Ubuntu 24.04, Python 3.13). Your
  times will differ.
- **Proven optimal.** Values reported as proven optimal do not change
  from run to run.
- **Thread counts.** CP-SAT ran with 8 workers, HiGHS with 1 thread, and
  the Python heuristics on one core.

## If CP-SAT crashes

A crash inside CP-SAT's native code ends Python with `Segmentation fault`
(exit code 139) and no traceback. This has been observed on some Linux
systems in the longer multi-worker examples (paint shop, GPU cluster),
while the same runs work cleanly elsewhere. Cap the number of search
workers without editing any code:

```bash
SCHEDBOOK_WORKERS=1 python ch04/paint_shop.py   # macOS / Linux
python run.py examples --workers 1              # any system
```

With one worker, time-limited runs can end with a different schedule or
a weaker bound than in the book. Read the printed status. Also make sure
the virtual environment contains only the packages in
`requirements.txt`.

## Notebooks

Start Jupyter in the `code` folder and use `%run ch02/cpsat_model.py`.
Do not paste whole scripts into cells: they locate `schedlib` through
`__file__`, which a cell does not define.

## Known issue: OR-Tools and HiGHS together

OR-Tools ships its own copy of HiGHS. With OR-Tools 9.15, `highspy` 1.14
works and 1.15 does not: importing both fails with an `undefined symbol`
error.

Keep the pinned versions. If you upgrade, pin `highspy<1.15`, or run MILP
and CP-SAT code in separate processes.

HiGHS also creates one thread pool per process. A later solve that asks
for a different number of threads fails with `NotSolved`. Every script
here passes `threads=1`.

## Errata

Corrections are listed in [ERRATA.md](ERRATA.md). Please report problems
through the repository's issue tracker.

## License

The code is released under the MIT License (see [LICENSE](LICENSE)).

The job-shop instances in `code/data/jobshop/` are public benchmarks
from the literature. They were taken from the JSPLIB collection; see the
README in that folder for their original sources.
