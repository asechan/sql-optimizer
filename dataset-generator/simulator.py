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

    # Gaussian noise
    noise = random.gauss(1.0, 0.15)
    base *= max(0.5, noise)

    return round(max(1.0, base), 2)


def label_slow(execution_time_ms: float, threshold_ms: float = 500.0) -> int:
    """Binary label: 1 if slow (above threshold), else 0."""
    return 1 if execution_time_ms > threshold_ms else 0
