"""Chapter 3: the 'tight' lot-sizing model written in Pyomo."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import pulp
import pyomo.environ as pyo

from lot_sizing import build, random_data
from schedlib.status import check_pulp


# [start:pyomo]
def build_pyomo(data):
    m = pyo.ConcreteModel("lot_sizing")
    m.P = pyo.Set(initialize=data.products)
    m.T = pyo.Set(initialize=data.periods, ordered=True)

    m.x = pyo.Var(m.P, m.T, domain=pyo.NonNegativeReals)   # production
    m.s = pyo.Var(m.P, m.T, domain=pyo.NonNegativeReals)   # inventory
    m.y = pyo.Var(m.P, m.T, domain=pyo.Binary)             # setup

    m.cost = pyo.Objective(expr=sum(
        data.setup_cost[i] * m.y[i, t] + data.hold_cost[i] * m.s[i, t]
        for i in m.P for t in m.T), sense=pyo.minimize)

    @m.Constraint(m.P, m.T)
    def flow(m, i, t):
        prev = m.s[i, t - 1] if t > 1 else 0
        return prev + m.x[i, t] - m.s[i, t] == data.demand[i, t]

    @m.Constraint(m.T)
    def capacity(m, t):
        return sum(data.unit_time[i] * m.x[i, t] +
                   data.setup_time[i] * m.y[i, t] for i in m.P) \
            <= data.capacity[t]

    @m.Constraint(m.P, m.T)
    def setup(m, i, t):
        fits = ((data.capacity[t] - data.setup_time[i])
                / data.unit_time[i])
        rest = sum(data.demand[i, k] for k in m.T if k >= t)
        return m.x[i, t] <= max(0, min(fits, rest)) * m.y[i, t]
    return m
# [end:pyomo]


if __name__ == "__main__":
    # [start:run]
    data = random_data(n_products=8, n_periods=15)
    model = build_pyomo(data)
    highs = pyo.SolverFactory("highs")
    highs.options["threads"] = 1      # same pool size as PuLP below
    result = highs.solve(model)
    print("Pyomo:", result.solver.termination_condition,
          round(pyo.value(model.cost)))
    stats = build(data, "tight").solve(pulp.HiGHS(msg=False,
                                                  threads=1))
    print("PuLP: ", check_pulp(stats), round(stats.objective))
    # [end:run]
