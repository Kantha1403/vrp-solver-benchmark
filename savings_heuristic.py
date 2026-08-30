"""Clarke-Wright savings algorithm — a stronger classical baseline than nearest-neighbor.

Why add this: nearest-neighbor is the "no one would ship this" strawman. Savings is
the algorithm a competent engineer would reach for before adopting a solver. Beating
THIS baseline is the credible claim for a portfolio piece — beating nearest-neighbor
alone invites the interview question "would a stronger heuristic have closed the gap?"
"""
import time
from typing import Dict, List, Tuple

from distance_utils import build_distance_matrix
from models import RoutingSolution, Scenario


def _initial_routes(num_customers: int) -> Dict[int, List[int]]:
    """Every customer starts on its own out-and-back route from the depot."""
    return {c: [c] for c in range(1, num_customers + 1)}


def _route_demand(route: List[int], demands: List[int]) -> int:
    return sum(demands[c] for c in route)


def solve_cvrp_savings(scenario: Scenario) -> RoutingSolution:
    locations = scenario.locations
    distance_matrix = build_distance_matrix(locations)
    demands = [loc.demand for loc in locations]
    n = len(scenario.customers)

    start = time.perf_counter()

    # Savings[i][j] = distance saved by merging two single-customer routes into one
    # route serving both, instead of visiting each separately from the depot.
    savings: List[Tuple[float, int, int]] = []
    for i in range(1, n + 1):
        for j in range(i + 1, n + 1):
            s = distance_matrix[0][i] + distance_matrix[0][j] - distance_matrix[i][j]
            savings.append((s, i, j))
    savings.sort(reverse=True, key=lambda x: x[0])

    routes = _initial_routes(n)
    # Why track endpoints: a customer can only be merged at the position where it's
    # adjacent to the depot (a route's first or last stop) — merging mid-route would
    # require the vehicle to double back, which isn't a valid CVRP move.
    route_of = {c: c for c in range(1, n + 1)}  # customer -> route key (mutates on merge)

    for _, i, j in savings:
        route_i_key, route_j_key = route_of[i], route_of[j]
        if route_i_key == route_j_key:
            continue  # already in the same route

        route_i, route_j = routes[route_i_key], routes[route_j_key]
        i_is_endpoint = i in (route_i[0], route_i[-1])
        j_is_endpoint = j in (route_j[0], route_j[-1])
        if not (i_is_endpoint and j_is_endpoint):
            continue

        combined_demand = _route_demand(route_i, demands) + _route_demand(route_j, demands)
        if combined_demand > scenario.vehicle_capacity:
            continue

        # Why four orientation cases: i and j can each be at the front or back of
        # their route, and the merge must connect them so the join point is where
        # savings[i][j] was actually computed (i adjacent to j in the new route).
        if route_i[-1] == i and route_j[0] == j:
            merged = route_i + route_j
        elif route_i[0] == i and route_j[-1] == j:
            merged = route_j + route_i
        elif route_i[-1] == i and route_j[-1] == j:
            merged = route_i + route_j[::-1]
        elif route_i[0] == i and route_j[0] == j:
            merged = route_i[::-1] + route_j
        else:
            continue  # neither i nor j is actually an endpoint of its route (safety net)

        del routes[route_j_key]
        routes[route_i_key] = merged
        for c in merged:
            route_of[c] = route_i_key

    final_routes = list(routes.values())
    elapsed = time.perf_counter() - start

    # Why this can be infeasible: savings merges routes down, it never splits an
    # over-capacity single customer back out — if the fleet has too few vehicles
    # for the resulting route count, some customers are left unvisited.
    if len(final_routes) > scenario.num_vehicles:
        return RoutingSolution(
            routes=[], total_distance=0.0, solve_time_seconds=elapsed,
            feasible=False, is_optimal=False, solver_name="Clarke-Wright Savings",
        )

    total_distance = 0.0
    for route in final_routes:
        total_distance += distance_matrix[0][route[0]]
        for a, b in zip(route, route[1:]):
            total_distance += distance_matrix[a][b]
        total_distance += distance_matrix[route[-1]][0]

    return RoutingSolution(
        routes=final_routes,
        total_distance=total_distance,
        solve_time_seconds=elapsed,
        feasible=True,
        is_optimal=False,
        solver_name="Clarke-Wright Savings",
    )
