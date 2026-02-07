"""
Configuration for the SQL dataset generator.
Adjust these values to control the size and diversity of the generated dataset.
"""

# ── Dataset size ──────────────────────────────────────────────────────────
NUM_QUERIES = 5000          # Total number of SQL queries to generate

# ── Schema simulation ────────────────────────────────────────────────────
TABLES = [
    "users", "orders", "products", "payments", "reviews",
    "categories", "inventory", "shipping", "suppliers", "employees",
    "customers", "invoices", "transactions", "sessions", "logs",
    "departments", "projects", "tasks", "comments", "notifications",
]

COLUMNS = {
    "users":         ["id", "name", "email", "age", "created_at", "status", "country"],
    "orders":        ["id", "user_id", "product_id", "quantity", "total", "created_at", "status"],
    "products":      ["id", "name", "category_id", "price", "stock", "created_at", "rating"],
    "payments":      ["id", "order_id", "amount", "method", "status", "paid_at"],
    "reviews":       ["id", "user_id", "product_id", "rating", "comment", "created_at"],
    "categories":    ["id", "name", "parent_id", "description"],
    "inventory":     ["id", "product_id", "warehouse_id", "quantity", "updated_at"],
    "shipping":      ["id", "order_id", "carrier", "tracking_number", "shipped_at", "delivered_at"],
    "suppliers":     ["id", "name", "contact_email", "country", "rating"],
    "employees":     ["id", "name", "department_id", "salary", "hire_date", "manager_id"],
    "customers":     ["id", "name", "email", "phone", "address", "city", "country"],
    "invoices":      ["id", "order_id", "amount", "due_date", "paid", "created_at"],
    "transactions":  ["id", "account_id", "type", "amount", "created_at", "status"],
    "sessions":      ["id", "user_id", "token", "ip_address", "created_at", "expires_at"],
    "logs":          ["id", "level", "message", "source", "created_at"],
    "departments":   ["id", "name", "budget", "manager_id", "created_at"],
    "projects":      ["id", "name", "department_id", "budget", "start_date", "end_date", "status"],
    "tasks":         ["id", "project_id", "assignee_id", "title", "status", "priority", "due_date"],
    "comments":      ["id", "user_id", "entity_id", "entity_type", "body", "created_at"],
    "notifications": ["id", "user_id", "type", "message", "read", "created_at"],
}

# Foreign-key relationships for realistic JOINs: (child_table, child_col, parent_table, parent_col)
JOIN_PAIRS = [
    ("orders",       "user_id",       "users",       "id"),
    ("orders",       "product_id",    "products",    "id"),
    ("payments",     "order_id",      "orders",      "id"),
    ("reviews",      "user_id",       "users",       "id"),
    ("reviews",      "product_id",    "products",    "id"),
    ("products",     "category_id",   "categories",  "id"),
    ("inventory",    "product_id",    "products",    "id"),
    ("shipping",     "order_id",      "orders",      "id"),
    ("employees",    "department_id", "departments", "id"),
    ("tasks",        "project_id",    "projects",    "id"),
    ("tasks",        "assignee_id",   "employees",   "id"),
    ("projects",     "department_id", "departments", "id"),
    ("invoices",     "order_id",      "orders",      "id"),
    ("sessions",     "user_id",       "users",       "id"),
    ("comments",     "user_id",       "users",       "id"),
    ("notifications","user_id",       "users",       "id"),
]

# ── Query complexity distribution (weights) ──────────────────────────────
# Controls how often each query pattern is generated
PATTERN_WEIGHTS = {
    "simple_select":       15,
    "select_where":        20,
    "select_where_order":  12,
    "select_limit":        8,
    "select_join":         15,
    "select_multi_join":   8,
    "select_subquery":     6,
    "select_group_by":     8,
    "select_having":       4,
    "select_distinct":     4,
}

# ── Output ────────────────────────────────────────────────────────────────
OUTPUT_DIR   = "output"
OUTPUT_FILE  = "sql_training_dataset.csv"
