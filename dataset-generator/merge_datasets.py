#!/usr/bin/env python3
"""Merge synthetic and TPC-H datasets into one training dataset."""

from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd

from features import FEATURE_COLUMNS
from simulator import label_slow


BASE_COLUMNS = [
    "sql",
    "pattern",
    "source",
    *FEATURE_COLUMNS,
    "execution_time_ms",
    "is_slow",
]


def ensure_columns(df: pd.DataFrame, source_name: str, slow_threshold_ms: float) -> pd.DataFrame:
    data = df.copy()

    if "source" not in data.columns:
        data["source"] = source_name

    if "is_slow" not in data.columns and "execution_time_ms" in data.columns:
        data["is_slow"] = data["execution_time_ms"].apply(
            lambda v: label_slow(float(v), threshold_ms=slow_threshold_ms)
            if pd.notna(v)
            else None
        )

    for col in FEATURE_COLUMNS:
        if col not in data.columns:
            data[col] = 0

    for col in BASE_COLUMNS:
        if col not in data.columns:
            data[col] = None

    return data


def clean_dataset(df: pd.DataFrame) -> pd.DataFrame:
    data = df.copy()
    data = data.dropna(subset=["sql", "execution_time_ms"])
    data["execution_time_ms"] = pd.to_numeric(data["execution_time_ms"], errors="coerce")
    data = data.dropna(subset=["execution_time_ms"])
    data = data[data["execution_time_ms"] > 0]

    for col in FEATURE_COLUMNS + ["is_slow"]:
        data[col] = pd.to_numeric(data[col], errors="coerce").fillna(0)

    data["is_slow"] = data["is_slow"].astype(int)
    return data


def maybe_sample(df: pd.DataFrame, limit: int | None, seed: int) -> pd.DataFrame:
    if limit is None or limit <= 0 or len(df) <= limit:
        return df
    return df.sample(n=limit, random_state=seed)


def upsample_to_target(df: pd.DataFrame, target_rows: int | None, seed: int) -> pd.DataFrame:
    if target_rows is None or target_rows <= 0:
        return df
    if len(df) == 0:
        return df
    if len(df) >= target_rows:
        return df.sample(n=target_rows, random_state=seed)
    return df.sample(n=target_rows, random_state=seed, replace=True)


def main() -> None:
    parser = argparse.ArgumentParser(description="Merge synthetic and TPC-H training datasets")
    parser.add_argument(
        "--synthetic",
        default="output/sql_training_dataset.csv",
        help="Path to synthetic dataset CSV",
    )
    parser.add_argument(
        "--tpch",
        default="output/tpch_metrics.csv",
        help="Path to TPC-H benchmark metrics CSV",
    )
    parser.add_argument(
        "--out",
        default="output/hybrid_training_dataset.csv",
        help="Output hybrid dataset CSV",
    )
    parser.add_argument(
        "--synthetic-limit",
        type=int,
        default=50000,
        help="Optional max rows from synthetic dataset",
    )
    parser.add_argument(
        "--tpch-target-rows",
        type=int,
        default=5000,
        help="Upsample TPC-H rows to this size for better representation",
    )
    parser.add_argument(
        "--slow-threshold-ms",
        type=float,
        default=500.0,
        help="Threshold used to derive is_slow when missing",
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=42,
        help="Random seed for sampling and shuffling",
    )
    args = parser.parse_args()

    synthetic_df = pd.read_csv(args.synthetic)
    tpch_df = pd.read_csv(args.tpch)

    synthetic_df = ensure_columns(synthetic_df, source_name="synthetic", slow_threshold_ms=args.slow_threshold_ms)
    tpch_df = ensure_columns(tpch_df, source_name="tpch", slow_threshold_ms=args.slow_threshold_ms)

    synthetic_df = clean_dataset(synthetic_df)
    tpch_df = clean_dataset(tpch_df)

    synthetic_df = maybe_sample(synthetic_df, args.synthetic_limit, args.seed)
    tpch_df = upsample_to_target(tpch_df, args.tpch_target_rows, args.seed)

    merged = pd.concat([synthetic_df, tpch_df], ignore_index=True)
    merged = merged.sample(frac=1.0, random_state=args.seed).reset_index(drop=True)

    final_columns = [c for c in BASE_COLUMNS if c in merged.columns]
    merged = merged[final_columns]

    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    merged.to_csv(out_path, index=False)

    print(f"Synthetic rows used: {len(synthetic_df):,}")
    print(f"TPC-H rows used:     {len(tpch_df):,}")
    print(f"Merged rows:         {len(merged):,}")
    print(f"Slow ratio:          {merged['is_slow'].mean():.3f}")
    print(f"Output:              {out_path}")


if __name__ == "__main__":
    main()
