"""Entry point: generate scenarios, run both solvers, print the KPI comparison.

Usage: python main.py
"""
import sys

from data_generation import generate_scenario, generate_scenario_batch
from baseline_heuristic import solve_cvrp_nearest_neighbor
from savings_heuristic import solve_cvrp_savings
from solver_cpsat import solve_cvrp
from evaluation import run_evaluation, summarize

BASELINE_NAMES = ["Nearest-Neighbor Heuristic", "Clarke-Wright Savings"]
CANDIDATE_NAME = "OR-Tools CP Routing"


def run_infeasibility_check() -> bool:
    """Sanity check: both solvers must report infeasible=False cleanly, not crash,
    when demand exceeds fleet capacity. This is the defensive-coding proof point,
    not just a happy-path demo."""
    scenario = generate_scenario(seed=999, num_customers=5, num_vehicles=1,
                                  vehicle_capacity=20, force_infeasible=True)
    heuristic_result = solve_cvrp_nearest_neighbor(scenario)
    savings_result = solve_cvrp_savings(scenario)
    solver_result = solve_cvrp(scenario, time_limit_seconds=5)

    ok = (not heuristic_result.feasible) and (not savings_result.feasible) and (not solver_result.feasible)
    status = "PASS" if ok else "FAIL"
    print(f"[Infeasibility handling check] {status}")
    return ok


def main():
    print("Running infeasibility guard check...")
    if not run_infeasibility_check():
        print("WARNING: infeasibility was not detected correctly by one or both solvers.")

    print("\nGenerating scenario sweep (5 seeds, 20 customers, 4 vehicles, capacity 50)...")
    seeds = [1, 2, 3, 4, 5]
    scenarios = generate_scenario_batch(seeds, num_customers=20, num_vehicles=4, vehicle_capacity=50)

    solvers = [
        solve_cvrp_nearest_neighbor,
        solve_cvrp_savings,
        lambda s: solve_cvrp(s, time_limit_seconds=10),
    ]

    print("Solving with all three methods (this can take up to ~10s per scenario for CP)...")
    results_df = run_evaluation(scenarios, solvers)
    summary_df = summarize(results_df, BASELINE_NAMES, CANDIDATE_NAME)

    pd_options_set = False
    try:
        import pandas as pd
        pd.set_option("display.width", 120)
        pd_options_set = True
    except ImportError:
        pass

    print("\n=== Per-scenario KPI comparison ===")
    print(summary_df.to_string())

    for baseline_name in BASELINE_NAMES:
        col = f"pct_improvement_vs_{baseline_name}"
        avg_improvement = summary_df[col].dropna().mean()
        if avg_improvement == avg_improvement:  # not NaN
            print(f"\nAverage distance improvement of {CANDIDATE_NAME} over {baseline_name}: "
                  f"{avg_improvement:.2f}%")
        else:
            print(f"\nAverage improvement over {baseline_name}: N/A (no scenario had both solvers feasible)")

    summary_df.to_csv("evaluation_results.csv")
    print("\nSaved full results to evaluation_results.csv")


if __name__ == "__main__":
    sys.exit(main())
