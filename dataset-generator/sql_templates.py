"""SQL template engine for generating diverse, realistic SQL queries."""

import random
from typing import List, Tuple

from config import TABLES, COLUMNS, JOIN_PAIRS


def _pick_table() -> str:
    return random.choice(TABLES)


def _pick_columns(table: str, n: int | None = None) -> List[str]:
    cols = COLUMNS.get(table, ["id"])
    if n is None:
        n = random.randint(1, min(4, len(cols)))
    return random.sample(cols, min(n, len(cols)))


def _pick_join_pair(base_table: str | None = None) -> Tuple[str, str, str, str] | None:
    candidates = JOIN_PAIRS
    if base_table:
        candidates = [
            jp for jp in JOIN_PAIRS
            if jp[0] == base_table or jp[2] == base_table
        ]
    if not candidates:
        return None
    return random.choice(candidates)


def _random_value(col: str) -> str:
    """Generate a plausible literal for a WHERE condition."""
    if col in ("id", "user_id", "product_id", "order_id", "category_id",
               "department_id", "project_id", "assignee_id", "manager_id",
               "warehouse_id", "account_id", "entity_id", "parent_id"):
        return str(random.randint(1, 10000))
    if col in ("age", "quantity", "stock", "priority"):
        return str(random.randint(1, 100))
    if col in ("price", "total", "amount", "salary", "budget"):
        return f"{random.uniform(10, 5000):.2f}"
    if col in ("rating",):
        return f"{random.uniform(1, 5):.1f}"
    if col in ("status",):
        return f"'{random.choice(['active', 'inactive', 'pending', 'completed', 'cancelled'])}'"
    if col in ("method",):
        return f"'{random.choice(['credit_card', 'paypal', 'bank_transfer', 'crypto'])}'"
    if col in ("level",):
        return f"'{random.choice(['INFO', 'WARN', 'ERROR', 'DEBUG'])}'"
    if col in ("type",):
        return f"'{random.choice(['credit', 'debit', 'refund', 'transfer'])}'"
    if col in ("country", "city"):
        return f"'{random.choice(['US', 'UK', 'DE', 'FR', 'JP', 'IN', 'BR', 'AU'])}'"
    if col in ("read", "paid"):
        return random.choice(["TRUE", "FALSE"])
    if "date" in col or "at" in col.lower():
        year = random.randint(2020, 2025)
        month = random.randint(1, 12)
        day = random.randint(1, 28)
        return f"'{year}-{month:02d}-{day:02d}'"
    # Default: quoted string
    return f"'value_{random.randint(1, 999)}'"


def _where_condition(table: str, num_conditions: int | None = None) -> Tuple[str, List[str]]:
    cols = COLUMNS.get(table, ["id"])
    if num_conditions is None:
        num_conditions = random.choices([1, 2, 3], weights=[50, 35, 15])[0]
    chosen = random.sample(cols, min(num_conditions, len(cols)))

    ops = ["=", ">", "<", ">=", "<=", "!="]
    parts = []
    for col in chosen:
        op = random.choice(ops)
        val = _random_value(col)
        parts.append(f"{table}.{col} {op} {val}")

    joiner = random.choice(["AND", "AND", "AND", "OR"])
    clause = f" {joiner} ".join(parts)
    return clause, chosen


def _order_by(table: str) -> Tuple[str, List[str]]:
    cols = COLUMNS.get(table, ["id"])
    n = random.randint(1, min(2, len(cols)))
    chosen = random.sample(cols, n)
    direction = random.choice(["ASC", "DESC"])
    parts = [f"{table}.{c} {direction}" for c in chosen]
    return "ORDER BY " + ", ".join(parts), chosen


def _agg_function(col: str) -> str:
    if col in ("id", "user_id", "order_id", "product_id"):
        return f"COUNT({col})"
    if col in ("price", "total", "amount", "salary", "budget", "quantity"):
        fn = random.choice(["SUM", "AVG", "MIN", "MAX"])
        return f"{fn}({col})"
    return f"COUNT({col})"


def gen_simple_select() -> dict:
    table = _pick_table()
    use_wildcard = random.random() < 0.4
    if use_wildcard:
        select_cols = ["*"]
    else:
        select_cols = _pick_columns(table)

    sql = f"SELECT {', '.join(select_cols)} FROM {table};"
    return {
        "sql": sql, "tables": [table], "joins": 0, "conditions": 0,
        "subqueries": 0, "has_wildcard": use_wildcard,
        "has_order_by": False, "has_group_by": False, "has_having": False,
        "has_distinct": False, "has_limit": False,
        "where_columns": [], "order_by_columns": [], "group_by_columns": [],
        "pattern": "simple_select",
    }


