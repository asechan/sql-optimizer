package com.sqloptimizer.service;

import net.sf.jsqlparser.JSQLParserException;
import net.sf.jsqlparser.expression.*;
import net.sf.jsqlparser.expression.operators.conditional.AndExpression;
import net.sf.jsqlparser.expression.operators.conditional.OrExpression;
import net.sf.jsqlparser.expression.operators.relational.*;
import net.sf.jsqlparser.parser.CCJSqlParserUtil;
import net.sf.jsqlparser.schema.Column;
import net.sf.jsqlparser.schema.Table;
import net.sf.jsqlparser.statement.Statement;
import net.sf.jsqlparser.statement.select.*;
import org.springframework.stereotype.Service;

import java.util.*;

@Service
public class SqlParserService {

    public static class ParseResult {
        private final List<String> tables;
        private final int joins;
        private final int conditions;
        private final int subqueries;
        private final boolean hasWildcard;
        private final boolean hasOrderBy;
        private final boolean hasGroupBy;
        private final boolean hasHaving;
        private final boolean hasDistinct;
        private final boolean hasLimit;
        private final List<String> whereColumns;
        private final List<String> orderByColumns;
        private final List<String> groupByColumns;
        private final String queryType;

        public ParseResult(List<String> tables, int joins, int conditions, int subqueries,
                           boolean hasWildcard, boolean hasOrderBy, boolean hasGroupBy,
                           boolean hasHaving, boolean hasDistinct, boolean hasLimit,
                           List<String> whereColumns, List<String> orderByColumns,
                           List<String> groupByColumns, String queryType) {
            this.tables = tables;
            this.joins = joins;
            this.conditions = conditions;
            this.subqueries = subqueries;
            this.hasWildcard = hasWildcard;
            this.hasOrderBy = hasOrderBy;
            this.hasGroupBy = hasGroupBy;
            this.hasHaving = hasHaving;
            this.hasDistinct = hasDistinct;
            this.hasLimit = hasLimit;
            this.whereColumns = whereColumns;
            this.orderByColumns = orderByColumns;
            this.groupByColumns = groupByColumns;
            this.queryType = queryType;
        }

        public List<String> getTables() { return tables; }
        public int getJoins() { return joins; }
        public int getConditions() { return conditions; }
        public int getSubqueries() { return subqueries; }
        public boolean isHasWildcard() { return hasWildcard; }
        public boolean isHasOrderBy() { return hasOrderBy; }
        public boolean isHasGroupBy() { return hasGroupBy; }
        public boolean isHasHaving() { return hasHaving; }
        public boolean isHasDistinct() { return hasDistinct; }
        public boolean isHasLimit() { return hasLimit; }
        public List<String> getWhereColumns() { return whereColumns; }
        public List<String> getOrderByColumns() { return orderByColumns; }
        public List<String> getGroupByColumns() { return groupByColumns; }
        public String getQueryType() { return queryType; }
    }

    public ParseResult parse(String sql) throws JSQLParserException {
        Statement statement = CCJSqlParserUtil.parse(sql);

        String queryType = statement.getClass().getSimpleName()
                .replace("Statement", "")
                .toUpperCase();

        if (!(statement instanceof Select selectStatement)) {
            return new ParseResult(
                    List.of(), 0, 0, 0,
                    false, false, false, false, false, false,
                    List.of(), List.of(), List.of(), queryType
            );
        }

        Set<String> tables = new LinkedHashSet<>();
        int[] joins = {0};
        int[] conditions = {0};
        int[] subqueries = {0};
        boolean[] hasWildcard = {false};
        boolean[] hasOrderBy = {false};
        boolean[] hasGroupBy = {false};
        boolean[] hasHaving = {false};
        boolean[] hasDistinct = {false};
        boolean[] hasLimit = {false};
        List<String> whereColumns = new ArrayList<>();
        List<String> orderByColumns = new ArrayList<>();
        List<String> groupByColumns = new ArrayList<>();

        analyzeSelect(selectStatement, tables, joins, conditions, subqueries,
                hasWildcard, hasOrderBy, hasGroupBy, hasHaving, hasDistinct, hasLimit,
                whereColumns, orderByColumns, groupByColumns);

        return new ParseResult(
                new ArrayList<>(tables), joins[0], conditions[0], subqueries[0],
                hasWildcard[0], hasOrderBy[0], hasGroupBy[0], hasHaving[0],
                hasDistinct[0], hasLimit[0],
                whereColumns, orderByColumns, groupByColumns, "SELECT"
        );
    }

    private void analyzeSelect(Select select,
                               Set<String> tables, int[] joins, int[] conditions, int[] subqueries,
                               boolean[] hasWildcard, boolean[] hasOrderBy, boolean[] hasGroupBy,
                               boolean[] hasHaving, boolean[] hasDistinct, boolean[] hasLimit,
                               List<String> whereColumns, List<String> orderByColumns,
                               List<String> groupByColumns) {

        if (select instanceof PlainSelect ps) {
            analyzePlainSelect(ps, tables, joins, conditions, subqueries,
                    hasWildcard, hasOrderBy, hasGroupBy, hasHaving, hasDistinct, hasLimit,
                    whereColumns, orderByColumns, groupByColumns);
        } else if (select instanceof SetOperationList sol) {
            for (Select sel : sol.getSelects()) {
                analyzeSelect(sel, tables, joins, conditions, subqueries,
                        hasWildcard, hasOrderBy, hasGroupBy, hasHaving, hasDistinct, hasLimit,
                        whereColumns, orderByColumns, groupByColumns);
            }
        }
    }

