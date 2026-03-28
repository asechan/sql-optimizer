#!/usr/bin/env python3
"""Execute TPC-H SQL queries on PostgreSQL and export model-ready metrics."""

from __future__ import annotations

import argparse
import glob
import re
import time
from pathlib import Path
from typing import Any

import pandas as pd
import psycopg

from features import FEATURE_COLUMNS, extract_features
from simulator import label_slow


def _natural_key(path_text: str) -> list[Any]:
    """Sort q1, q2, ... q10 numerically instead of lexicographically."""
    return [int(s) if s.isdigit() else s.lower() for s in re.split(r"(\d+)", path_text)]


def read_queries(query_glob: str) -> list[tuple[str, str]]:
    files = sorted(glob.glob(query_glob), key=_natural_key)
    if not files:
        raise FileNotFoundError(f"No query files found for glob: {query_glob}")

    queries: list[tuple[str, str]] = []
    for file_path in files:
        path = Path(file_path)
        query_id = path.stem
        sql = path.read_text(encoding="utf-8").strip()
        if not sql:
            continue
        queries.append((query_id, sql.rstrip(";")))

    if not queries:
        raise ValueError("Query files were found but all were empty")
    return queries


def _between(sql: str, start_kw: str, stop_words: list[str]) -> str:
    lowered = sql.lower()
    start = lowered.find(start_kw)
    if start == -1:
        return ""
    start += len(start_kw)
    end = len(sql)
    for word in stop_words:
        idx = lowered.find(word, start)
        if idx != -1:
            end = min(end, idx)
    return sql[start:end]


def _extract_tables(sql: str) -> list[str]:
    from_matches = re.findall(r"\bfrom\s+([a-zA-Z_][\w.]*)", sql, flags=re.IGNORECASE)
    join_matches = re.findall(r"\bjoin\s+([a-zA-Z_][\w.]*)", sql, flags=re.IGNORECASE)
    all_tables = []
    for table in from_matches + join_matches:
        cleaned = table.split(".")[-1]
        if cleaned not in all_tables:
            all_tables.append(cleaned)
    return all_tables


def _extract_columns_from_clause(clause: str) -> list[str]:
    cols = re.findall(r"\b([a-zA-Z_][\w]*)\.([a-zA-Z_][\w]*)\b", clause)
    col_names = []
    for _, col in cols:
        if col not in col_names:
            col_names.append(col)
    return col_names


def estimate_query_meta(sql: str, pattern: str) -> dict[str, Any]:
    where_clause = _between(sql, "where", ["group by", "having", "order by", "limit"])
    order_clause = _between(sql, "order by", ["limit", "offset"])
    group_clause = _between(sql, "group by", ["having", "order by", "limit"])

    joins = len(re.findall(r"\bjoin\b", sql, flags=re.IGNORECASE))
    where_ops = len(re.findall(r"\b(and|or)\b", where_clause, flags=re.IGNORECASE))
    where_conditions = 0 if not where_clause.strip() else max(1, where_ops + 1)
    subqueries = len(re.findall(r"\(\s*select\b", sql, flags=re.IGNORECASE))

    return {
        "sql": sql,
        "pattern": pattern,
        "tables": _extract_tables(sql),
        "joins": joins,
        "conditions": where_conditions,
        "subqueries": subqueries,
        "has_wildcard": bool(re.search(r"\bselect\s+\*", sql, flags=re.IGNORECASE)),
        "has_order_by": bool(order_clause.strip()),
        "has_group_by": bool(group_clause.strip()),
        "has_having": bool(re.search(r"\bhaving\b", sql, flags=re.IGNORECASE)),
        "has_distinct": bool(re.search(r"\bselect\s+distinct\b", sql, flags=re.IGNORECASE)),
        "has_limit": bool(re.search(r"\blimit\b", sql, flags=re.IGNORECASE)),
        "where_columns": _extract_columns_from_clause(where_clause),
        "order_by_columns": _extract_columns_from_clause(order_clause),
        "group_by_columns": _extract_columns_from_clause(group_clause),
    }


def explain_and_time(cur: psycopg.Cursor[Any], sql: str) -> tuple[float, float]:
    start = time.perf_counter()
    cur.execute(f"EXPLAIN (ANALYZE, FORMAT JSON) {sql}")
    result = cur.fetchone()
    wall_ms = (time.perf_counter() - start) * 1000.0

    if result is None:
        raise RuntimeError("No EXPLAIN result returned")

    payload = result[0]
    if isinstance(payload, str):
        raise RuntimeError("Unexpected JSON payload type from EXPLAIN")

    if isinstance(payload, list) and payload:
        parsed = payload[0]
    else:
        parsed = payload

    exec_ms = float(parsed.get("Execution Time", wall_ms))
    return exec_ms, wall_ms


def split_sql_statements(sql: str) -> list[str]:
    """Split semicolon-separated SQL text into executable statements."""
    return [stmt.strip() for stmt in sql.split(";") if stmt.strip()]


def pick_explain_target(statements: list[str]) -> int:
    """Pick the statement index to benchmark with EXPLAIN ANALYZE."""
    # Prefer the last SELECT/WITH statement if multiple statements are present.
    for idx in range(len(statements) - 1, -1, -1):
        lowered = statements[idx].lstrip().lower()
        if lowered.startswith("select") or lowered.startswith("with"):
            return idx
    return len(statements) - 1


