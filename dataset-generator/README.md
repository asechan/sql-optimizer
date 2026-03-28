# Dataset Generator — AI SQL Optimizer

Generates synthetic SQL queries with structural features and simulated execution times for ML model training.

## What It Does

1. **SQL Template Engine** (`sql_templates.py`) — Generates diverse, realistic SQL queries across 18 patterns:
   - Simple SELECT, WHERE, ORDER BY, LIMIT
   - Single and multi-table JOINs
   - Subqueries (IN-style)
   - GROUP BY, HAVING, DISTINCT
   - ORDER BY + LIMIT, JOIN + ORDER + LIMIT
   - CTEs (`WITH`), `EXISTS`, `UNION ALL`
   - `CASE WHEN`, window functions, correlated subqueries

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

# Recommended for hybrid training (larger OLTP mix)
python generate_dataset.py --num 50000 --seed 42 --out output/oltp_expanded.csv

# Custom size + reproducible seed
python generate_dataset.py --num 10000 --seed 42

# Custom output path
python generate_dataset.py --out ../ml-service/data/training.csv

# Generate TPC-H schema/load scripts (and optionally .tbl files if dbgen is installed)
python tpch_generator.py --scale 10 --output-dir output/tpch --skip-dbgen

# Execute TPC-H query files on PostgreSQL and capture real timings
python execute_tpch_queries.py \
   --dsn postgresql://postgres:postgres@localhost:5433/tpch \
   --queries-glob "output/tpch/queries/q*.sql" \
   --warmup-runs 1 \
   --runs-per-query 3 \
   --statement-timeout-ms 120000 \
   --out output/tpch_metrics.csv

# Merge synthetic + TPC-H benchmark metrics into one hybrid dataset
python merge_datasets.py \
   --synthetic output/sql_training_dataset.csv \
   --tpch output/tpch_metrics.csv \
   --out output/hybrid_training_dataset.csv
```

## Configuration

Edit `config.py` to adjust:
- `NUM_QUERIES` — default dataset size
- `TABLES` / `COLUMNS` — schema simulation
- `JOIN_PAIRS` — foreign-key relationships
- `PATTERN_WEIGHTS` — query pattern distribution

## Hybrid Dataset Workflow

Use this sequence for the hybrid approach:

1. Start benchmark PostgreSQL service:

```bash
docker compose --profile benchmark up -d tpch-postgres
```

2. Generate/load TPC-H data:

```bash
python tpch_generator.py --scale 10 --output-dir output/tpch
psql "postgresql://postgres:postgres@localhost:5433/tpch" -f output/tpch/create_tpch_schema.sql
psql "postgresql://postgres:postgres@localhost:5433/tpch" -f output/tpch/load_tpch_data.sql
```

`tpch_generator.py` also normalizes dbgen `.tbl` files into `.csv` files by stripping trailing delimiters so PostgreSQL `COPY` can load reliably.

3. Put TPC-H SQL files in `output/tpch/queries/` as `q1.sql`, `q2.sql`, ... `q22.sql`.

The generator creates placeholder stubs for `q1.sql`..`q22.sql` if they are missing.

4. Execute benchmark queries and export metrics:

```bash
python execute_tpch_queries.py --queries-glob "output/tpch/queries/q*.sql"
```

5. Merge with synthetic dataset:

```bash
python merge_datasets.py --out output/hybrid_training_dataset.csv
```

6. Train ML models against the merged file:

```bash
cd ../ml-service
python train_model.py --dataset ../dataset-generator/output/hybrid_training_dataset.csv
```

## Sample Output Stats

```
Total queries:     5,000
Slow queries:      ~5%
Avg exec time:     ~155 ms
Pattern coverage:  18 distinct query shapes
Features:          14 numeric columns
```
