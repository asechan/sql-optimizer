"""
Execution Time Simulator — produces realistic-looking query execution
times using a formula that mirrors real-world cost factors, plus noise.

The simulated times serve as training labels for the ML model.
Real latency depends on data volume, hardware, indexing, etc. — this
simulator captures the *structural* cost relationships so the model
learns which query shapes are expensive.
"""

import math
import random


def simulate_execution_time(features: dict, pattern: str) -> float:
    """
    Simulate a query execution time in milliseconds.

    Factors that increase cost:
      - Number of tables (full-scan baseline per table)
      - Number of joins (nested-loop join cost)
      - Subqueries (correlated subquery penalty)
      - SELECT * (extra I/O for wide rows)
      - ORDER BY without LIMIT (full sort)
      - GROUP BY / HAVING (hash-aggregate cost)
      - DISTINCT (dedup cost)
      - Missing LIMIT (unbounded result set)

    Factors that decrease cost:
      - WHERE conditions (filter early)
      - LIMIT (cap output size)
    """

    # Base cost per table (simulating sequence scan)
    base = features.get("num_tables", 1) * random.uniform(15, 50)

    # Join cost scales super-linearly
    num_joins = features.get("num_joins", 0)
    if num_joins > 0:
        base += num_joins * random.uniform(60, 180)
        # Extra penalty for multi-joins (plan complexity)
        if num_joins >= 2:
            base *= 1.0 + (num_joins - 1) * random.uniform(0.2, 0.5)

    # Subquery cost (each may trigger re-execution)
    num_sub = features.get("num_subqueries", 0)
    if num_sub > 0:
        base += num_sub * random.uniform(150, 400)

    # WHERE reduces rows but adds evaluation cost
    num_cond = features.get("num_conditions", 0)
    if num_cond > 0:
        # Conditions help — discount
        base *= max(0.4, 1.0 - num_cond * random.uniform(0.05, 0.15))

    # SELECT * penalty
    if features.get("has_wildcard", 0):
        base *= random.uniform(1.1, 1.5)

    # ORDER BY without LIMIT — full sort
    if features.get("has_order_by", 0) and not features.get("has_limit", 0):
        base += random.uniform(80, 250)

    # GROUP BY cost
    if features.get("has_group_by", 0):
        num_gb = features.get("num_group_columns", 1)
        base += num_gb * random.uniform(40, 120)

    # HAVING — additional filter on aggregates
    if features.get("has_having", 0):
        base += random.uniform(20, 60)

    # DISTINCT — dedup overhead
    if features.get("has_distinct", 0):
        base += random.uniform(30, 100)

    # LIMIT discount — caps result processing
    if features.get("has_limit", 0):
        base *= random.uniform(0.3, 0.7)

    # Query length as a mild proxy for complexity
    qlen = features.get("query_length", 50)
    base += math.log1p(qlen) * random.uniform(0.5, 2.0)

    # Add Gaussian noise ±15 %
    noise = random.gauss(1.0, 0.15)
    base *= max(0.5, noise)

    # Floor at 1 ms
    return round(max(1.0, base), 2)


def label_slow(execution_time_ms: float, threshold_ms: float = 500.0) -> int:
    """Binary label: 1 if slow (above threshold), else 0."""
    return 1 if execution_time_ms > threshold_ms else 0
