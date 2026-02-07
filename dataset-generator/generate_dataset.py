#!/usr/bin/env python3
"""
generate_dataset.py — Main entry point for the SQL training-dataset generator.

Generates a CSV of synthetic SQL queries with extracted features and
simulated execution times, ready for ML model training in Phase 5.

Usage:
    python generate_dataset.py                      # defaults from config.py
    python generate_dataset.py --num 10000           # override count
    python generate_dataset.py --out my_dataset.csv  # custom output path
    python generate_dataset.py --seed 42             # reproducible
"""

import argparse
import os
import random
import sys
import time

import numpy as np
import pandas as pd

from config import NUM_QUERIES, PATTERN_WEIGHTS, OUTPUT_DIR, OUTPUT_FILE
from sql_templates import GENERATORS
from features import extract_features, FEATURE_COLUMNS
from simulator import simulate_execution_time, label_slow


def build_weighted_pattern_list() -> list[str]:
    """Expand pattern weights into a selection list for random.choice."""
    pool: list[str] = []
    for pattern, weight in PATTERN_WEIGHTS.items():
        pool.extend([pattern] * weight)
    return pool


def generate_single(pattern: str) -> dict:
    """Generate one query record: SQL + features + simulated timing."""
    generator = GENERATORS[pattern]
    meta = generator()

    feats = extract_features(meta)
    exec_time = simulate_execution_time(feats, pattern)
    is_slow = label_slow(exec_time)

    record = {
        "sql": meta["sql"],
        "pattern": meta["pattern"],
        **feats,
        "execution_time_ms": exec_time,
        "is_slow": is_slow,
    }
    return record


def generate_dataset(num_queries: int, seed: int | None = None) -> pd.DataFrame:
    """Generate the full dataset as a DataFrame."""
    if seed is not None:
        random.seed(seed)
        np.random.seed(seed)

    pattern_pool = build_weighted_pattern_list()
    records: list[dict] = []

    for i in range(num_queries):
        pattern = random.choice(pattern_pool)
        record = generate_single(pattern)
        records.append(record)

        if (i + 1) % 1000 == 0:
            print(f"  Generated {i + 1}/{num_queries} queries...")

    df = pd.DataFrame(records)

    # Reorder columns for readability
    col_order = (
        ["sql", "pattern"]
        + FEATURE_COLUMNS
        + ["execution_time_ms", "is_slow"]
    )
    df = df[[c for c in col_order if c in df.columns]]

    return df


def print_summary(df: pd.DataFrame) -> None:
    """Print dataset statistics."""
    print("\n═══ Dataset Summary ══════════════════════════════════════")
    print(f"  Total queries:     {len(df):,}")
    print(f"  Slow queries:      {df['is_slow'].sum():,}  "
          f"({df['is_slow'].mean() * 100:.1f}%)")
    print(f"  Avg exec time:     {df['execution_time_ms'].mean():.1f} ms")
    print(f"  Median exec time:  {df['execution_time_ms'].median():.1f} ms")
    print(f"  Max exec time:     {df['execution_time_ms'].max():.1f} ms")
    print(f"  Min exec time:     {df['execution_time_ms'].min():.1f} ms")
    print()
    print("  Pattern distribution:")
    for pattern, count in df["pattern"].value_counts().items():
        print(f"    {pattern:25s} {count:5d}  ({count / len(df) * 100:5.1f}%)")
    print()
    print("  Feature stats:")
    for col in FEATURE_COLUMNS:
        print(f"    {col:22s}  mean={df[col].mean():7.2f}  "
              f"min={df[col].min()}  max={df[col].max()}")
    print("══════════════════════════════════════════════════════════\n")


def main():
    parser = argparse.ArgumentParser(
        description="Generate a synthetic SQL training dataset for the AI SQL Optimizer."
    )
    parser.add_argument(
        "--num", type=int, default=NUM_QUERIES,
        help=f"Number of queries to generate (default: {NUM_QUERIES})"
    )
    parser.add_argument(
        "--out", type=str, default=None,
        help=f"Output CSV path (default: {OUTPUT_DIR}/{OUTPUT_FILE})"
    )
    parser.add_argument(
        "--seed", type=int, default=None,
        help="Random seed for reproducibility"
    )
    args = parser.parse_args()

    out_path = args.out or os.path.join(OUTPUT_DIR, OUTPUT_FILE)
    os.makedirs(os.path.dirname(out_path) or ".", exist_ok=True)

    print(f"\n🔧 Generating {args.num:,} synthetic SQL queries...")
    start = time.time()

    df = generate_dataset(args.num, seed=args.seed)

    elapsed = time.time() - start
    print(f"✅ Generated in {elapsed:.1f}s")

    df.to_csv(out_path, index=False)
    print(f"💾 Saved to {out_path}  ({os.path.getsize(out_path) / 1024:.0f} KB)")

    print_summary(df)


if __name__ == "__main__":
    main()
