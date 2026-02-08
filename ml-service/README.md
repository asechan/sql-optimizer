# ML Service — SQL Optimizer Prediction API

FastAPI service that predicts SQL query execution time and slow-query probability using trained scikit-learn models.

## Endpoints

| Method | Path       | Description                            |
|--------|------------|----------------------------------------|
| POST   | `/predict` | Predict execution time & slow flag     |
| GET    | `/health`  | Health check                           |
| GET    | `/metrics` | Model evaluation metrics from training |
| GET    | `/features`| Expected feature column names          |

## Quick Start

```bash
# Install dependencies
pip install -r requirements.txt

# Train models (uses dataset from Phase 4)
python train_model.py

# Start the server
uvicorn app:app --host 0.0.0.0 --port 8000 --reload
```

## Example Request

```bash
curl -X POST http://localhost:8000/predict \
  -H "Content-Type: application/json" \
  -d '{
    "num_tables": 2,
    "num_joins": 1,
    "num_conditions": 1,
    "num_subqueries": 0,
    "has_wildcard": 0,
    "has_order_by": 1,
    "has_group_by": 0,
    "has_having": 0,
    "has_distinct": 0,
    "has_limit": 0,
    "num_where_columns": 1,
    "num_order_columns": 1,
    "num_group_columns": 0,
    "query_length": 120
  }'
```

## Example Response

```json
{
  "predicted_time_ms": 213.45,
  "is_slow": false,
  "slow_probability": 0.1234,
  "confidence": "high",
  "model_version": "1.0.0"
}
```

## Model Details

- **Regression**: GradientBoostingRegressor — predicts execution time (ms)
- **Classification**: GradientBoostingClassifier — predicts slow query (>500ms)
- **Features**: 14 numeric features extracted from SQL structure
- **Training data**: 5,000 synthetic queries from the dataset generator
