"""Cross-platform runner: the same jobs as the Makefile, without make.

    python run.py test          quick examples + test suites (minutes)
    python run.py examples      every other example script (about an
                                hour: several solve with time limits)
    python run.py figures       regenerate the figures
    python run.py experiments   rerun the long benchmarks (hours)

Together the four jobs run every runnable script in the repository.

Add --workers N (e.g. --workers 1) to cap the number of CP-SAT search
workers in every script: a diagnostic mode for machines on which the
default of 8 parallel workers misbehaves (see schedlib/diagnostics.py).

Run it from the code/ folder of the repository, inside the virtual
environment described in Appendix A.
"""
import os
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent

TEST = ["ch01/dispatching_rules.py", "ch02/milp_disjunctive.py",
        "ch02/milp_time_indexed.py", "ch02/cpsat_model.py",
        "ch02/lp_bounds.py", "ch03/lp_example.py",
        "ch03/branch_and_bound.py", "ch03/lot_sizing_pyomo.py",
        "ch04/propagation.py", "ch04/cumulative_crew.py",
        "ch04/berth_2d.py", "ch05/moore_hodgson.py",
        "ch05/lawler_prec.py", "ch06/lpt.py", "ch07/flowshop.py",
        "ch09/renovation.py", "ch11/school.py", "ch12/clinic.py",
        "ch13/atcs.py", "ch17/test_service.py",
        "tests/test_regressions.py", "tests/test_crosscheck.py",
        "tests/test_reference_results.py"]
EXAMPLES = ["ch01/brute_force.py", "ch02/parallel_cpsat.py",
            "ch03/lot_sizing.py", "ch03/read_log.py",
            "ch04/paint_shop.py", "ch04/reservoir_buffer.py",
            "ch05/dp_wt.py", "ch05/earliness_tardiness.py",
            "ch06/gpu_cluster.py", "ch07/variants.py",
            "ch08/workshop_operators.py", "ch09/crashing.py",
            "ch10/roster.py", "ch11/exams.py", "ch12/field_service.py",
            "ch13/fast_neh.py", "ch15/rolling_horizon.py",
            "ch16/reschedule.py", "ch16/robust.py",
            "ch17/plotly_gantt.py"]
FIGURES = [f"{d}/make_figures.py" for d in
           ("ch01", "ch02", "ch03", "ch04", "ch06", "ch07", "ch08",
            "ch09", "ch12", "ch15", "ch16", "ch17")]
EXPERIMENTS = ["ch02/compare.py", "ch05/benchmark.py",
               "ch06/pcmax_benchmark.py",
               "ch05/large_with_hint.py", "ch05/make_tables.py",
               "ch07/benchmark.py", "ch08/benchmark.py",
               "ch08/make_tables.py", "ch09/random_experiment.py",
               "ch13/sgs_experiment.py", "ch14/experiment_wt.py",
               "ch14/experiment_flow.py", "ch14/make_tables.py",
               "ch15/lns_experiment.py"]
JOBS = {"test": TEST, "examples": EXAMPLES, "figures": FIGURES,
        "experiments": EXPERIMENTS}


def main(job, workers=None):
    env = dict(os.environ)
    if workers is not None:
        env["SCHEDBOOK_WORKERS"] = str(workers)
    for script in JOBS[job]:
        path = HERE / script
        print(f"--- {script}", flush=True)
        subprocess.run([sys.executable, path.name], cwd=path.parent,
                       env=env, check=True)


if __name__ == "__main__":
    args = sys.argv[1:]
    workers = None
    if len(args) == 3 and args[1] == "--workers" and args[2].isdigit():
        workers = int(args[2])
        args = args[:1]
    if len(args) != 1 or args[0] not in JOBS:
        sys.exit(__doc__)
    main(args[0], workers)