def run_query_once(cur: psycopg.Cursor[Any], sql: str) -> tuple[float, float, str]:
    """Execute setup/teardown statements around an EXPLAIN ANALYZE target query."""
    statements = split_sql_statements(sql)
    if not statements:
        raise RuntimeError("No SQL statements to execute")

    target_idx = pick_explain_target(statements)
    setup = statements[:target_idx]
    target = statements[target_idx]
    teardown = statements[target_idx + 1 :]

    for stmt in setup:
        cur.execute(stmt)

    try:
        exec_ms, wall_ms = explain_and_time(cur, target)
    finally:
        for stmt in teardown:
            cur.execute(stmt)

    return exec_ms, wall_ms, target


def run_benchmark(
    dsn: str,
    query_glob: str,
    runs_per_query: int,
    warmup_runs: int,
    slow_threshold_ms: float,
    statement_timeout_ms: int,
    continue_on_error: bool,
) -> pd.DataFrame:
    queries = read_queries(query_glob)

    rows: list[dict[str, Any]] = []
    with psycopg.connect(dsn) as conn:
        with conn.cursor() as cur:
            if statement_timeout_ms > 0:
                cur.execute(f"SET statement_timeout = {int(statement_timeout_ms)}")

            for query_id, sql in queries:
                pattern = f"tpch_{query_id.lower()}"
                meta = estimate_query_meta(sql, pattern)
                features = extract_features(meta)

                # Warmup runs are excluded from exported metrics.
                for _ in range(max(0, warmup_runs)):
                    run_query_once(cur, sql)

                for run_num in range(1, runs_per_query + 1):
                    try:
                        exec_ms, wall_ms, benchmark_sql = run_query_once(cur, sql)
                        benchmark_meta = estimate_query_meta(benchmark_sql, pattern)
                        benchmark_features = extract_features(benchmark_meta)
                        row = {
                            "source": "tpch",
                            "query_id": query_id,
                            "run": run_num,
                            "sql": benchmark_sql,
                            "pattern": pattern,
                            **benchmark_features,
                            "execution_time_ms": round(exec_ms, 3),
                            "wall_time_ms": round(wall_ms, 3),
                            "is_slow": label_slow(exec_ms, threshold_ms=slow_threshold_ms),
                        }
                        rows.append(row)
                    except Exception as exc:  # pylint: disable=broad-exception-caught
                        if not continue_on_error:
                            raise
                        rows.append(
                            {
                                "source": "tpch",
                                "query_id": query_id,
                                "run": run_num,
                                "sql": sql,
                                "pattern": pattern,
                                **{col: features.get(col, 0) for col in FEATURE_COLUMNS},
                                "execution_time_ms": None,
                                "wall_time_ms": None,
                                "is_slow": None,
                                "error": str(exc),
                            }
                        )
                        conn.rollback()

    return pd.DataFrame(rows)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Execute TPC-H SQL files against PostgreSQL and export training rows"
    )
    parser.add_argument(
        "--dsn",
        default="postgresql://postgres:postgres@localhost:5433/tpch",
        help="PostgreSQL DSN",
    )
    parser.add_argument(
        "--queries-glob",
        default="output/tpch/queries/q*.sql",
        help="Glob pattern for SQL files (e.g. output/tpch/queries/q*.sql)",
    )
    parser.add_argument(
        "--runs-per-query",
        type=int,
        default=3,
        help="How many times to run each query",
    )
    parser.add_argument(
        "--warmup-runs",
        type=int,
        default=1,
        help="Warmup executions per query before timed runs",
    )
    parser.add_argument(
        "--slow-threshold-ms",
        type=float,
        default=500.0,
        help="Slow query threshold in milliseconds",
    )
    parser.add_argument(
        "--statement-timeout-ms",
        type=int,
        default=0,
        help="Optional PostgreSQL statement timeout in milliseconds (0 disables)",
    )
    parser.add_argument(
        "--out",
        default="output/tpch_metrics.csv",
        help="Output CSV path",
    )
    parser.add_argument(
        "--continue-on-error",
        action="store_true",
        help="Continue when a query fails and store the error in the output",
    )
    args = parser.parse_args()

    df = run_benchmark(
        dsn=args.dsn,
        query_glob=args.queries_glob,
        runs_per_query=args.runs_per_query,
        warmup_runs=args.warmup_runs,
        slow_threshold_ms=args.slow_threshold_ms,
        statement_timeout_ms=args.statement_timeout_ms,
        continue_on_error=args.continue_on_error,
    )

    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(out_path, index=False)

    total = len(df)
    ok = int(df["execution_time_ms"].notna().sum()) if "execution_time_ms" in df else 0
    slow_ratio = float(df["is_slow"].fillna(0).mean()) if "is_slow" in df else 0.0

    print(f"Rows written: {total}")
    print(f"Successful runs: {ok}")
    print(f"Slow ratio: {slow_ratio:.3f}")
    print(f"Output: {out_path}")


if __name__ == "__main__":
    main()