    private void analyzePlainSelect(PlainSelect ps,
                                    Set<String> tables, int[] joins, int[] conditions,
                                    int[] subqueries,
                                    boolean[] hasWildcard, boolean[] hasOrderBy,
                                    boolean[] hasGroupBy, boolean[] hasHaving,
                                    boolean[] hasDistinct, boolean[] hasLimit,
                                    List<String> whereColumns, List<String> orderByColumns,
                                    List<String> groupByColumns) {

        if (ps.getSelectItems() != null) {
            for (SelectItem<?> item : ps.getSelectItems()) {
                if (item.toString().contains("*")) {
                    hasWildcard[0] = true;
                }
                if (item.getExpression() instanceof ParenthesedSelect) {
                    subqueries[0]++;
                }
            }
        }

        FromItem fromItem = ps.getFromItem();
        extractTablesFromItem(fromItem, tables, subqueries);

        if (ps.getJoins() != null) {
            for (Join join : ps.getJoins()) {
                joins[0]++;
                extractTablesFromItem(join.getRightItem(), tables, subqueries);
                if (join.getOnExpressions() != null) {
                    for (Expression onExpr : join.getOnExpressions()) {
                        conditions[0] += countConditions(onExpr);
                    }
                }
            }
        }

        if (ps.getWhere() != null) {
            conditions[0] += countConditions(ps.getWhere());
            extractColumnsFromExpression(ps.getWhere(), whereColumns);
            countSubqueries(ps.getWhere(), subqueries);
        }

        if (ps.getOrderByElements() != null && !ps.getOrderByElements().isEmpty()) {
            hasOrderBy[0] = true;
            for (OrderByElement ob : ps.getOrderByElements()) {
                if (ob.getExpression() instanceof Column col) {
                    orderByColumns.add(col.getColumnName());
                }
            }
        }

        if (ps.getGroupBy() != null) {
            hasGroupBy[0] = true;
            GroupByElement groupBy = ps.getGroupBy();
            if (groupBy.getGroupByExpressionList() != null) {
                for (Object item : groupBy.getGroupByExpressionList()) {
                    if (item instanceof Column col) {
                        groupByColumns.add(col.getColumnName());
                    }
                }
            }
        }

        if (ps.getHaving() != null) {
            hasHaving[0] = true;
            conditions[0] += countConditions(ps.getHaving());
        }

        if (ps.getDistinct() != null) {
            hasDistinct[0] = true;
        }

        if (ps.getLimit() != null) {
            hasLimit[0] = true;
        }
    }

    private void extractTablesFromItem(FromItem fromItem, Set<String> tables, int[] subqueries) {
        if (fromItem instanceof Table table) {
            tables.add(table.getName().toLowerCase());
        } else if (fromItem instanceof ParenthesedSelect) {
            subqueries[0]++;
        }
    }

    private int countConditions(Expression expr) {
        if (expr instanceof AndExpression and) {
            return countConditions(and.getLeftExpression()) + countConditions(and.getRightExpression());
        } else if (expr instanceof OrExpression or) {
            return countConditions(or.getLeftExpression()) + countConditions(or.getRightExpression());
        } else if (expr instanceof Parenthesis paren) {
            return countConditions(paren.getExpression());
        } else {
            // Any other expression (=, <, >, LIKE, IN, BETWEEN, IS NULL, etc.) is one condition
            return 1;
        }
    }

    private void extractColumnsFromExpression(Expression expr, List<String> columns) {
        if (expr instanceof AndExpression and) {
            extractColumnsFromExpression(and.getLeftExpression(), columns);
            extractColumnsFromExpression(and.getRightExpression(), columns);
        } else if (expr instanceof OrExpression or) {
            extractColumnsFromExpression(or.getLeftExpression(), columns);
            extractColumnsFromExpression(or.getRightExpression(), columns);
        } else if (expr instanceof Parenthesis paren) {
            extractColumnsFromExpression(paren.getExpression(), columns);
        } else if (expr instanceof ComparisonOperator comp) {
            if (comp.getLeftExpression() instanceof Column col) {
                columns.add(col.getColumnName());
            }
            if (comp.getRightExpression() instanceof Column col) {
                columns.add(col.getColumnName());
            }
        } else if (expr instanceof InExpression in) {
            if (in.getLeftExpression() instanceof Column col) {
                columns.add(col.getColumnName());
            }
        } else if (expr instanceof Between between) {
            if (between.getLeftExpression() instanceof Column col) {
                columns.add(col.getColumnName());
            }
        } else if (expr instanceof LikeExpression like) {
            if (like.getLeftExpression() instanceof Column col) {
                columns.add(col.getColumnName());
            }
        } else if (expr instanceof IsNullExpression isNull) {
            if (isNull.getLeftExpression() instanceof Column col) {
                columns.add(col.getColumnName());
            }
        }
    }

    private void countSubqueries(Expression expr, int[] subqueries) {
        if (expr instanceof ParenthesedSelect) {
            subqueries[0]++;
        } else if (expr instanceof AndExpression and) {
            countSubqueries(and.getLeftExpression(), subqueries);
            countSubqueries(and.getRightExpression(), subqueries);
        } else if (expr instanceof OrExpression or) {
            countSubqueries(or.getLeftExpression(), subqueries);
            countSubqueries(or.getRightExpression(), subqueries);
        } else if (expr instanceof Parenthesis paren) {
            countSubqueries(paren.getExpression(), subqueries);
        } else if (expr instanceof InExpression in) {
            if (in.getRightExpression() instanceof ParenthesedSelect) {
                subqueries[0]++;
            }
        } else if (expr instanceof ExistsExpression exists) {
            if (exists.getRightExpression() instanceof ParenthesedSelect) {
                subqueries[0]++;
            }
        }
    }
}