def gen_select_where() -> dict:
    table = _pick_table()
    use_wildcard = random.random() < 0.3
    select_cols = ["*"] if use_wildcard else _pick_columns(table)
    where_clause, where_cols = _where_condition(table)

    sql = f"SELECT {', '.join(select_cols)} FROM {table} WHERE {where_clause};"
    return {
        "sql": sql, "tables": [table], "joins": 0,
        "conditions": len(where_cols), "subqueries": 0,
        "has_wildcard": use_wildcard, "has_order_by": False,
        "has_group_by": False, "has_having": False,
        "has_distinct": False, "has_limit": False,
        "where_columns": where_cols, "order_by_columns": [],
        "group_by_columns": [], "pattern": "select_where",
    }


def gen_select_where_order() -> dict:
    table = _pick_table()
    use_wildcard = random.random() < 0.25
    select_cols = ["*"] if use_wildcard else _pick_columns(table)
    where_clause, where_cols = _where_condition(table)
    order_clause, order_cols = _order_by(table)

    sql = f"SELECT {', '.join(select_cols)} FROM {table} WHERE {where_clause} {order_clause};"
    return {
        "sql": sql, "tables": [table], "joins": 0,
        "conditions": len(where_cols), "subqueries": 0,
        "has_wildcard": use_wildcard, "has_order_by": True,
        "has_group_by": False, "has_having": False,
        "has_distinct": False, "has_limit": False,
        "where_columns": where_cols, "order_by_columns": order_cols,
        "group_by_columns": [], "pattern": "select_where_order",
    }


def gen_select_limit() -> dict:
    table = _pick_table()
    use_wildcard = random.random() < 0.35
    select_cols = ["*"] if use_wildcard else _pick_columns(table)
    limit = random.choice([10, 25, 50, 100, 500, 1000])

    has_where = random.random() < 0.5
    where_clause, where_cols = ("", [])
    if has_where:
        where_clause, where_cols = _where_condition(table)
        where_clause = f" WHERE {where_clause}"

    sql = f"SELECT {', '.join(select_cols)} FROM {table}{where_clause} LIMIT {limit};"
    return {
        "sql": sql, "tables": [table], "joins": 0,
        "conditions": len(where_cols), "subqueries": 0,
        "has_wildcard": use_wildcard, "has_order_by": False,
        "has_group_by": False, "has_having": False,
        "has_distinct": False, "has_limit": True,
        "where_columns": where_cols, "order_by_columns": [],
        "group_by_columns": [], "pattern": "select_limit",
    }


def gen_select_join() -> dict:
    jp = random.choice(JOIN_PAIRS)
    child, child_col, parent, parent_col = jp

    use_wildcard = random.random() < 0.35
    if use_wildcard:
        select_cols = ["*"]
    else:
        cols_child = _pick_columns(child, random.randint(1, 3))
        cols_parent = _pick_columns(parent, random.randint(1, 2))
        select_cols = [f"{child}.{c}" for c in cols_child] + [f"{parent}.{c}" for c in cols_parent]

    join_type = random.choice(["JOIN", "LEFT JOIN", "INNER JOIN"])
    on_clause = f"{child}.{child_col} = {parent}.{parent_col}"

    has_where = random.random() < 0.5
    where_clause, where_cols = ("", [])
    if has_where:
        where_table = random.choice([child, parent])
        where_clause, where_cols = _where_condition(where_table, random.randint(1, 2))
        where_clause = f" WHERE {where_clause}"

    sql = (f"SELECT {', '.join(select_cols)} "
           f"FROM {child} {join_type} {parent} ON {on_clause}{where_clause};")

    return {
        "sql": sql, "tables": [child, parent], "joins": 1,
        "conditions": len(where_cols), "subqueries": 0,
        "has_wildcard": use_wildcard, "has_order_by": False,
        "has_group_by": False, "has_having": False,
        "has_distinct": False, "has_limit": False,
        "where_columns": where_cols, "order_by_columns": [],
        "group_by_columns": [], "pattern": "select_join",
    }


