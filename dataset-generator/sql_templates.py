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
}
