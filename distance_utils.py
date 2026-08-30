"""Distance matrix computation.

Why a separate module: both the CP-SAT solver and the heuristic baseline need the
exact same distances to produce a fair KPI comparison. Computing it twice risks the
two solvers silently optimizing against different numbers.
"""
import math
from typing import List

from models import Customer


def build_distance_matrix(locations: List[Customer]) -> List[List[float]]:
    n = len(locations)
    matrix = [[0.0] * n for _ in range(n)]
    for i in range(n):
        for j in range(i + 1, n):
            dx = locations[i].x - locations[j].x
            dy = locations[i].y - locations[j].y
            dist = math.hypot(dx, dy)
            matrix[i][j] = dist
            matrix[j][i] = dist
    return matrix


def build_scaled_int_matrix(locations: List[Customer], scale: int = 1000) -> List[List[int]]:
    """CP-SAT requires integer costs. Scaling preserves ranking/precision instead of
    truncating to whole units, which would distort routes with many close-together
    customers."""
    float_matrix = build_distance_matrix(locations)
    return [[round(d * scale) for d in row] for row in float_matrix]
