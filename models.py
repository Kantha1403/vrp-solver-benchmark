"""Shared data structures for the capacitated VRP problem."""
from dataclasses import dataclass, field
from typing import List


@dataclass(frozen=True)
class Customer:
    id: int
    x: float
    y: float
    demand: int


@dataclass(frozen=True)
class Scenario:
    """A single problem instance. Depot is always index 0 in `locations`."""
    seed: int
    depot: Customer
    customers: List[Customer]
    num_vehicles: int
    vehicle_capacity: int

    @property
    def locations(self) -> List[Customer]:
        return [self.depot] + self.customers

    @property
    def total_demand(self) -> int:
        return sum(c.demand for c in self.customers)

    @property
    def fleet_capacity(self) -> int:
        return self.num_vehicles * self.vehicle_capacity


@dataclass
class RoutingSolution:
    """Uniform output contract so CP-SAT and the heuristic are directly comparable."""
    routes: List[List[int]]  # each route is a list of location indices, depot excluded
    total_distance: float
    solve_time_seconds: float
    feasible: bool
    # Why: CP-SAT can hit a time limit without proving optimality; downstream KPI
    # reporting needs to distinguish "optimal" from "best found so far".
    is_optimal: bool
    solver_name: str = ""
