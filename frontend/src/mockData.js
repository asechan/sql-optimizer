export const mockAnalysis = {
  predictedTime: 120,
  isSlow: true,
  suggestedIndex: "CREATE INDEX idx_user_id ON users(id);",
  optimizedQuery: "SELECT id, name FROM users WHERE id = ?",
  queryFeatures: {
    tables: ["users", "orders"],
    joins: 1,
    conditions: 2,
    subqueries: 0,
    hasWildcard: true,
    hasOrderBy: true,
  },
};
