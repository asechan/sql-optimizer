#!/usr/bin/env python3
"""
train_model.py — Train ML models for SQL query performance prediction.

Trains two models on the dataset from Phase 4:
  1. Regression  — Predicts execution_time_ms (GradientBoostingRegressor)
  2. Classification — Predicts is_slow (GradientBoostingClassifier)

Outputs:
  models/regressor.joblib     — Execution time predictor
  models/classifier.joblib    — Slow-query classifier
  models/feature_columns.json — Ordered feature list
  models/metrics.json         — Evaluation metrics

Usage:
    python train_model.py
    python train_model.py --dataset ../dataset-generator/output/sql_training_dataset.csv
"""

import argparse
import json
import os
import sys

import joblib
import numpy as np
import pandas as pd
from sklearn.ensemble import GradientBoostingClassifier, GradientBoostingRegressor
from sklearn.metrics import (
    accuracy_score,
    f1_score,
    mean_absolute_error,
    mean_squared_error,
    precision_score,
    r2_score,
    recall_score,
)
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler


# ── Feature columns (must match dataset-generator/features.py) ───────────
FEATURE_COLUMNS = [
    "num_tables",
    "num_joins",
    "num_conditions",
    "num_subqueries",
    "has_wildcard",
    "has_order_by",
    "has_group_by",
    "has_having",
    "has_distinct",
    "has_limit",
    "num_where_columns",
    "num_order_columns",
    "num_group_columns",
    "query_length",
]

MODELS_DIR = os.path.join(os.path.dirname(__file__), "models")


def load_dataset(path: str) -> pd.DataFrame:
    """Load and validate the training dataset."""
    print(f"Loading dataset from {path}")
    df = pd.read_csv(path)
    print(f"  Rows: {len(df):,}  Columns: {list(df.columns)}")

    missing = [c for c in FEATURE_COLUMNS if c not in df.columns]
    if missing:
        raise ValueError(f"Missing feature columns: {missing}")
    if "execution_time_ms" not in df.columns:
        raise ValueError("Missing target column: execution_time_ms")
    if "is_slow" not in df.columns:
        raise ValueError("Missing target column: is_slow")

    return df


def train(dataset_path: str) -> dict:
    """Train both models and save artifacts."""
    df = load_dataset(dataset_path)

    X = df[FEATURE_COLUMNS].values
    y_reg = df["execution_time_ms"].values
    y_cls = df["is_slow"].values

    # Split
    X_train, X_test, y_reg_train, y_reg_test, y_cls_train, y_cls_test = (
        train_test_split(X, y_reg, y_cls, test_size=0.2, random_state=42)
    )

    print(f"\n  Train set: {len(X_train):,}   Test set: {len(X_test):,}")
    print(f"  Slow ratio (train): {y_cls_train.mean():.3f}")
    print(f"  Slow ratio (test):  {y_cls_test.mean():.3f}")

    # Scale features
    scaler = StandardScaler()
    X_train_scaled = scaler.fit_transform(X_train)
    X_test_scaled = scaler.transform(X_test)

    # ── Regression model ─────────────────────────────────────────────────
    print("\n══ Training Regression Model (GradientBoostingRegressor) ══")
    reg = GradientBoostingRegressor(
        n_estimators=200,
        max_depth=5,
        learning_rate=0.1,
        subsample=0.8,
        random_state=42,
    )
    reg.fit(X_train_scaled, y_reg_train)

    y_reg_pred = reg.predict(X_test_scaled)
    reg_metrics = {
        "r2": round(r2_score(y_reg_test, y_reg_pred), 4),
        "mae": round(mean_absolute_error(y_reg_test, y_reg_pred), 2),
        "rmse": round(np.sqrt(mean_squared_error(y_reg_test, y_reg_pred)), 2),
    }
    print(f"  R²:   {reg_metrics['r2']}")
    print(f"  MAE:  {reg_metrics['mae']} ms")
    print(f"  RMSE: {reg_metrics['rmse']} ms")

    # Feature importance
    importance = dict(zip(FEATURE_COLUMNS, reg.feature_importances_.round(4).tolist()))
    top_features = sorted(importance.items(), key=lambda x: x[1], reverse=True)[:5]
    print("  Top features:")
    for feat, imp in top_features:
        print(f"    {feat:25s} {imp:.4f}")

    # ── Classification model ─────────────────────────────────────────────
    print("\n══ Training Classification Model (GradientBoostingClassifier) ══")
    cls = GradientBoostingClassifier(
        n_estimators=150,
        max_depth=4,
        learning_rate=0.1,
        subsample=0.8,
        random_state=42,
    )
    cls.fit(X_train_scaled, y_cls_train)

    y_cls_pred = cls.predict(X_test_scaled)
    y_cls_proba = cls.predict_proba(X_test_scaled)[:, 1]
    cls_metrics = {
        "accuracy": round(accuracy_score(y_cls_test, y_cls_pred), 4),
        "precision": round(precision_score(y_cls_test, y_cls_pred, zero_division=0), 4),
        "recall": round(recall_score(y_cls_test, y_cls_pred, zero_division=0), 4),
        "f1": round(f1_score(y_cls_test, y_cls_pred, zero_division=0), 4),
    }
    print(f"  Accuracy:  {cls_metrics['accuracy']}")
    print(f"  Precision: {cls_metrics['precision']}")
    print(f"  Recall:    {cls_metrics['recall']}")
    print(f"  F1:        {cls_metrics['f1']}")

    # ── Save artifacts ───────────────────────────────────────────────────
    os.makedirs(MODELS_DIR, exist_ok=True)

    joblib.dump(reg, os.path.join(MODELS_DIR, "regressor.joblib"))
    joblib.dump(cls, os.path.join(MODELS_DIR, "classifier.joblib"))
    joblib.dump(scaler, os.path.join(MODELS_DIR, "scaler.joblib"))

    with open(os.path.join(MODELS_DIR, "feature_columns.json"), "w") as f:
        json.dump(FEATURE_COLUMNS, f, indent=2)

    all_metrics = {
        "regression": reg_metrics,
        "classification": cls_metrics,
        "feature_importance": importance,
        "dataset_size": len(df),
        "train_size": len(X_train),
        "test_size": len(X_test),
    }
    with open(os.path.join(MODELS_DIR, "metrics.json"), "w") as f:
        json.dump(all_metrics, f, indent=2)

    print(f"\n✓ Models saved to {MODELS_DIR}/")
    print(f"  regressor.joblib, classifier.joblib, scaler.joblib")
    print(f"  feature_columns.json, metrics.json")

    return all_metrics


def main():
    parser = argparse.ArgumentParser(description="Train SQL optimizer ML models")
    parser.add_argument(
        "--dataset",
        default=os.path.join(
            os.path.dirname(__file__),
            "..", "dataset-generator", "output", "sql_training_dataset.csv",
        ),
        help="Path to training CSV",
    )
    args = parser.parse_args()

    if not os.path.exists(args.dataset):
        print(f"Error: Dataset not found at {args.dataset}")
        sys.exit(1)

    train(args.dataset)


if __name__ == "__main__":
    main()
