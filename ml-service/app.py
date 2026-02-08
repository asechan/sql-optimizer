"""
FastAPI ML Prediction Service for the AI SQL Optimizer.

Endpoints:
  POST /predict     — Predict execution time and slow-query probability
  GET  /health      — Health check
  GET  /metrics     — Model evaluation metrics
  GET  /features    — Expected feature columns
"""

import json
import os
from contextlib import asynccontextmanager

import joblib
import numpy as np
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

# ── Model paths ───────────────────────────────────────────────────────────
MODELS_DIR = os.path.join(os.path.dirname(__file__), "models")

# Globals loaded at startup
regressor = None
classifier = None
scaler = None
feature_columns = None
metrics_data = None


# ── Lifespan: load models once on startup ─────────────────────────────────
@asynccontextmanager
async def lifespan(app: FastAPI):
    global regressor, classifier, scaler, feature_columns, metrics_data

    regressor = joblib.load(os.path.join(MODELS_DIR, "regressor.joblib"))
    classifier = joblib.load(os.path.join(MODELS_DIR, "classifier.joblib"))
    scaler = joblib.load(os.path.join(MODELS_DIR, "scaler.joblib"))

    with open(os.path.join(MODELS_DIR, "feature_columns.json")) as f:
        feature_columns = json.load(f)

    metrics_path = os.path.join(MODELS_DIR, "metrics.json")
    if os.path.exists(metrics_path):
        with open(metrics_path) as f:
            metrics_data = json.load(f)

    print(f"✓ Models loaded from {MODELS_DIR}")
    print(f"  Features: {feature_columns}")
    yield


# ── App ───────────────────────────────────────────────────────────────────
app = FastAPI(
    title="SQL Optimizer ML Service",
    description="Predicts SQL query execution time and slow-query probability",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


# ── Schemas ───────────────────────────────────────────────────────────────
class QueryFeatures(BaseModel):
    """Input features extracted from SQL parsing."""
    num_tables: int = Field(ge=0, description="Number of tables referenced")
    num_joins: int = Field(ge=0, description="Number of JOIN operations")
    num_conditions: int = Field(ge=0, description="Number of WHERE conditions")
    num_subqueries: int = Field(ge=0, description="Number of subqueries")
    has_wildcard: int = Field(ge=0, le=1, description="1 if SELECT *")
    has_order_by: int = Field(ge=0, le=1, description="1 if ORDER BY present")
    has_group_by: int = Field(ge=0, le=1, description="1 if GROUP BY present")
    has_having: int = Field(ge=0, le=1, description="1 if HAVING present")
    has_distinct: int = Field(ge=0, le=1, description="1 if DISTINCT present")
    has_limit: int = Field(ge=0, le=1, description="1 if LIMIT present")
    num_where_columns: int = Field(ge=0, description="Number of columns in WHERE")
    num_order_columns: int = Field(ge=0, description="Number of columns in ORDER BY")
    num_group_columns: int = Field(ge=0, description="Number of columns in GROUP BY")
    query_length: int = Field(ge=0, description="Character length of the SQL query")


class PredictionResponse(BaseModel):
    """ML prediction results."""
    predicted_time_ms: float = Field(description="Predicted execution time in ms")
    is_slow: bool = Field(description="Whether the query is predicted to be slow")
    slow_probability: float = Field(description="Probability of being slow (0-1)")
    confidence: str = Field(description="Confidence level: high, medium, or low")
    model_version: str = Field(default="1.0.0")


class HealthResponse(BaseModel):
    status: str
    models_loaded: bool
    feature_count: int


# ── Endpoints ─────────────────────────────────────────────────────────────
@app.post("/predict", response_model=PredictionResponse)
async def predict(features: QueryFeatures):
    """Predict execution time and slow-query probability from query features."""
    if regressor is None or classifier is None:
        raise HTTPException(status_code=503, detail="Models not loaded")

    # Build feature vector in the correct column order
    feature_vector = np.array([[
        features.num_tables,
        features.num_joins,
        features.num_conditions,
        features.num_subqueries,
        features.has_wildcard,
        features.has_order_by,
        features.has_group_by,
        features.has_having,
        features.has_distinct,
        features.has_limit,
        features.num_where_columns,
        features.num_order_columns,
        features.num_group_columns,
        features.query_length,
    ]])

    # Scale features
    feature_scaled = scaler.transform(feature_vector)

    # Predict
    predicted_time = float(regressor.predict(feature_scaled)[0])
    predicted_time = max(0.1, round(predicted_time, 2))  # Floor at 0.1ms

    slow_proba = float(classifier.predict_proba(feature_scaled)[0][1])
    is_slow = slow_proba >= 0.5

    # Confidence based on probability distance from decision boundary
    if slow_proba >= 0.85 or slow_proba <= 0.15:
        confidence = "high"
    elif slow_proba >= 0.7 or slow_proba <= 0.3:
        confidence = "medium"
    else:
        confidence = "low"

    return PredictionResponse(
        predicted_time_ms=predicted_time,
        is_slow=is_slow,
        slow_probability=round(slow_proba, 4),
        confidence=confidence,
        model_version="1.0.0",
    )


@app.get("/health", response_model=HealthResponse)
async def health():
    """Health check endpoint."""
    return HealthResponse(
        status="ok",
        models_loaded=regressor is not None and classifier is not None,
        feature_count=len(feature_columns) if feature_columns else 0,
    )


@app.get("/metrics")
async def get_metrics():
    """Return model evaluation metrics from training."""
    if metrics_data is None:
        raise HTTPException(status_code=404, detail="No metrics available")
    return metrics_data


@app.get("/features")
async def get_features():
    """Return the ordered list of expected feature columns."""
    if feature_columns is None:
        raise HTTPException(status_code=503, detail="Features not loaded")
    return {"features": feature_columns, "count": len(feature_columns)}
