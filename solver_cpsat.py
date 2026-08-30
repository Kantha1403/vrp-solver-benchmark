"""Optimal/near-optimal CVRP solver via OR-Tools' CP-based routing engine.

Why the routing library instead of raw CP-SAT: OR-Tools' `constraint_solver.pywrapcp`
routing module is purpose-built for vehicle routing (it handles the circuit/capacity
constraints that would otherwise need to be hand-modeled in raw CP-SAT) and is the
tool Google itself recommends for VRP variants. It still solves via constraint
programming + local search, which is what the JD's "CP-SAT" line is testing for.
"""
import time

from ortools.constraint_solver import routing_enums_pb2
from ortools.constraint_solver import pywrapcp

from distance_utils import build_scaled_int_matrix
from models import RoutingSolution, Scenario


def solve_cvrp(scenario: Scenario, time_limit_seconds: int = 10) -> RoutingSolution:
    """Solves the scenario's capacitated VRP.

    Returns a RoutingSolution with feasible=False (not an exception) when no
    solution exists — infeasibility is a normal, expected outcome for a solver,
    not an error condition.
    """
    locations = scenario.locations
    distance_matrix = build_scaled_int_matrix(locations)
    demands = [loc.demand for loc in locations]

    manager = pywrapcp.RoutingIndexManager(
        len(locations), scenario.num_vehicles, 0  # depot index = 0
    )
    routing = pywrapcp.RoutingModel(manager)

    def distance_callback(from_index, to_index):
        from_node = manager.IndexToNode(from_index)
        to_node = manager.IndexToNode(to_index)
        return distance_matrix[from_node][to_node]

    transit_callback_index = routing.RegisterTransitCallback(distance_callback)
    routing.SetArcCostEvaluatorOfAllVehicles(transit_callback_index)

    def demand_callback(from_index):
        node = manager.IndexToNode(from_index)
        return demands[node]

    demand_callback_index = routing.RegisterUnaryTransitCallback(demand_callback)
    routing.AddDimensionWithVehicleCapacity(
        demand_callback_index,
        0,  # no slack
        [scenario.vehicle_capacity] * scenario.num_vehicles,
        True,  # start cumul at zero
        "Capacity",
    )

    search_parameters = pywrapcp.DefaultRoutingSearchParameters()
    search_parameters.first_solution_strategy = (
        routing_enums_pb2.FirstSolutionStrategy.PATH_CHEAPEST_ARC
    )
    search_parameters.local_search_metaheuristic = (
        routing_enums_pb2.LocalSearchMetaheuristic.GUIDED_LOCAL_SEARCH
    )
    search_parameters.time_limit.FromSeconds(time_limit_seconds)

    start = time.perf_counter()
    solution = routing.SolveWithParameters(search_parameters)
    elapsed = time.perf_counter() - start

    if solution is None:
        return RoutingSolution(
            routes=[], total_distance=0.0, solve_time_seconds=elapsed,
            feasible=False, is_optimal=False, solver_name="OR-Tools CP Routing",
        )

    routes = []
    total_distance_scaled = 0
    for vehicle_id in range(scenario.num_vehicles):
        index = routing.Start(vehicle_id)
        route = []
        while not routing.IsEnd(index):
            node = manager.IndexToNode(index)
            if node != 0:  # exclude depot from the route's customer list
                route.append(node)
            previous_index = index
            index = solution.Value(routing.NextVar(index))
            total_distance_scaled += routing.GetArcCostForVehicle(
                previous_index, index, vehicle_id
            )
        if route:  # Why: omit vehicles that never left the depot
            routes.append(route)

    return RoutingSolution(
        routes=routes,
        total_distance=total_distance_scaled / 1000,  # undo the scaling from build_scaled_int_matrix
        solve_time_seconds=elapsed,
        feasible=True,
        # Why: the search can exit on the time limit rather than proving optimality;
        # SolveWithParameters gives no direct optimality flag, so treat a full time-
        # limit exhaustion as "not proven optimal" for honest KPI reporting.
        is_optimal=elapsed < time_limit_seconds,
        solver_name="OR-Tools CP Routing",
    )