def gen_select_multi_join() -> dict:
    num_joins = random.choice([2, 2, 3])
    used_tables = set()
    join_clauses = []
    tables_list = []

    # Start with a random join pair
    first_jp = random.choice(JOIN_PAIRS)
    child, child_col, parent, parent_col = first_jp
    used_tables.update([child, parent])
    tables_list.extend([child, parent])
    base_table = child
    join_type = random.choice(["JOIN", "LEFT JOIN", "INNER JOIN"])
    join_clauses.append(f"{join_type} {parent} ON {child}.{child_col} = {parent}.{parent_col}")

    # Add more joins
    for _ in range(num_joins - 1):
        candidates = [
            jp for jp in JOIN_PAIRS
            if (jp[0] in used_tables or jp[2] in used_tables)
            and not (jp[0] in used_tables and jp[2] in used_tables)
        ]
        if not candidates:
            break
        jp = random.choice(candidates)
        c, cc, p, pc = jp
        jt = random.choice(["JOIN", "LEFT JOIN", "INNER JOIN"])
        join_clauses.append(f"{jt} {c if c not in used_tables else p} ON {c}.{cc} = {p}.{pc}")
        new_table = c if c not in used_tables else p
        used_tables.add(new_table)
        tables_list.append(new_table)

    use_wildcard = random.random() < 0.4
    if use_wildcard:
        select_cols = ["*"]
    else:
        all_cols = []
        for t in tables_list[:3]:
            for c in _pick_columns(t, random.randint(1, 2)):
                all_cols.append(f"{t}.{c}")
        select_cols = all_cols

    has_where = random.random() < 0.4
    where_clause, where_cols = ("", [])
    if has_where:
        wt = random.choice(list(used_tables))
        where_clause, where_cols = _where_condition(wt, 1)
        where_clause = f" WHERE {where_clause}"

    sql = f"SELECT {', '.join(select_cols)} FROM {base_table} {' '.join(join_clauses)}{where_clause};"

    return {
        "sql": sql, "tables": tables_list, "joins": len(join_clauses),
        "conditions": len(where_cols), "subqueries": 0,
        "has_wildcard": use_wildcard, "has_order_by": False,
        "has_group_by": False, "has_having": False,
        "has_distinct": False, "has_limit": False,
        "where_columns": where_cols, "order_by_columns": [],
        "group_by_columns": [], "pattern": "select_multi_join",
    }


def gen_select_subquery() -> dict:
    outer_table = _pick_table()
    inner_jp = _pick_join_pair(outer_table)
    if inner_jp is None:
        # Fallback to a simple subquery
        inner_jp = random.choice(JOIN_PAIRS)

    child, child_col, parent, parent_col = inner_jp
    # Determine which table is the inner query
    if child == outer_table:
        inner_table = parent
        link_col = child_col
        inner_col = parent_col
    else:
        inner_table = child
        link_col = parent_col
        inner_col = child_col

    outer_cols = _pick_columns(outer_table, random.randint(2, 4))
    select_cols = [f"{outer_table}.{c}" for c in outer_cols]

    # Inner WHERE condition (optional)
    inner_where = ""
    if random.random() < 0.5:
        inner_where_clause, _ = _where_condition(inner_table, 1)
        inner_where = f" WHERE {inner_where_clause}"

    sql = (f"SELECT {', '.join(select_cols)} FROM {outer_table} "
           f"WHERE {outer_table}.{link_col} IN "
           f"(SELECT {inner_table}.{inner_col} FROM {inner_table}{inner_where});")

    return {
        "sql": sql, "tables": [outer_table, inner_table], "joins": 0,
        "conditions": 1, "subqueries": 1,
        "has_wildcard": False, "has_order_by": False,
        "has_group_by": False, "has_having": False,
        "has_distinct": False, "has_limit": False,
        "where_columns": [link_col], "order_by_columns": [],
        "group_by_columns": [], "pattern": "select_subquery",
    }


def gen_select_group_by() -> dict:
    table = _pick_table()
    cols = COLUMNS.get(table, ["id"])

    # Pick 1–2 group-by columns
    gb_count = random.randint(1, min(2, len(cols)))
    gb_cols = random.sample(cols, gb_count)

    # Pick 1–2 aggregate columns (different from group-by if possible)
    remaining = [c for c in cols if c not in gb_cols]
    if not remaining:
        remaining = cols
    agg_count = random.randint(1, min(2, len(remaining)))
    agg_cols = random.sample(remaining, agg_count)

    select_parts = [f"{table}.{c}" for c in gb_cols]
    for ac in agg_cols:
        select_parts.append(_agg_function(ac))

    has_where = random.random() < 0.4
    where_clause, where_cols = ("", [])
    if has_where:
        where_clause, where_cols = _where_condition(table, 1)
        where_clause = f" WHERE {where_clause}"

    gb_clause = ", ".join(f"{table}.{c}" for c in gb_cols)
    sql = f"SELECT {', '.join(select_parts)} FROM {table}{where_clause} GROUP BY {gb_clause};"

    return {
        "sql": sql, "tables": [table], "joins": 0,
        "conditions": len(where_cols), "subqueries": 0,
        "has_wildcard": False, "has_order_by": False,
        "has_group_by": True, "has_having": False,
        "has_distinct": False, "has_limit": False,
        "where_columns": where_cols, "order_by_columns": [],
        "group_by_columns": gb_cols, "pattern": "select_group_by",
    }


