"""Chapter 3 -- branch and bound from scratch on an order-selection problem.

Which orders should the shop accept for Saturday's 8-hour shift to
maximise revenue?  (A 0/1 knapsack problem, small enough to watch.)
"""
import itertools

# [start:data]
ORDERS = {        # name: (hours of press time, revenue)
    "A": (3.0, 330), "B": (2.5, 260), "C": (2.0, 190), "D": (1.5, 150),
    "E": (4.0, 360), "F": (1.0, 70),  "G": (3.5, 300), "H": (2.0, 170),
}
CAPACITY = 8.0
# [end:data]


# [start:relaxation]
def lp_bound(fixed: dict[str, int]):
    """Solve the LP relaxation given some variables fixed to 0 or 1.

    For a knapsack the LP is solved greedily: take free orders by
    decreasing revenue per hour, and a fraction of the first one that
    does not fit.  Returns (bound, fractional order or None).
    """
    used = sum(ORDERS[o][0] for o, v in fixed.items() if v == 1)
    if used > CAPACITY:
        return None, None                         # infeasible node
    value = sum(ORDERS[o][1] for o, v in fixed.items() if v == 1)
    free = sorted((o for o in ORDERS if o not in fixed),
                  key=lambda o: ORDERS[o][1] / ORDERS[o][0],
                  reverse=True)
    room = CAPACITY - used
    for o in free:
        hours, revenue = ORDERS[o]
        if hours <= room:
            room -= hours
            value += revenue
        else:
            return value + revenue * room / hours, o   # fractional
    return value, None                                  # integral
# [end:relaxation]


# [start:bnb]
def branch_and_bound(verbose: bool = True):
    best_value, best_set = 0, None
    stack = [{}]                      # nodes = partial assignments
    nodes = 0
    while stack:
        fixed = stack.pop()
        nodes += 1
        bound, frac = lp_bound(fixed)
        tag = " ".join(f"{o}={v}" for o, v in fixed.items()) or "root"
        if bound is None:
            verdict = "infeasible"
        elif bound <= best_value:
            verdict = f"bound {bound:.0f} <= {best_value}: prune"
        elif frac is None:            # LP solution is integral
            best_value = bound
            best_set = [o for o in ORDERS if fixed.get(o) == 1 or
                        (o not in fixed and _greedy_takes(fixed, o))]
            verdict = f"integral {bound:.0f}: new incumbent"
        else:                         # branch on the fractional order
            stack.append({**fixed, frac: 0})
            stack.append({**fixed, frac: 1})
            verdict = f"bound {bound:.1f}, branch on {frac}"
        if verbose:
            print(f"node {nodes:2}  {tag:24} {verdict}")
    return best_value, best_set, nodes
# [end:bnb]


def _greedy_takes(fixed, order):
    """True if the greedy LP solution at this node takes `order` fully."""
    used = sum(ORDERS[o][0] for o, v in fixed.items() if v == 1)
    free = sorted((o for o in ORDERS if o not in fixed),
                  key=lambda o: ORDERS[o][1] / ORDERS[o][0],
                  reverse=True)
    room = CAPACITY - used
    for o in free:
        if ORDERS[o][0] <= room:
            room -= ORDERS[o][0]
            if o == order:
                return True
        else:
            return False
    return False


def brute_force():
    best = (0, None)
    for k in range(len(ORDERS) + 1):
        for subset in itertools.combinations(ORDERS, k):
            hours = sum(ORDERS[o][0] for o in subset)
            value = sum(ORDERS[o][1] for o in subset)
            if hours <= CAPACITY and value > best[0]:
                best = (value, list(subset))
    return best


if __name__ == "__main__":
    # [start:run]
    value, chosen, nodes = branch_and_bound()
    print(f"\nbranch and bound: {value:.0f} with {chosen} "
          f"after {nodes} nodes")
    print("brute force check:", brute_force())
    # [end:run]
