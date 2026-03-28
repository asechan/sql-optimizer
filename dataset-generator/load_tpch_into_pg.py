#!/usr/bin/env python3
"""Load generated TPC-H CSV files into PostgreSQL."""

from __future__ import annotations

import argparse
from pathlib import Path

import psycopg

TABLES = [
    "region",
    "nation",
    "supplier",
    "customer",
    "part",
    "partsupp",
    "orders",
    "lineitem",
]


def main() -> None:
    parser = argparse.ArgumentParser(description="Load generated TPC-H CSV files into PostgreSQL")
    parser.add_argument("--dsn", default="postgresql://postgres:postgres@localhost:5433/tpch")
    parser.add_argument("--tpch-dir", default="output/tpch")
    args = parser.parse_args()

    tpch_dir = Path(args.tpch_dir).resolve()
    schema_sql = (tpch_dir / "create_tpch_schema.sql").read_text(encoding="utf-8")

    with psycopg.connect(args.dsn) as conn:
        with conn.cursor() as cur:
            cur.execute(schema_sql)
            cur.execute("TRUNCATE TABLE lineitem, orders, partsupp, part, customer, supplier, nation, region;")

            for table in TABLES:
                csv_path = tpch_dir / f"{table}.csv"
                if not csv_path.exists():
                    raise FileNotFoundError(f"Missing CSV file: {csv_path}")

                with cur.copy(f"COPY {table} FROM STDIN WITH (FORMAT csv, DELIMITER '|')") as copy:
                    with csv_path.open("r", encoding="utf-8") as f:
                        for line in f:
                            copy.write(line)

                cur.execute(f"SELECT count(*) FROM {table}")
                print(f"{table:10s} rows: {cur.fetchone()[0]}")

        conn.commit()

    print("load-complete")


if __name__ == "__main__":
    main()