def gen_select_having() -> dict:
    table = _pick_table()
    cols = COLUMNS.get(table, ["id"])
    gb_col = random.choice(cols)
    remaining = [c for c in cols if c != gb_col]
    if not remaining:
        remaining = cols
    agg_col = random.choice(remaining)

    agg = _agg_function(agg_col)
    having_val = random.randint(1, 100)
    having_op = random.choice([">", ">=", "<", "<="])

    sql = (f"SELECT {table}.{gb_col}, {agg} FROM {table} "
           f"GROUP BY {table}.{gb_col} HAVING {agg} {having_op} {having_val};")

    return {
        "sql": sql, "tables": [table], "joins": 0,
        "conditions": 0, "subqueries": 0,
        "has_wildcard": False, "has_order_by": False,
        "has_group_by": True, "has_having": True,
        "has_distinct": False, "has_limit": False,
        "where_columns": [], "order_by_columns": [],
        "group_by_columns": [gb_col], "pattern": "select_having",
    }


def gen_select_distinct() -> dict:
    table = _pick_table()
    select_cols = _pick_columns(table, random.randint(1, 3))

    has_where = random.random() < 0.5
    where_clause, where_cols = ("", [])
    if has_where:
        where_clause, where_cols = _where_condition(table, 1)
        where_clause = f" WHERE {where_clause}"

    sql = f"SELECT DISTINCT {', '.join(select_cols)} FROM {table}{where_clause};"

    return {
        "sql": sql, "tables": [table], "joins": 0,
        "conditions": len(where_cols), "subqueries": 0,
        "has_wildcard": False, "has_order_by": False,
        "has_group_by": False, "has_having": False,
        "has_distinct": True, "has_limit": False,
        "where_columns": where_cols, "order_by_columns": [],
        "group_by_columns": [], "pattern": "select_distinct",
    }


def gen_select_order_limit() -> dict:
    table = _pick_table()
    select_cols = _pick_columns(table, random.randint(2, 4))

    where_clause, where_cols = _where_condition(table, random.randint(1, 2))
    order_clause, order_cols = _order_by(table)
    limit = random.choice([10, 25, 50, 100, 200])

    sql = (
        f"SELECT {', '.join(f'{table}.{c}' for c in select_cols)} "
        f"FROM {table} WHERE {where_clause} {order_clause} LIMIT {limit};"
    )

    return {
        "sql": sql,
        "tables": [table],
        "joins": 0,
        "conditions": len(where_cols),
        "subqueries": 0,
        "has_wildcard": False,
        "has_order_by": True,
        "has_group_by": False,
        "has_having": False,
        "has_distinct": False,
        "has_limit": True,
        "where_columns": where_cols,
        "order_by_columns": order_cols,
        "group_by_columns": [],
        "pattern": "select_order_limit",
    }


def gen_select_join_order_limit() -> dict:
    child, child_col, parent, parent_col = random.choice(JOIN_PAIRS)

    cols_child = _pick_columns(child, random.randint(1, 3))
    cols_parent = _pick_columns(parent, random.randint(1, 2))
    select_cols = [f"{child}.{c}" for c in cols_child] + [f"{parent}.{c}" for c in cols_parent]

    where_table = random.choice([child, parent])
    where_clause, where_cols = _where_condition(where_table, random.randint(1, 2))
    order_table = random.choice([child, parent])
    order_clause, order_cols = _order_by(order_table)
    limit = random.choice([20, 50, 100, 250])

    sql = (
        f"SELECT {', '.join(select_cols)} FROM {child} "
        f"JOIN {parent} ON {child}.{child_col} = {parent}.{parent_col} "
        f"WHERE {where_clause} {order_clause} LIMIT {limit};"
    )

    return {
        "sql": sql,
        "tables": [child, parent],
        "joins": 1,
        "conditions": len(where_cols),
        "subqueries": 0,
        "has_wildcard": False,
        "has_order_by": True,
        "has_group_by": False,
        "has_having": False,
        "has_distinct": False,
        "has_limit": True,
        "where_columns": where_cols,
        "order_by_columns": order_cols,
        "group_by_columns": [],
        "pattern": "select_join_order_limit",
    }


