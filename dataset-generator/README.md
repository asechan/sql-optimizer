# Dataset Generator — AI SQL Optimizer

Generates synthetic SQL queries with structural features and simulated execution times for ML model training.

## What It Does

1. **SQL Template Engine** (`sql_templates.py`) — Generates diverse, realistic SQL queries across 10 patterns:
   - Simple SELECT, WHERE, ORDER BY, LIMIT
   - Single and multi-table JOINs
   - Subqueries (IN-style)
   - GROUP BY, HAVING, DISTINCT

2. **Feature Extraction** (`features.py`) — Extracts 14 numeric features per query:
   - `num_tables`, `num_joins`, `num_conditions`, `num_subqueries`
   - `has_wildcard`, `has_order_by`, `has_group_by`, `has_having`, `has_distinct`, `has_limit`
   - `num_where_columns`, `num_order_columns`, `num_group_columns`, `query_length`

3. **Execution Simulator** (`simulator.py`) — Models realistic execution costs:
   - Base cost per table, join penalty, subquery overhead
   - Discounts for WHERE filters and LIMIT
   - Gaussian noise for realism
   - Binary `is_slow` label (threshold: 500 ms)

## Output

CSV file with columns:

| Column | Description |
|--------|-------------|
| `sql` | The generated SQL query |
| `pattern` | Query pattern type |
| `num_tables` .. `query_length` | 14 numeric features |
| `execution_time_ms` | Simulated execution time |
| `is_slow` | Binary label (1 = slow) |

## Usage

```bash
# Install dependencies
pip install -r requirements.txt

# Generate default dataset (5,000 queries)
python generate_dataset.py

# Custom size + reproducible seed
python generate_dataset.py --num 10000 --seed 42

# Custom output path
python generate_dataset.py --out ../ml-service/data/training.csv
```

## Configuration

Edit `config.py` to adjust:
- `NUM_QUERIES` — default dataset size
- `TABLES` / `COLUMNS` — schema simulation
- `JOIN_PAIRS` — foreign-key relationships
- `PATTERN_WEIGHTS` — query pattern distribution

## Sample Output Stats

```
Total queries:     5,000
Slow queries:      ~5%
Avg exec time:     ~155 ms
Pattern coverage:  10 distinct query shapes
Features:          14 numeric columns
```
