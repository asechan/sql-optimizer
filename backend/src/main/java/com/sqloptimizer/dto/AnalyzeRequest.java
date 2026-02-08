package com.sqloptimizer.dto;

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