def gen_select_cte() -> dict:
    table = _pick_table()
    cte_cols = _pick_columns(table, random.randint(3, 5))
    where_clause, where_cols = _where_condition(table, random.randint(1, 2))
    order_clause, order_cols = _order_by(table)
    limit = random.choice([25, 50, 100, 200])

    select_list = ", ".join(f"{table}.{c}" for c in cte_cols)
    sql = (
        f"WITH base_rows AS ("
        f"SELECT {select_list} FROM {table} WHERE {where_clause}"
        f") "
        f"SELECT {', '.join(cte_cols)} FROM base_rows {order_clause} LIMIT {limit};"
    )

    return {
        "sql": sql,
        "tables": [table],
        "joins": 0,
        "conditions": len(where_cols),
        "subqueries": 1,
        "has_wildcard": False,
        "has_order_by": True,
        "has_group_by": False,
        "has_having": False,
        "has_distinct": False,
        "has_limit": True,
        "where_columns": where_cols,
        "order_by_columns": order_cols,
        "group_by_columns": [],
        "pattern": "select_cte",
    }


def gen_select_exists() -> dict:
    child, child_col, parent, parent_col = random.choice(JOIN_PAIRS)
    outer_table = parent
    inner_table = child

    outer_cols = _pick_columns(outer_table, random.randint(2, 4))
    inner_where_clause, inner_where_cols = _where_condition(inner_table, 1)

    sql = (
        f"SELECT {', '.join(f'o.{c}' for c in outer_cols)} "
        f"FROM {outer_table} o "
        f"WHERE EXISTS ("
        f"SELECT 1 FROM {inner_table} i "
        f"WHERE i.{child_col} = o.{parent_col} AND {inner_where_clause}"
        f");"
    )

    where_cols = [parent_col] + inner_where_cols
    return {
        "sql": sql,
        "tables": [outer_table, inner_table],
        "joins": 0,
        "conditions": len(where_cols),
        "subqueries": 1,
        "has_wildcard": False,
        "has_order_by": False,
        "has_group_by": False,
        "has_having": False,
        "has_distinct": False,
        "has_limit": False,
        "where_columns": where_cols,
        "order_by_columns": [],
        "group_by_columns": [],
        "pattern": "select_exists",
    }


def gen_select_union_all() -> dict:
    table_a = _pick_table()
    table_b = _pick_table()
    cols_a = _pick_columns(table_a, random.randint(2, 3))
    cols_b = _pick_columns(table_b, len(cols_a))

    where_a, where_cols_a = _where_condition(table_a, 1)
    where_b, where_cols_b = _where_condition(table_b, 1)

    select_a = ", ".join(f"{table_a}.{c}" for c in cols_a)
    select_b = ", ".join(f"{table_b}.{c}" for c in cols_b)

    sql = (
        f"SELECT {select_a} FROM {table_a} WHERE {where_a} "
        f"UNION ALL "
        f"SELECT {select_b} FROM {table_b} WHERE {where_b};"
    )

    return {
        "sql": sql,
        "tables": [table_a, table_b],
        "joins": 0,
        "conditions": len(where_cols_a) + len(where_cols_b),
        "subqueries": 0,
        "has_wildcard": False,
        "has_order_by": False,
        "has_group_by": False,
        "has_having": False,
        "has_distinct": False,
        "has_limit": False,
        "where_columns": where_cols_a + where_cols_b,
        "order_by_columns": [],
        "group_by_columns": [],
        "pattern": "select_union_all",
    }


