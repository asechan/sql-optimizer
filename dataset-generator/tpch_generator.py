#!/usr/bin/env python3
"""Generate TPC-H data files and PostgreSQL load scripts."""

from __future__ import annotations

import argparse
import re
import shutil
import subprocess
from pathlib import Path

TPCH_TABLES = [
    "region",
    "nation",
    "supplier",
    "customer",
    "part",
    "partsupp",
    "orders",
    "lineitem",
]

TPCH_QUERY_COUNT = 22

TPCH_SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS region (
    r_regionkey INTEGER PRIMARY KEY,
    r_name CHAR(25) NOT NULL,
    r_comment VARCHAR(152)
);

CREATE TABLE IF NOT EXISTS nation (
    n_nationkey INTEGER PRIMARY KEY,
    n_name CHAR(25) NOT NULL,
    n_regionkey INTEGER NOT NULL,
    n_comment VARCHAR(152)
);

CREATE TABLE IF NOT EXISTS supplier (
    s_suppkey INTEGER PRIMARY KEY,
    s_name CHAR(25) NOT NULL,
    s_address VARCHAR(40) NOT NULL,
    s_nationkey INTEGER NOT NULL,
    s_phone CHAR(15) NOT NULL,
    s_acctbal NUMERIC(15,2) NOT NULL,
    s_comment VARCHAR(101) NOT NULL
);

CREATE TABLE IF NOT EXISTS customer (
    c_custkey INTEGER PRIMARY KEY,
    c_name VARCHAR(25) NOT NULL,
    c_address VARCHAR(40) NOT NULL,
    c_nationkey INTEGER NOT NULL,
    c_phone CHAR(15) NOT NULL,
    c_acctbal NUMERIC(15,2) NOT NULL,
    c_mktsegment CHAR(10) NOT NULL,
    c_comment VARCHAR(117) NOT NULL
);

CREATE TABLE IF NOT EXISTS part (
    p_partkey INTEGER PRIMARY KEY,
    p_name VARCHAR(55) NOT NULL,
    p_mfgr CHAR(25) NOT NULL,
    p_brand CHAR(10) NOT NULL,
    p_type VARCHAR(25) NOT NULL,
    p_size INTEGER NOT NULL,
    p_container CHAR(10) NOT NULL,
    p_retailprice NUMERIC(15,2) NOT NULL,
    p_comment VARCHAR(23) NOT NULL
);

CREATE TABLE IF NOT EXISTS partsupp (
    ps_partkey INTEGER NOT NULL,
    ps_suppkey INTEGER NOT NULL,
    ps_availqty INTEGER NOT NULL,
    ps_supplycost NUMERIC(15,2) NOT NULL,
    ps_comment VARCHAR(199) NOT NULL,
    PRIMARY KEY (ps_partkey, ps_suppkey)
);

CREATE TABLE IF NOT EXISTS orders (
    o_orderkey BIGINT PRIMARY KEY,
    o_custkey INTEGER NOT NULL,
    o_orderstatus CHAR(1) NOT NULL,
    o_totalprice NUMERIC(15,2) NOT NULL,
    o_orderdate DATE NOT NULL,
    o_orderpriority CHAR(15) NOT NULL,
    o_clerk CHAR(15) NOT NULL,
    o_shippriority INTEGER NOT NULL,
    o_comment VARCHAR(79) NOT NULL
);

