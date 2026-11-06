"""Chapter 3: capacitated lot sizing: three formulations of one model."""
import random
import sys
import time
from dataclasses import dataclass
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import pulp

from schedlib.status import NoSolution, check_pulp


# [start:data]
@dataclass
class LotSizingData:
    products: list[str]
    periods: list[int]            # 1..T
    demand: dict                  # (i, t) -> units
    unit_time: dict               # i -> press hours per unit
    setup_time: dict              # i -> hours lost when switching to i
    setup_cost: dict              # i -> cost of a setup
    hold_cost: dict               # i -> cost per unit per period
    capacity: dict                # t -> press hours available
# [end:data]


def random_data(n_products=15, n_periods=24, seed=0) -> LotSizingData:
    rng = random.Random(seed)
    P = [f"P{i+1}" for i in range(n_products)]
    T = list(range(1, n_periods + 1))
    demand = {(i, t): (rng.randint(5, 40) if rng.random() < 0.7 else 0)
              for i in P for t in T}
    unit = {i: rng.choice([1, 1, 2]) for i in P}
    st = {i: rng.randint(4, 10) for i in P}
    sc = {i: rng.randint(150, 400) for i in P}
    h = {i: rng.randint(1, 4) for i in P}
    load = sum(unit[i] * demand[i, t] for i in P for t in T) / len(T)
    cap = {t: int(1.25 * load + 0.5 * sum(st.values())) for t in T}
    return LotSizingData(P, T, demand, unit, st, sc, h, cap)


# [start:model]
def build(data: LotSizingData, variant: str, relax: bool = False):
    """variant: 'weak' (huge M), 'tight' (smallest valid M),
    'strong' (tight M plus (l,S) inequalities)."""
    P, T, d = data.products, data.periods, data.demand
    m = pulp.LpProblem(f"lot_sizing_{variant}", pulp.LpMinimize)
    kind = pulp.LpContinuous if relax else pulp.LpBinary
    x = {(i, t): m.add_variable(f"x_{i}_{t}", 0) for i in P for t in T}
    s = {(i, t): m.add_variable(f"s_{i}_{t}", 0) for i in P for t in T}
    y = {(i, t): m.add_variable(f"y_{i}_{t}", 0, 1, kind)
         for i in P for t in T}

    m += pulp.lpSum(data.setup_cost[i] * y[i, t] +
                    data.hold_cost[i] * s[i, t] for i in P for t in T)

    for i in P:
        for t in T:
            prev = s[i, t - 1] if t > 1 else 0
            m += prev + x[i, t] - s[i, t] == d[i, t]   # inventory flow
    for t in T:
        m += pulp.lpSum(data.unit_time[i] * x[i, t] +
                        data.setup_time[i] * y[i, t] for i in P) \
            <= data.capacity[t]                         # press hours

    for i in P:
        for t in T:
            if variant == "weak":
                M = 100_000
            else:   # what can be made in t, and what is still needed
                fits = (data.capacity[t] - data.setup_time[i]) \
                    / data.unit_time[i]
                rest = sum(d[i, k] for k in T if k >= t)
                M = max(0, min(fits, rest))
            m += x[i, t] <= M * y[i, t]                 # setup forcing
            if variant == "strong":
                m += x[i, t] <= d[i, t] * y[i, t] + s[i, t]
    return m
# [end:model]


def solve(data, variant, time_limit=60):
    lp = build(data, variant, relax=True)
    # one thread everywhere: HiGHS keeps a single thread pool per
    # process and rejects a later solve that asks for another size
    lp_result = lp.solve(pulp.HiGHS(msg=False, threads=1))
    if lp_result.status != pulp.LpSolveStatus.Optimal:
        raise NoSolution("LP relaxation: " + lp_result.status_str)
    lp_bound = lp_result.objective        # a valid bound: LP is optimal
    m = build(data, variant)
    t0 = time.perf_counter()
    st = m.solve(pulp.HiGHS(msg=False, timeLimit=time_limit, threads=1))
    check_pulp(st)            # no plan at all: stop here, don't print one
    return dict(variant=variant, lp=lp_bound, obj=st.objective,
                bound=st.best_bound,
                seconds=time.perf_counter() - t0,
                optimal=st.status == pulp.LpSolveStatus.Optimal)


if __name__ == "__main__":
    # [start:run]
    data = random_data()
    print(f"{'variant':8} {'LP bound':>9} {'best':>7} {'bound':>7} "
          f"{'time':>6}")
    for v in ["weak", "tight", "strong"]:
        r = solve(data, v)
        print(f"{v:8} {r['lp']:9.0f} {r['obj']:7.0f} "
              f"{r['bound']:7.0f} {r['seconds']:5.1f}s")
    # [end:run]
