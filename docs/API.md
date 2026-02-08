# API Reference

Complete API documentation for the AI SQL Query Optimizer.

---

## Backend API (Spring Boot — port 8080)

### `GET /api/health`

Health check endpoint.

**Response**

```json
{
  "status": "UP"
}
```

---

### `POST /api/analyze`

Analyze a SQL query — parse structure, predict performance, suggest indexes, and optimize.

**Request**

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `query` | string | ✅ | The SQL query to analyze |

```bash
curl -X POST http://localhost:8080/api/analyze \
  -H "Content-Type: application/json" \
  -d '{"query": "SELECT * FROM users WHERE age > 25 ORDER BY name"}'
```

**Response**

```json
{
  "predictedTime": 142,
  "slow": false,
  "slowProbability": 0.0823,
  "confidence": "high",
  "predictionSource": "ml",
  "suggestedIndex": "CREATE INDEX idx_users_age ON users (age);",
  "suggestedIndexes": [
    "CREATE INDEX idx_users_age ON users (age);",
    "CREATE INDEX idx_users_age_name ON users (age, name);"
  ],
  "optimizedQuery": "SELECT age, name FROM users WHERE age > 25 ORDER BY name;",
  "optimizationTips": [
    "Replace SELECT * with specific column names to reduce I/O and enable covering indexes.",
    "ORDER BY without LIMIT forces a full sort — add LIMIT if only top rows are needed."
  ],
  "queryFeatures": {
    "tables": ["users"],
    "joins": 0,
    "conditions": 1,
    "subqueries": 0,
    "hasWildcard": true,
    "hasOrderBy": true,
    "hasGroupBy": false,
    "hasHaving": false,
    "hasDistinct": false,
    "hasLimit": false,
    "whereColumns": ["age"],
    "orderByColumns": ["name"],
    "groupByColumns": [],
    "queryType": "SELECT"
  }
}
```

**Response Fields**

| Field | Type | Description |
|-------|------|-------------|
| `predictedTime` | integer | Predicted execution time in milliseconds |
| `slow` | boolean | Whether the query is predicted to be slow (>500ms) |
| `slowProbability` | float | Probability of being a slow query (0.0–1.0) |
| `confidence` | string | Prediction confidence: `high`, `medium`, or `low` |
| `predictionSource` | string | `ml` if ML service responded, `heuristic` if fallback was used |
| `suggestedIndex` | string | Primary index recommendation (or `-- No index suggestions`) |
| `suggestedIndexes` | string[] | All index recommendations |
| `optimizedQuery` | string | Rewritten query with optimizations applied |
| `optimizationTips` | string[] | Human-readable optimization suggestions |
| `queryFeatures` | object | Parsed structural features of the query |

**Error Responses**

| Status | Body | Cause |
|--------|------|-------|
| 400 | `{"error": "Query must not be empty"}` | Missing or blank query |
| 400 | `{"error": "Invalid SQL: ..."}` | JSqlParser could not parse the query |

---

## ML Service API (FastAPI — port 8000)

### `GET /health`

Health check endpoint.

**Response**

```json
{
  "status": "ok",
  "models_loaded": true,
  "feature_count": 14
}
```

---

### `POST /predict`

Predict execution time and slow-query probability from extracted query features.

**Request**

| Field | Type | Range | Description |
|-------|------|-------|-------------|
| `num_tables` | int | ≥ 0 | Number of tables referenced |
| `num_joins` | int | ≥ 0 | Number of JOIN operations |
| `num_conditions` | int | ≥ 0 | Number of WHERE conditions |
| `num_subqueries` | int | ≥ 0 | Number of subqueries |
| `has_wildcard` | int | 0–1 | 1 if `SELECT *` |
| `has_order_by` | int | 0–1 | 1 if ORDER BY present |
| `has_group_by` | int | 0–1 | 1 if GROUP BY present |
| `has_having` | int | 0–1 | 1 if HAVING present |
| `has_distinct` | int | 0–1 | 1 if DISTINCT present |
| `has_limit` | int | 0–1 | 1 if LIMIT present |
| `num_where_columns` | int | ≥ 0 | Number of columns in WHERE clause |
| `num_order_columns` | int | ≥ 0 | Number of columns in ORDER BY |
| `num_group_columns` | int | ≥ 0 | Number of columns in GROUP BY |
| `query_length` | int | ≥ 0 | Character length of the SQL query |

```bash
curl -X POST http://localhost:8000/predict \
  -H "Content-Type: application/json" \
  -d '{
    "num_tables": 3,
    "num_joins": 2,
    "num_conditions": 2,
    "num_subqueries": 0,
    "has_wildcard": 1,
    "has_order_by": 1,
    "has_group_by": 0,
    "has_having": 0,
    "has_distinct": 0,
    "has_limit": 0,
    "num_where_columns": 2,
    "num_order_columns": 1,
    "num_group_columns": 0,
    "query_length": 180
  }'
```

**Response**

```json
{
  "predicted_time_ms": 487.23,
  "is_slow": false,
  "slow_probability": 0.4312,
  "confidence": "medium",
  "model_version": "1.0.0"
}
```

| Field | Type | Description |
|-------|------|-------------|
| `predicted_time_ms` | float | Predicted execution time in ms (minimum 0.1) |
| `is_slow` | boolean | True if `slow_probability ≥ 0.5` |
| `slow_probability` | float | Probability of being slow (0.0–1.0) |
| `confidence` | string | `high` (≥0.85 or ≤0.15), `medium` (≥0.7 or ≤0.3), `low` |
| `model_version` | string | Model version string |

---

### `GET /metrics`

Return model evaluation metrics from training.

**Response**

```json
{
  "regression": {
    "r2": 0.8611,
    "mae": 39.92,
    "rmse": 73.49
  },
  "classification": {
    "accuracy": 0.978,
    "precision": 0.8235,
    "recall": 0.7636,
    "f1": 0.7925
  },
  "feature_importance": { "..." : "..." },
  "dataset_size": 5000,
  "train_size": 4000
}
```

---

### `GET /features`

Return the ordered list of expected feature columns.

**Response**

```json
{
  "features": [
    "num_tables", "num_joins", "num_conditions", "num_subqueries",
    "has_wildcard", "has_order_by", "has_group_by", "has_having",
    "has_distinct", "has_limit", "num_where_columns", "num_order_columns",
    "num_group_columns", "query_length"
  ],
  "count": 14
}
```

---

## Inter-Service Communication

```
React UI  ──► POST /api/analyze ──►  Spring Boot  ──► POST /predict ──►  FastAPI ML Service
   ▲                                      │
   └──────── JSON response ◄──────────────┘
```

The Spring Boot backend acts as an API gateway:
1. Receives the raw SQL from the React frontend
2. Parses it with JSqlParser and extracts features
3. Calls the ML service for prediction (falls back to heuristic if unavailable)
4. Assembles the full response with features, prediction, indexes, and optimization tips
