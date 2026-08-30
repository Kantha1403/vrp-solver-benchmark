# Capacitated Vehicle Routing: Solver vs. Heuristic Benchmark

A minimal, complete decision-optimization portfolio piece: given a fleet of
capacity-constrained vehicles and a set of delivery customers, find the routing
that minimizes total distance — solved two ways and benchmarked against each other.

## Why this exists
Built to demonstrate the "Optimization & solvers (MILP/CP-SAT)" and "design robust
evaluation harnesses... define KPIs" requirements for an applied ML / decision
intelligence role, using a domain (logistics routing) adjacent to supply chain work.

## Structure
- `models.py` — shared `Scenario` / `RoutingSolution` data contracts
- `data_generation.py` — seeded synthetic CVRP scenario generator, incl. a forced-infeasible mode
- `distance_utils.py` — single source of truth for distances (float + CP-SAT-safe scaled int)
- `solver_cpsat.py` — OR-Tools CP-based routing solver (optimal/near-optimal)
- `baseline_heuristic.py` — naive nearest-neighbor baseline (the "no one would ship this" strawman)
- `savings_heuristic.py` — Clarke-Wright savings algorithm (the credible baseline a competent engineer would reach for)
- `evaluation.py` — scenario-sweep harness producing per-seed KPI comparison across all three methods
- `main.py` — runs an infeasibility guard check, then a 5-seed sweep, prints & saves results

## Run it
```bash
pip install ortools pandas
python main.py
```

## Design choices worth noting
- **OR-Tools' routing library, not raw CP-SAT.** It's still a CP + local-search
  engine under the hood, but it natively models the circuit and capacity
  constraints VRP needs — hand-rolling those in raw CP-SAT would spend the
  time budget on boilerplate instead of the evaluation harness.
- **Infeasibility is treated as a normal outcome, not an exception.** Both
  solvers return `feasible=False` cleanly; `main.py` runs a dedicated check
  that fabricates an over-demand scenario and asserts both solvers agree.
- **KPI comparison only scores scenarios where both solvers are feasible.**
  Comparing a feasible route's distance against an infeasible result's `0.0`
  would silently corrupt the improvement percentage.

## Results (5-seed sweep, 20 customers / 4 vehicles / capacity 50)
| Baseline | Avg. CP solver improvement |
|---|---|
| Nearest-Neighbor (naive) | ~25.7% shorter routes |
| Clarke-Wright Savings (classical, credible) | ~5.2% shorter routes |

The gap over the strong baseline is the number worth citing — it reflects genuine
solver value on top of an already-competent classical algorithm, not an inflated
comparison against a strawman. One scenario (seed 2) was correctly flagged
infeasible by all three independent methods (demand exceeded total fleet
capacity), showing the constraint-checking logic is consistent, not just the
happy path.

## Possible extensions (not built, noted for interview discussion)
- Time-window constraints (CVRPTW)
- Multi-depot variant
- Wrap `evaluate_scenario` as a Ray/Stable-Baselines environment step to compare
  against a learned dispatch policy
