package com.sqloptimizer.dto;

/**
 * Request body for the /analyze endpoint.
 */
public class AnalyzeRequest {

    private String query;

    public AnalyzeRequest() {}

    public AnalyzeRequest(String query) {
        this.query = query;
    }

    public String getQuery() {
        return query;
    }

    public void setQuery(String query) {
        this.query = query;
    }
}
