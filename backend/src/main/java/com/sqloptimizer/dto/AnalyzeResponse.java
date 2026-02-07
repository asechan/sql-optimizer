package com.sqloptimizer.dto;

import java.util.List;

/**
 * Response body for the /analyze endpoint.
 * Contains parsed query features, performance prediction, index suggestions,
 * optimized query, and optimization tips.
 */
public class AnalyzeResponse {

    private long predictedTime;
    private boolean isSlow;
    private String suggestedIndex;
    private List<String> suggestedIndexes;
    private String optimizedQuery;
    private List<String> optimizationTips;
    private QueryFeatures queryFeatures;

    public static class QueryFeatures {
        private List<String> tables;
        private int joins;
        private int conditions;
        private int subqueries;
        private boolean hasWildcard;
        private boolean hasOrderBy;
        private boolean hasGroupBy;
        private boolean hasHaving;
        private boolean hasDistinct;
        private boolean hasLimit;
        private List<String> whereColumns;
        private List<String> orderByColumns;
        private List<String> groupByColumns;
        private String queryType;

        public QueryFeatures() {}

        public QueryFeatures(List<String> tables, int joins, int conditions,
                             int subqueries, boolean hasWildcard, boolean hasOrderBy) {
            this.tables = tables;
            this.joins = joins;
            this.conditions = conditions;
            this.subqueries = subqueries;
            this.hasWildcard = hasWildcard;
            this.hasOrderBy = hasOrderBy;
        }

        public List<String> getTables() { return tables; }
        public void setTables(List<String> tables) { this.tables = tables; }
        public int getJoins() { return joins; }
        public void setJoins(int joins) { this.joins = joins; }
        public int getConditions() { return conditions; }
        public void setConditions(int conditions) { this.conditions = conditions; }
        public int getSubqueries() { return subqueries; }
        public void setSubqueries(int subqueries) { this.subqueries = subqueries; }
        public boolean isHasWildcard() { return hasWildcard; }
        public void setHasWildcard(boolean hasWildcard) { this.hasWildcard = hasWildcard; }
        public boolean isHasOrderBy() { return hasOrderBy; }
        public void setHasOrderBy(boolean hasOrderBy) { this.hasOrderBy = hasOrderBy; }
        public boolean isHasGroupBy() { return hasGroupBy; }
        public void setHasGroupBy(boolean hasGroupBy) { this.hasGroupBy = hasGroupBy; }
        public boolean isHasHaving() { return hasHaving; }
        public void setHasHaving(boolean hasHaving) { this.hasHaving = hasHaving; }
        public boolean isHasDistinct() { return hasDistinct; }
        public void setHasDistinct(boolean hasDistinct) { this.hasDistinct = hasDistinct; }
        public boolean isHasLimit() { return hasLimit; }
        public void setHasLimit(boolean hasLimit) { this.hasLimit = hasLimit; }
        public List<String> getWhereColumns() { return whereColumns; }
        public void setWhereColumns(List<String> whereColumns) { this.whereColumns = whereColumns; }
        public List<String> getOrderByColumns() { return orderByColumns; }
        public void setOrderByColumns(List<String> orderByColumns) { this.orderByColumns = orderByColumns; }
        public List<String> getGroupByColumns() { return groupByColumns; }
        public void setGroupByColumns(List<String> groupByColumns) { this.groupByColumns = groupByColumns; }
        public String getQueryType() { return queryType; }
        public void setQueryType(String queryType) { this.queryType = queryType; }
    }

    public AnalyzeResponse() {}

    public long getPredictedTime() { return predictedTime; }
    public void setPredictedTime(long predictedTime) { this.predictedTime = predictedTime; }
    public boolean isSlow() { return isSlow; }
    public void setSlow(boolean slow) { isSlow = slow; }
    public String getSuggestedIndex() { return suggestedIndex; }
    public void setSuggestedIndex(String suggestedIndex) { this.suggestedIndex = suggestedIndex; }
    public List<String> getSuggestedIndexes() { return suggestedIndexes; }
    public void setSuggestedIndexes(List<String> suggestedIndexes) { this.suggestedIndexes = suggestedIndexes; }
    public String getOptimizedQuery() { return optimizedQuery; }
    public void setOptimizedQuery(String optimizedQuery) { this.optimizedQuery = optimizedQuery; }
    public List<String> getOptimizationTips() { return optimizationTips; }
    public void setOptimizationTips(List<String> optimizationTips) { this.optimizationTips = optimizationTips; }
    public QueryFeatures getQueryFeatures() { return queryFeatures; }
    public void setQueryFeatures(QueryFeatures queryFeatures) { this.queryFeatures = queryFeatures; }
}