CREATE TABLE IF NOT EXISTS lineitem (
    l_orderkey BIGINT NOT NULL,
    l_partkey INTEGER NOT NULL,
    l_suppkey INTEGER NOT NULL,
    l_linenumber INTEGER NOT NULL,
    l_quantity NUMERIC(15,2) NOT NULL,
    l_extendedprice NUMERIC(15,2) NOT NULL,
    l_discount NUMERIC(15,2) NOT NULL,
    l_tax NUMERIC(15,2) NOT NULL,
    l_returnflag CHAR(1) NOT NULL,
    l_linestatus CHAR(1) NOT NULL,
    l_shipdate DATE NOT NULL,
    l_commitdate DATE NOT NULL,
    l_receiptdate DATE NOT NULL,
    l_shipinstruct CHAR(25) NOT NULL,
    l_shipmode CHAR(10) NOT NULL,
    l_comment VARCHAR(44) NOT NULL,
    PRIMARY KEY (l_orderkey, l_linenumber)
);
""".strip()


def _q_path(path: Path) -> str:
    """Quote filesystem paths for SQL string literals."""
    return path.as_posix().replace("'", "''")


def build_copy_sql(data_dir: Path) -> str:
    lines = [
        "TRUNCATE TABLE lineitem, orders, partsupp, part, customer, supplier, nation, region;",
    ]
    for table in TPCH_TABLES:
        csv_path = (data_dir / f"{table}.csv").resolve()
        lines.append(
            f"COPY {table} FROM '{_q_path(csv_path)}' WITH (FORMAT csv, DELIMITER '|');"
        )
    return "\n".join(lines)


def ensure_dbgen_assets(dbgen_bin: str, output_dir: Path) -> None:
    """Copy required dbgen assets into output_dir when missing."""
    dbgen_dir = Path(dbgen_bin).resolve().parent
    required = ["dists.dss"]

    for asset in required:
        src = dbgen_dir / asset
        dst = output_dir / asset
        if dst.exists():
            continue
        if not src.exists():
            raise RuntimeError(f"Required dbgen asset not found: {src}")
        shutil.copy2(src, dst)


def write_sql_scripts(output_dir: Path) -> tuple[Path, Path]:
    schema_path = output_dir / "create_tpch_schema.sql"
    load_path = output_dir / "load_tpch_data.sql"

    schema_path.write_text(TPCH_SCHEMA_SQL + "\n", encoding="utf-8")
    load_path.write_text(build_copy_sql(output_dir) + "\n", encoding="utf-8")

    return schema_path, load_path


def normalize_tbl_files(output_dir: Path) -> tuple[list[str], list[str]]:
    """Convert dbgen .tbl files to delimiter-clean .csv files for PostgreSQL COPY."""
    created_csv: list[str] = []
    missing_tbl: list[str] = []

    for table in TPCH_TABLES:
        tbl_path = output_dir / f"{table}.tbl"
        csv_path = output_dir / f"{table}.csv"

        if not tbl_path.exists():
            missing_tbl.append(tbl_path.name)
            continue

        with tbl_path.open("r", encoding="utf-8", errors="ignore") as src, csv_path.open(
            "w", encoding="utf-8"
        ) as dst:
            for line in src:
                stripped = line.rstrip("\n")
                if stripped.endswith("|"):
                    stripped = stripped[:-1]
                dst.write(stripped + "\n")

        created_csv.append(csv_path.name)

    return created_csv, missing_tbl


def write_query_stubs(output_dir: Path) -> Path:
    """Create q1..q22 SQL placeholders when benchmark query files are absent."""
    query_dir = output_dir / "queries"
    query_dir.mkdir(parents=True, exist_ok=True)

    for idx in range(1, TPCH_QUERY_COUNT + 1):
        q_path = query_dir / f"q{idx}.sql"
        if q_path.exists():
            continue
        q_path.write_text(
            "\n".join(
                [
                    f"-- TPC-H Query {idx}",
                    "-- Paste the official PostgreSQL-compatible TPC-H SQL here.",
                    "-- This placeholder is created by tpch_generator.py.",
                    "SELECT 1;",
                ]
            )
            + "\n",
            encoding="utf-8",
        )

    return query_dir


def normalize_qgen_sql_for_postgres(sql_text: str) -> str:
    """Apply conservative rewrites for qgen output to run on PostgreSQL."""
    lines = []
    for raw in sql_text.splitlines():
        line = raw.rstrip()
        stripped = line.strip().lower()
        # qgen banner comment is not needed in exported SQL files.
        if stripped == "-- using default substitutions":
            continue
        # qgen appends Oracle compatibility rownum filters; we'll convert later.
        if stripped == "where rownum <= -1;":
            continue
        lines.append(line)

    sql = "\n".join(lines)
    # Convert interval literals like: interval '90' day (3) -> interval '90 day'
    sql = re.sub(
        r"interval\s+'(\d+)'\s+day\s*\(\d+\)",
        r"interval '\1 day'",
        sql,
        flags=re.IGNORECASE,
    )
    sql = re.sub(
        r"interval\s+'(\d+)'\s+month\s*\(\d+\)",
        r"interval '\1 month'",
        sql,
        flags=re.IGNORECASE,
    )

    # Convert trailing Oracle rownum limit syntax to PostgreSQL LIMIT.
    # Pattern typically appears as:
    #   ...
    #   order by ...;
    #   where rownum <= 100;
    sql = re.sub(
        r";\s*where\s+rownum\s*<=\s*(\d+)\s*;\s*$",
        r"\nlimit \1;",
        sql,
        flags=re.IGNORECASE | re.DOTALL,
    )

    sql = sql.strip()
    return sql


def generate_queries_with_qgen(qgen_bin: str, scale_factor: float, output_dir: Path) -> tuple[Path, int]:
    """Generate official TPC-H q1..q22 SQL files using qgen."""
    qgen_path = Path(qgen_bin).resolve()
    if not qgen_path.exists():
        raise RuntimeError(f"qgen binary not found: {qgen_path}")

    qgen_dir = qgen_path.parent
    templates_dir = qgen_dir / "queries"
    if not templates_dir.exists():
        raise RuntimeError(f"qgen templates directory not found: {templates_dir}")

    query_dir = output_dir / "queries"
    query_dir.mkdir(parents=True, exist_ok=True)

    generated = 0
    qgen_scale = scale_factor if scale_factor >= 1 else 1
    for idx in range(1, TPCH_QUERY_COUNT + 1):
        out_path = query_dir / f"q{idx}.sql"
        cmd = [str(qgen_path), "-b", "../dists.dss", "-d", "-s", str(qgen_scale), str(idx)]
        result = subprocess.run(
            cmd,
            cwd=templates_dir,
            check=True,
            capture_output=True,
            text=True,
        )
        sql_text = normalize_qgen_sql_for_postgres(result.stdout.strip())
        if not sql_text:
            raise RuntimeError(f"qgen produced empty SQL for query {idx}")
        out_path.write_text(sql_text + "\n", encoding="utf-8")
        generated += 1

    return query_dir, generated


def run_dbgen(dbgen_bin: str, scale_factor: float, output_dir: Path) -> None:
    if not shutil.which(dbgen_bin):
        raise RuntimeError(
            f"dbgen executable '{dbgen_bin}' was not found in PATH. "
            "Install tpch-dbgen first or pass --skip-dbgen to only emit SQL scripts."
        )

    output_dir.mkdir(parents=True, exist_ok=True)
    ensure_dbgen_assets(dbgen_bin, output_dir)

    cmd = [dbgen_bin, "-f", "-s", str(scale_factor)]
    print(f"Running: {' '.join(cmd)} in {output_dir}")
    subprocess.run(cmd, cwd=output_dir, check=True)


def validate_generated_files(output_dir: Path) -> list[str]:
    missing = []
    for table in TPCH_TABLES:
        path = output_dir / f"{table}.tbl"
        if not path.exists():
            missing.append(path.name)
    return missing


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate TPC-H data and PostgreSQL load scripts")
    parser.add_argument(
        "--scale",
        type=float,
        default=1.0,
        help="TPC-H scale factor for dbgen (default: 1.0)",
    )
    parser.add_argument(
        "--output-dir",
        default="output/tpch",
        help="Directory for generated .tbl files and SQL scripts",
    )
    parser.add_argument(
        "--dbgen-bin",
        default="dbgen",
        help="Path or name of dbgen executable",
    )
    parser.add_argument(
        "--qgen-bin",
        default=None,
        help="Path or name of qgen executable (default: sibling of dbgen-bin)",
    )
    parser.add_argument(
        "--skip-dbgen",
        action="store_true",
        help="Only generate create/load SQL scripts, skip dbgen execution",
    )
    parser.add_argument(
        "--skip-qgen",
        action="store_true",
        help="Keep placeholder q1..q22 stubs instead of generating real queries with qgen",
    )
    args = parser.parse_args()

    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    if not args.skip_dbgen:
        run_dbgen(args.dbgen_bin, args.scale, output_dir)
        missing_files = validate_generated_files(output_dir)
        if missing_files:
            raise RuntimeError(
                "dbgen finished but required files are missing: " + ", ".join(missing_files)
            )

    csv_files, missing_tbl = normalize_tbl_files(output_dir)

    schema_path, load_path = write_sql_scripts(output_dir)
    query_stub_dir = write_query_stubs(output_dir)

    if not args.skip_qgen:
        resolved_qgen = args.qgen_bin
        if not resolved_qgen:
            resolved_qgen = str(Path(args.dbgen_bin).resolve().with_name("qgen"))
        try:
            query_stub_dir, generated_count = generate_queries_with_qgen(
                qgen_bin=resolved_qgen,
                scale_factor=args.scale,
                output_dir=output_dir,
            )
            print(f"Generated query files via qgen: {generated_count}")
        except Exception as exc:  # pylint: disable=broad-exception-caught
            print(f"qgen generation failed, keeping stubs: {exc}")

    print(f"Schema SQL: {schema_path}")
    print(f"Load SQL:   {load_path}")
    print(f"Query SQL directory: {query_stub_dir}")
    if csv_files:
        print(f"Generated normalized CSV files: {len(csv_files)}")
    if missing_tbl and args.skip_dbgen:
        print(
            "No .tbl files found for normalization. "
            "After adding .tbl files, rerun this script to produce .csv load files."
        )
    if args.skip_dbgen:
        print("Skipped dbgen. Provide .tbl files in the output directory before loading.")


if __name__ == "__main__":
    main()
