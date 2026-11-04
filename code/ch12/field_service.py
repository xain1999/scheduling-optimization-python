"""Chapter 12 -- field service: technicians, time windows, and travel."""
import math
import random
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from ortools.constraint_solver import pywrapcp, routing_enums_pb2

from schedlib.results import save
from schedlib.status import NoSolution


# [start:data]
DEPOT = (50, 50)
SHIFT = (8 * 60, 17 * 60)              # technicians work 8:00-17:00


def visits(n=30, seed=4):
    """Customer visits: location, service minutes, a two- or four-hour
    window promised to the customer, and the skill required."""
    rng = random.Random(seed)
    out = []
    for i in range(n):
        start = rng.choice([8, 10, 12, 14]) * 60
        width = rng.choice([120, 120, 240])
        out.append(dict(name=f"C{i+1}", xy=(rng.uniform(0, 100),
                                            rng.uniform(0, 100)),
                        service=rng.choice([30, 45, 60, 90]),
                        window=(start, min(start + width, SHIFT[1])),
                        skill=rng.choice(["boiler", "boiler",
                                          "electric"])))
    return out


TECHS = {"Tara": {"boiler", "electric"}, "Umar": {"boiler"},
         "Vera": {"boiler"}, "Wes": {"electric", "boiler"}}


def minutes(a, b):
    """Driving time: 1.2 minutes per distance unit, at least 5."""
    return max(5, round(1.2 * math.dist(a, b)))


# Skipping a visit must cost more than all the driving it could save.
# Driving fits inside the shifts, so the total over all technicians is
# at most 4 * 540 = 2,160 minutes: with 10,000 per skipped visit, any
# plan that serves one more visit is cheaper, whatever its routes.
SKIP = 10_000
# [end:data]


# [start:model]
def plan_routes(jobs, techs=TECHS, seconds=15):
    points = [DEPOT] + [j["xy"] for j in jobs]
    names = list(techs)
    manager = pywrapcp.RoutingIndexManager(len(points), len(names), 0)
    routing = pywrapcp.RoutingModel(manager)

    def travel(i, j):                    # driving minutes, i to j
        a, b = manager.IndexToNode(i), manager.IndexToNode(j)
        return minutes(points[a], points[b])

    def service_plus_travel(i, j):       # start at i until reaching j
        a = manager.IndexToNode(i)
        service = jobs[a - 1]["service"] if a > 0 else 0
        return service + travel(i, j)
    cost = routing.RegisterTransitCallback(travel)
    routing.SetArcCostEvaluatorOfAllVehicles(cost)     # objective
    transit = routing.RegisterTransitCallback(service_plus_travel)
    max_wait = SHIFT[1] - SHIFT[0]       # waiting allowed all day
    routing.AddDimension(transit, max_wait, SHIFT[1], False, "Time")
    time_dim = routing.GetDimensionOrDie("Time")
    for node, job in enumerate(jobs, start=1):
        idx = manager.NodeToIndex(node)
        time_dim.CumulVar(idx).SetRange(*job["window"])   # promise
        allowed = [v for v, t in enumerate(names)
                   if job["skill"] in techs[t]]
        # skills: restrict which vehicle may visit (-1 = not visited)
        routing.VehicleVar(idx).SetValues([-1] + allowed)
        routing.AddDisjunction([idx], SKIP)     # may skip, at a price
    for v in range(len(names)):
        time_dim.CumulVar(routing.Start(v)).SetRange(*SHIFT)
        time_dim.CumulVar(routing.End(v)).SetRange(*SHIFT)
        routing.AddVariableMinimizedByFinalizer(
            time_dim.CumulVar(routing.End(v)))

    params = pywrapcp.DefaultRoutingSearchParameters()
    params.first_solution_strategy = (
        routing_enums_pb2.FirstSolutionStrategy.PATH_CHEAPEST_ARC)
    params.local_search_metaheuristic = (
        routing_enums_pb2.LocalSearchMetaheuristic.GUIDED_LOCAL_SEARCH)
    params.time_limit.FromSeconds(seconds)
    sol = routing.SolveWithParameters(params)
    if sol is None:                   # no feasible routes were found
        raise NoSolution(routing.status())

    routes = {}
    for v, tech in enumerate(names):
        idx, stops = routing.Start(v), []
        while not routing.IsEnd(idx):
            node = manager.IndexToNode(idx)
            if node > 0:
                stops.append((jobs[node - 1]["name"],
                              sol.Value(time_dim.CumulVar(idx))))
            idx = sol.Value(routing.NextVar(idx))
        routes[tech] = stops
    skipped = [j["name"] for node, j in enumerate(jobs, 1)
               if sol.Value(routing.NextVar(manager.NodeToIndex(node)))
               == manager.NodeToIndex(node)]
    return routes, skipped, sol.ObjectiveValue()
# [end:model]


def hhmm(t):
    return f"{t // 60:02d}:{t % 60:02d}"


if __name__ == "__main__":
    # [start:run]
    jobs = visits()
    routes, skipped, cost = plan_routes(jobs)
    for tech, stops in routes.items():
        text = [f"{n}@{hhmm(t)}" for n, t in stops]
        print(f"{tech:5}", " ".join(text[:5]))
        if len(text) > 5:
            print(" " * 5, " ".join(text[5:]))
    print("not served today:", skipped or "none")
    # [end:run]
    save("ch12_routes", {"routes": routes, "skipped": skipped})
