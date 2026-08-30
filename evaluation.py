"""Runs both solvers across a scenario sweep and reports comparison KPIs.

Why a dedicated harness module: the JD asks for "offline simulation... ablations,
and scenario analysis" as a distinct skill from building the solver itself. Keeping
this separate from solver_cpsat.py and baseline_heuristic.py means either solver can
be swapped or extended without touching how they're scored.
"""
from dataclasses import asdict
from typing import Callable, List

import pandas as pd

from models import RoutingSolution, Scenario


def _pct_improvement(baseline: float, candidate: float) -> float:
    """Positive = candidate is better (shorter distance) than baseline."""
    if baseline == 0:
        return 0.0  # Why: an empty/degenerate scenario shouldn't produce a divide-by-zero
    return round((baseline - candidate) / baseline * 100, 2)


def evaluate_scenario(
    scenario: Scenario,
    solvers: List[Callable[[Scenario], RoutingSolution]],
) -> List[dict]:
    """Runs every solver on one scenario and returns one result row per solver."""
    rows = []
    for solve_fn in solvers:
        result = solve_fn(scenario)
        row = asdict(result)
        row.pop("routes")  # Why: routes aren't tabular KPI data, drop before DataFrame conversion
        row["seed"] = scenario.seed
        row["num_customers"] = len(scenario.customers)
        row["num_vehicles"] = scenario.num_vehicles
        rows.append(row)
    return rows


def run_evaluation(
    scenarios: List[Scenario],
    solvers: List[Callable[[Scenario], RoutingSolution]],
) -> pd.DataFrame:
    """Full sweep across all scenarios; one row per (scenario, solver) pair."""
    if not scenarios:
        raise ValueError("scenarios list is empty — nothing to evaluate")
    if not solvers:
        raise ValueError("solvers list is empty — nothing to compare against")

    all_rows = []
    for scenario in scenarios:
        all_rows.extend(evaluate_scenario(scenario, solvers))
    return pd.DataFrame(all_rows)


def summarize(results_df: pd.DataFrame, baseline_names: List[str], candidate_name: str) -> pd.DataFrame:
    """Per-seed comparison table: distance + feasibility for every baseline, plus the
    candidate's improvement % over EACH baseline separately. Multiple baselines let
    the summary show the candidate beat both a weak and a strong heuristic, which is
    a more credible claim than beating one arbitrary comparison point."""
    pivot = results_df.pivot(index="seed", columns="solver_name", values="total_distance")
    feasibility = results_df.pivot(index="seed", columns="solver_name", values="feasible")
    solve_time = results_df.pivot(index="seed", columns="solver_name", values="solve_time_seconds")

    summary = pd.DataFrame(index=pivot.index)
    summary[f"{candidate_name}_distance"] = pivot[candidate_name]
    summary[f"{candidate_name}_feasible"] = feasibility[candidate_name]
    summary[f"{candidate_name}_solve_time_s"] = solve_time[candidate_name]

    for baseline_name in baseline_names:
        summary[f"{baseline_name}_distance"] = pivot[baseline_name]
        summary[f"{baseline_name}_feasible"] = feasibility[baseline_name]

        # Why: only compute an improvement % when both solvers actually found a
        # feasible route — comparing against an infeasible result is meaningless.
        both_feasible = feasibility[baseline_name] & feasibility[candidate_name]
        summary[f"pct_improvement_vs_{baseline_name}"] = [
            _pct_improvement(b, c) if ok else None
            for b, c, ok in zip(pivot[baseline_name], pivot[candidate_name], both_feasible)
        ]
    return summary
