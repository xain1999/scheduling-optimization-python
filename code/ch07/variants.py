"""Chapter 7 -- permutation, general and no-wait flow shops on ta001."""
from cpsat_flowshop import cpsat_flowshop, no_wait_tsp
from flowshop import taillard_instance

# [start:variants]
p = taillard_instance(873654221, 20, 5)                 # ta001
for label, solve in [
        ("permutation", lambda: cpsat_flowshop(p, permutation=True)),
        ("any order per machine",
         lambda: cpsat_flowshop(p, permutation=False)),
        ("no-wait (interval model)",
         lambda: cpsat_flowshop(p, permutation=True, no_wait=True)),
        ("no-wait (as a TSP)", lambda: no_wait_tsp(p))]:
    r = solve()
    status = "optimal" if r["optimal"] else f"bound {r['bound']}"
    print(f"{label:26} makespan {r['cmax']}  ({status})")
# [end:variants]
