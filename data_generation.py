"""Generates reproducible CVRP scenarios for benchmarking solvers.

Why synthetic: a public CVRP dataset (e.g. Solomon/Uchoa instances) would be more
"credible" for a portfolio piece, but coupling the harness to a fixed file format
hides the KPI logic. Seeded generation gives the same rigor (repeatable, scenario
sweeps) while keeping the evaluation harness the visible centerpiece.
"""
import random
from typing import Optional

from models import Customer, Scenario


def generate_scenario(
    seed: int,
    num_customers: int = 20,
    num_vehicles: int = 4,
    vehicle_capacity: int = 50,
    grid_size: float = 100.0,
    demand_range: tuple = (1, 15),
    force_infeasible: bool = False,
) -> Scenario:
    """Builds one random CVRP instance.

    `force_infeasible=True` inflates demand beyond fleet capacity — used to verify
    both solvers report infeasibility cleanly instead of crashing or silently
    dropping customers.
    """
    if num_customers <= 0:
        raise ValueError("num_customers must be positive; a depot-only scenario is degenerate")
    if num_vehicles <= 0 or vehicle_capacity <= 0:
        raise ValueError("num_vehicles and vehicle_capacity must be positive")

    rng = random.Random(seed)
    depot = Customer(id=0, x=grid_size / 2, y=grid_size / 2, demand=0)

    customers = []
    for i in range(1, num_customers + 1):
        demand = rng.randint(*demand_range)
        customers.append(Customer(
            id=i,
            x=rng.uniform(0, grid_size),
            y=rng.uniform(0, grid_size),
            demand=demand,
        ))

    if force_infeasible:
        # Why: push one customer's demand above total fleet capacity so the
        # scenario is guaranteed infeasible, regardless of the random draw above.
        overloaded = customers[0]
        customers[0] = Customer(
            id=overloaded.id, x=overloaded.x, y=overloaded.y,
            demand=num_vehicles * vehicle_capacity + 1,
        )

    return Scenario(
        seed=seed,
        depot=depot,
        customers=customers,
        num_vehicles=num_vehicles,
        vehicle_capacity=vehicle_capacity,
    )


def generate_scenario_batch(
    seeds: list,
    num_customers: int = 20,
    num_vehicles: int = 4,
    vehicle_capacity: int = 50,
) -> list:
    """One scenario per seed — the unit the evaluation harness sweeps over."""
    return [
        generate_scenario(seed, num_customers, num_vehicles, vehicle_capacity)
        for seed in seeds
    ]
