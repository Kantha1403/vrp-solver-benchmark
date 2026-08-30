"""Naive nearest-neighbor CVRP heuristic — the baseline the CP solver is judged against.

Why include this at all: an optimizer's KPI numbers are meaningless without a
reference point. This is deliberately the simplest reasonable heuristic a team might
reach for before adopting a solver, so the eventual gap reflects real solver value,
not a strawman comparison.
"""
import time

from distance_utils import build_distance_matrix
from models import RoutingSolution, Scenario


def solve_cvrp_nearest_neighbor(scenario: Scenario) -> RoutingSolution:
    locations = scenario.locations
    distance_matrix = build_distance_matrix(locations)
    demands = [loc.demand for loc in locations]

    unvisited = set(range(1, len(locations)))  # exclude depot
    routes = []
    total_distance = 0.0

    start = time.perf_counter()
    for _ in range(scenario.num_vehicles):
        if not unvisited:
            break
        route = []
        remaining_capacity = scenario.vehicle_capacity
        current = 0  # depot

        while True:
            # Why: filter by remaining capacity BEFORE picking nearest — otherwise
            # the heuristic could pick a close customer it can't actually serve.
            feasible_next = [
                c for c in unvisited if demands[c] <= remaining_capacity
            ]
            if not feasible_next:
                break
            next_stop = min(feasible_next, key=lambda c: distance_matrix[current][c])
            route.append(next_stop)
            total_distance += distance_matrix[current][next_stop]
            remaining_capacity -= demands[next_stop]
            unvisited.discard(next_stop)
            current = next_stop

        if route:
            total_distance += distance_matrix[current][0]  # return to depot
            routes.append(route)

    elapsed = time.perf_counter() - start

    # Why: leftover customers mean no vehicle had enough remaining capacity for
    # them even at full load — a real infeasibility, not a heuristic quirk, when it
    # happens on the FIRST stop of an otherwise-empty vehicle.
    feasible = len(unvisited) == 0

    return RoutingSolution(
        routes=routes,
        total_distance=total_distance,
        solve_time_seconds=elapsed,
        feasible=feasible,
        is_optimal=False,  # heuristics never claim optimality
        solver_name="Nearest-Neighbor Heuristic",
    )
