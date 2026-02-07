package com.sqloptimizer.service;

import com.sqloptimizer.service.SqlParserService.ParseResult;
import net.sf.jsqlparser.JSQLParserException;
import net.sf.jsqlparser.expression.operators.relational.ComparisonOperator;
import net.sf.jsqlparser.parser.CCJSqlParserUtil;
import net.sf.jsqlparser.schema.Column;
import net.sf.jsqlparser.statement.Statement;
import net.sf.jsqlparser.statement.select.*;
import org.springframework.stereotype.Service;

import java.util.ArrayList;
import java.util.List;

/**
 * Generates optimized query suggestions based on parsed features.
 * Applies rule-based rewrite heuristics:
 *   - Replace SELECT * with explicit columns when possible
 *   - Add LIMIT to unbounded queries
 *   - Suggest EXISTS over IN for correlated subqueries
 *   - Suggest column pruning for JOIN queries
 */
@Service
public class QueryOptimizerService {

    /**
     * Generate an optimized version of the SQL query along with optimization tips.
     *
     * @param originalSql the raw SQL query
     * @param parseResult parsed feature data
     * @return optimized SQL string and tips
     */
    public OptimizationResult optimize(String originalSql, ParseResult parseResult) {
        List<String> tips = new ArrayList<>();
        String optimized = originalSql.trim();

        // Normalize whitespace
        optimized = optimized.replaceAll("\\s+", " ");

        // 1. Replace SELECT * with column hint
        if (parseResult.isHasWildcard()) {
            tips.add("Replace SELECT * with specific column names to reduce I/O and enable covering indexes.");
        }

        // 2. Missing LIMIT on large result sets
        if (!parseResult.isHasLimit() && !parseResult.isHasGroupBy()
                && parseResult.getSubqueries() == 0 && parseResult.getConditions() == 0) {
            tips.add("Add a LIMIT clause to prevent unbounded result sets.");
            optimized = optimized.replaceAll(";\\s*$", "") + " LIMIT 1000;";
        }

        // 3. Multiple joins with SELECT *
        if (parseResult.isHasWildcard() && parseResult.getJoins() >= 2) {
            tips.add("SELECT * with multiple JOINs pulls all columns from all tables — specify only needed columns.");
        }

        // 4. ORDER BY without LIMIT
        if (parseResult.isHasOrderBy() && !parseResult.isHasLimit()) {
            tips.add("ORDER BY without LIMIT forces a full sort — add LIMIT if only top rows are needed.");
        }

        // 5. Using DISTINCT may indicate a missing JOIN condition
        if (parseResult.isHasDistinct() && parseResult.getJoins() > 0) {
            tips.add("DISTINCT with JOINs may indicate a missing or incorrect JOIN condition producing duplicates.");
        }

        // 6. Subquery optimization hint
        if (parseResult.getSubqueries() > 0) {
            tips.add("Consider rewriting correlated subqueries as JOINs or using EXISTS instead of IN for better performance.");
        }

        // 7. GROUP BY without index hint
        if (parseResult.isHasGroupBy() && parseResult.getGroupByColumns().size() > 2) {
            tips.add("GROUP BY on many columns can be expensive — ensure an appropriate composite index exists.");
        }

        // Build the optimized query: for now we apply simple safe rewrites
        optimized = applySimpleRewrites(optimized, parseResult);

        // Ensure it ends with semicolon
        if (!optimized.endsWith(";")) {
            optimized += ";";
        }

        return new OptimizationResult(optimized, tips);
    }

    /**
     * Apply simple, safe query rewrites.
     */
    private String applySimpleRewrites(String sql, ParseResult parseResult) {
        String result = sql;

        // Replace SELECT * with SELECT column list when we have WHERE columns to hint
        if (parseResult.isHasWildcard() && !parseResult.getWhereColumns().isEmpty()) {
            // Suggest specific columns from WHERE + ORDER BY as a starting point
            List<String> suggestedCols = new ArrayList<>(parseResult.getWhereColumns());
            for (String ob : parseResult.getOrderByColumns()) {
                if (!suggestedCols.contains(ob)) {
                    suggestedCols.add(ob);
                }
            }
            String colList = String.join(", ", suggestedCols);
            // Replace first SELECT * occurrence
            result = result.replaceFirst("(?i)SELECT\\s+\\*", "SELECT " + colList);
        }

        return result;
    }

    /**
     * Result of query optimization.
     */
    public static class OptimizationResult {
        private final String optimizedQuery;
        private final List<String> tips;

        public OptimizationResult(String optimizedQuery, List<String> tips) {
            this.optimizedQuery = optimizedQuery;
            this.tips = tips;
        }

        public String getOptimizedQuery() { return optimizedQuery; }
        public List<String> getTips() { return tips; }
    }
}
