package com.sqloptimizer.service;

import com.sqloptimizer.service.SqlParserService.ParseResult;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.http.*;
import org.springframework.stereotype.Service;
import org.springframework.web.client.RestTemplate;

import java.util.HashMap;
import java.util.Map;

/**
 * Client for the Python ML prediction service (FastAPI).
 * Sends parsed query features and receives execution-time predictions.
 * Falls back to a heuristic estimate if the ML service is unavailable.
 */
@Service
public class MlPredictionService {

    private static final Logger log = LoggerFactory.getLogger(MlPredictionService.class);

    private final RestTemplate restTemplate;
    private final String mlServiceUrl;

    public MlPredictionService(
            RestTemplate restTemplate,
            @Value("${ml.service.url:http://localhost:8000}") String mlServiceUrl) {
        this.restTemplate = restTemplate;
        this.mlServiceUrl = mlServiceUrl;
    }

    /**
     * Prediction result from the ML service.
     */
    public record PredictionResult(
            double predictedTimeMs,
            boolean isSlow,
            double slowProbability,
            String confidence,
            String source  // "ml" or "heuristic"
    ) {}

    /**
     * Call the ML service for a prediction. Falls back to heuristic on failure.
     */
    public PredictionResult predict(ParseResult parseResult, String sql) {
        try {
            return callMlService(parseResult, sql);
        } catch (Exception e) {
            log.warn("ML service unavailable, falling back to heuristic: {}", e.getMessage());
            return heuristicFallback(parseResult);
        }
    }

    private PredictionResult callMlService(ParseResult parseResult, String sql) {
        String url = mlServiceUrl + "/predict";

        Map<String, Object> body = new HashMap<>();
        body.put("num_tables", parseResult.getTables().size());
        body.put("num_joins", parseResult.getJoins());
        body.put("num_conditions", parseResult.getConditions());
        body.put("num_subqueries", parseResult.getSubqueries());
        body.put("has_wildcard", parseResult.isHasWildcard() ? 1 : 0);
        body.put("has_order_by", parseResult.isHasOrderBy() ? 1 : 0);
        body.put("has_group_by", parseResult.isHasGroupBy() ? 1 : 0);
        body.put("has_having", parseResult.isHasHaving() ? 1 : 0);
        body.put("has_distinct", parseResult.isHasDistinct() ? 1 : 0);
        body.put("has_limit", parseResult.isHasLimit() ? 1 : 0);
        body.put("num_where_columns", parseResult.getWhereColumns().size());
        body.put("num_order_columns", parseResult.getOrderByColumns().size());
        body.put("num_group_columns", parseResult.getGroupByColumns().size());
        body.put("query_length", sql.length());

        HttpHeaders headers = new HttpHeaders();
        headers.setContentType(MediaType.APPLICATION_JSON);
        HttpEntity<Map<String, Object>> request = new HttpEntity<>(body, headers);

        ResponseEntity<Map> response = restTemplate.exchange(
                url, HttpMethod.POST, request, Map.class);

        if (response.getStatusCode().is2xxSuccessful() && response.getBody() != null) {
            Map<String, Object> respBody = response.getBody();
            double predictedTime = ((Number) respBody.get("predicted_time_ms")).doubleValue();
            boolean isSlow = (Boolean) respBody.get("is_slow");
            double slowProba = ((Number) respBody.get("slow_probability")).doubleValue();
            String confidence = (String) respBody.get("confidence");

            log.info("ML prediction: {}ms (slow={}, confidence={})", predictedTime, isSlow, confidence);
            return new PredictionResult(predictedTime, isSlow, slowProba, confidence, "ml");
        }

        throw new RuntimeException("Empty response from ML service");
    }

    /**
     * Heuristic fallback (same logic as Phase 3 estimateTime).
     */
    private PredictionResult heuristicFallback(ParseResult r) {
        long base = 10;
        base += r.getTables().size() * 20L;
        base += r.getJoins() * 80L;
        base += r.getConditions() * 15L;
        base += r.getSubqueries() * 200L;
        if (r.isHasWildcard()) base += 50;
        if (r.isHasOrderBy()) base += 60;
        if (r.isHasGroupBy()) base += 70;
        if (r.isHasDistinct()) base += 40;
        if (!r.isHasLimit()) base += 30;

        boolean isSlow = base > 500;
        double slowProba = Math.min(1.0, base / 1000.0);

        return new PredictionResult(base, isSlow, slowProba, "low", "heuristic");
    }
}
