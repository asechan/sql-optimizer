package com.sqloptimizer.dto;

import java.util.List;

/**
 * Response body for the /analyze endpoint.
 */
public class AnalyzeResponse {

    private long predictedTime;
    private boolean isSlow;
    private String suggestedIndex;
    private String optimizedQuery;
    private QueryFeatures queryFeatures;

    public static class QueryFeatures {
        private List<String> tables;
        private int joins;
        private int conditions;
        private int subqueries;
        private boolean hasWildcard;
        private boolean hasOrderBy;

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
    }

    public AnalyzeResponse() {}

    public long getPredictedTime() { return predictedTime; }
    public void setPredictedTime(long predictedTime) { this.predictedTime = predictedTime; }
    public boolean isSlow() { return isSlow; }
    public void setSlow(boolean slow) { isSlow = slow; }
    public String getSuggestedIndex() { return suggestedIndex; }
    public void setSuggestedIndex(String suggestedIndex) { this.suggestedIndex = suggestedIndex; }
    public String getOptimizedQuery() { return optimizedQuery; }
    public void setOptimizedQuery(String optimizedQuery) { this.optimizedQuery = optimizedQuery; }
    public QueryFeatures getQueryFeatures() { return queryFeatures; }
    public void setQueryFeatures(QueryFeatures queryFeatures) { this.queryFeatures = queryFeatures; }
}
