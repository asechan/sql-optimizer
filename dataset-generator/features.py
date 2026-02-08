"""Feature extraction for SQL query metadata."""

from typing import List


def extract_features(query_meta: dict) -> dict:
    """Extract numeric features from query metadata."""
    tables: List[str] = query_meta.get("tables", [])

    return {
        "num_tables":        len(tables),
        "num_joins":         query_meta.get("joins", 0),
        "num_conditions":    query_meta.get("conditions", 0),
        "num_subqueries":    query_meta.get("subqueries", 0),
        "has_wildcard":      int(query_meta.get("has_wildcard", False)),
        "has_order_by":      int(query_meta.get("has_order_by", False)),
        "has_group_by":      int(query_meta.get("has_group_by", False)),
        "has_having":        int(query_meta.get("has_having", False)),
        "has_distinct":      int(query_meta.get("has_distinct", False)),
        "has_limit":         int(query_meta.get("has_limit", False)),
        "num_where_columns": len(query_meta.get("where_columns", [])),
        "num_order_columns": len(query_meta.get("order_by_columns", [])),
        "num_group_columns": len(query_meta.get("group_by_columns", [])),
        "query_length":      len(query_meta.get("sql", "")),
    }


FEATURE_COLUMNS = [
    "num_tables", "num_joins", "num_conditions", "num_subqueries",
    "has_wildcard", "has_order_by", "has_group_by", "has_having",
    "has_distinct", "has_limit",
    "num_where_columns", "num_order_columns", "num_group_columns",
    "query_length",
]
