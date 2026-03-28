"""Simulates query execution times for training data."""

import math
import random


def simulate_execution_time(features: dict, pattern: str) -> float:
    """Simulate a query execution time in milliseconds based on structural features."""
    # Base cost per table
    base = features.get("num_tables", 1) * random.uniform(15, 50)

    # Join cost
    num_joins = features.get("num_joins", 0)
    if num_joins > 0:
        base += num_joins * random.uniform(60, 180)
        # Extra penalty for multi-joins (plan complexity)
        if num_joins >= 2:
            base *= 1.0 + (num_joins - 1) * random.uniform(0.2, 0.5)

    # Subquery cost
    num_sub = features.get("num_subqueries", 0)
    if num_sub > 0:
        base += num_sub * random.uniform(150, 400)

    # WHERE filtering discount
    num_cond = features.get("num_conditions", 0)
    if num_cond > 0:
        base *= max(0.4, 1.0 - num_cond * random.uniform(0.05, 0.15))

    # SELECT * penalty
    if features.get("has_wildcard", 0):
        base *= random.uniform(1.1, 1.5)

    # ORDER BY without LIMIT — full sort
    if features.get("has_order_by", 0) and not features.get("has_limit", 0):
        base += random.uniform(80, 250)

    # GROUP BY
    if features.get("has_group_by", 0):
        num_gb = features.get("num_group_columns", 1)
        base += num_gb * random.uniform(40, 120)

    # HAVING
    if features.get("has_having", 0):
        base += random.uniform(20, 60)

    # DISTINCT
    if features.get("has_distinct", 0):
        base += random.uniform(30, 100)

    # LIMIT discount
    if features.get("has_limit", 0):
        base *= random.uniform(0.3, 0.7)

    # Query length as a complexity proxy
    qlen = features.get("query_length", 50)
    base += math.log1p(qlen) * random.uniform(0.5, 2.0)

    # Pattern-aware adjustments for advanced query constructs.
    if pattern == "select_cte":
        base += random.uniform(60, 180)
        base *= random.uniform(1.05, 1.2)
    elif pattern == "select_exists":
        base += random.uniform(90, 230)
        base *= random.uniform(1.08, 1.25)
    elif pattern == "select_union_all":
        base += random.uniform(80, 220)
        base *= random.uniform(1.05, 1.18)
    elif pattern == "select_case_when":
        base += random.uniform(30, 120)
    elif pattern == "select_window_fn":
        base += random.uniform(130, 320)
        base *= random.uniform(1.1, 1.3)
    elif pattern == "select_correlated_subquery":
        base += random.uniform(160, 420)
        base *= random.uniform(1.15, 1.45)
    elif pattern == "select_join_order_limit":
        base += random.uniform(70, 180)
    elif pattern == "select_order_limit":
        base += random.uniform(20, 80)

    # Gaussian noise
    noise = random.gauss(1.0, 0.15)
    base *= max(0.5, noise)

    return round(max(1.0, base), 2)


def label_slow(execution_time_ms: float, threshold_ms: float = 500.0) -> int:
    """Binary label: 1 if slow (above threshold), else 0."""
    return 1 if execution_time_ms > threshold_ms else 0