def gen_select_case_when() -> dict:
    table = random.choice(["orders", "transactions", "payments", "invoices"])
    cols = COLUMNS.get(table, ["id", "status"])
    gb_col = random.choice([c for c in cols if c in ("status", "method", "type", "country")] or cols[:1])
    metric_col = random.choice([c for c in cols if c in ("total", "amount", "price", "quantity")] or cols[:1])
    threshold = _random_value(metric_col)

    sql = (
        f"SELECT {table}.{gb_col}, "
        f"SUM(CASE WHEN {table}.{metric_col} > {threshold} THEN 1 ELSE 0 END) AS high_value_count, "
        f"COUNT(*) AS total_rows "
        f"FROM {table} "
        f"GROUP BY {table}.{gb_col};"
    )

    return {
        "sql": sql,
        "tables": [table],
        "joins": 0,
        "conditions": 1,
        "subqueries": 0,
        "has_wildcard": False,
        "has_order_by": False,
        "has_group_by": True,
        "has_having": False,
        "has_distinct": False,
        "has_limit": False,
        "where_columns": [metric_col],
        "order_by_columns": [],
        "group_by_columns": [gb_col],
        "pattern": "select_case_when",
    }


def gen_select_window_fn() -> dict:
    table = random.choice(["orders", "transactions", "reviews", "tasks"])
    cols = COLUMNS.get(table, ["id"])

    partition_col = random.choice([c for c in cols if c.endswith("_id") or c in ("status", "type")] or [cols[0]])
    order_col = random.choice([c for c in cols if "date" in c or c.endswith("_at") or c == "id"] or [cols[0]])

    select_cols = _pick_columns(table, random.randint(2, 4))
    where_clause, where_cols = _where_condition(table, 1)
    limit = random.choice([50, 100, 200])

    sql = (
        f"SELECT {', '.join(f'{table}.{c}' for c in select_cols)}, "
        f"ROW_NUMBER() OVER (PARTITION BY {table}.{partition_col} ORDER BY {table}.{order_col} DESC) AS row_num "
        f"FROM {table} WHERE {where_clause} "
        f"ORDER BY {table}.{partition_col} ASC LIMIT {limit};"
    )

    return {
        "sql": sql,
        "tables": [table],
        "joins": 0,
        "conditions": len(where_cols),
        "subqueries": 0,
        "has_wildcard": False,
        "has_order_by": True,
        "has_group_by": False,
        "has_having": False,
        "has_distinct": False,
        "has_limit": True,
        "where_columns": where_cols,
        "order_by_columns": [partition_col, order_col],
        "group_by_columns": [],
        "pattern": "select_window_fn",
    }


def gen_select_correlated_subquery() -> dict:
    outer_table = random.choice(["users", "customers", "projects", "products"])
    related = [jp for jp in JOIN_PAIRS if jp[2] == outer_table or jp[0] == outer_table]
    if not related:
        related = [random.choice(JOIN_PAIRS)]

    child, child_col, parent, parent_col = random.choice(related)
    if outer_table == child:
        inner_table = parent
        outer_key = child_col
        inner_key = parent_col
    else:
        inner_table = child
        outer_key = parent_col
        inner_key = child_col

    outer_cols = _pick_columns(outer_table, random.randint(2, 3))
    where_clause, where_cols = _where_condition(outer_table, 1)

    sql = (
        f"SELECT {', '.join(f'o.{c}' for c in outer_cols)}, "
        f"(SELECT COUNT(*) FROM {inner_table} i WHERE i.{inner_key} = o.{outer_key}) AS related_count "
        f"FROM {outer_table} o WHERE {where_clause};"
    )

    return {
        "sql": sql,
        "tables": [outer_table, inner_table],
        "joins": 0,
        "conditions": len(where_cols) + 1,
        "subqueries": 1,
        "has_wildcard": False,
        "has_order_by": False,
        "has_group_by": False,
        "has_having": False,
        "has_distinct": False,
        "has_limit": False,
        "where_columns": where_cols + [outer_key],
        "order_by_columns": [],
        "group_by_columns": [],
        "pattern": "select_correlated_subquery",
    }


GENERATORS = {
    "simple_select":       gen_simple_select,
    "select_where":        gen_select_where,
    "select_where_order":  gen_select_where_order,
    "select_limit":        gen_select_limit,
    "select_join":         gen_select_join,
    "select_multi_join":   gen_select_multi_join,
    "select_subquery":     gen_select_subquery,
    "select_group_by":     gen_select_group_by,
    "select_having":       gen_select_having,
    "select_distinct":     gen_select_distinct,
    "select_order_limit":  gen_select_order_limit,
    "select_join_order_limit": gen_select_join_order_limit,
    "select_cte":          gen_select_cte,
    "select_exists":       gen_select_exists,
    "select_union_all":    gen_select_union_all,
    "select_case_when":    gen_select_case_when,
    "select_window_fn":    gen_select_window_fn,
    "select_correlated_subquery": gen_select_correlated_subquery,
}
