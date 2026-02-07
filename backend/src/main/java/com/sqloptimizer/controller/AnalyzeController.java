package com.sqloptimizer.controller;

import com.sqloptimizer.dto.AnalyzeRequest;
import com.sqloptimizer.dto.AnalyzeResponse;
import com.sqloptimizer.dto.AnalyzeResponse.QueryFeatures;
import com.sqloptimizer.service.IndexSuggestionService;
import com.sqloptimizer.service.QueryOptimizerService;
import com.sqloptimizer.service.QueryOptimizerService.OptimizationResult;
import com.sqloptimizer.service.SqlParserService;
import com.sqloptimizer.service.SqlParserService.ParseResult;
import net.sf.jsqlparser.JSQLParserException;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

import java.util.List;
import java.util.Map;

/**
 * REST controller for SQL query analysis.
 * Phase 3: real SQL parsing via JSqlParser, rule-based index suggestions
 * and query optimization hints.
 */
@RestController
@RequestMapping("/api")
public class AnalyzeController {

    private final SqlParserService sqlParserService;
    private final IndexSuggestionService indexSuggestionService;
    private final QueryOptimizerService queryOptimizerService;

    public AnalyzeController(SqlParserService sqlParserService,
                             IndexSuggestionService indexSuggestionService,
                             QueryOptimizerService queryOptimizerService) {
        this.sqlParserService = sqlParserService;
        this.indexSuggestionService = indexSuggestionService;
        this.queryOptimizerService = queryOptimizerService;
    }

    @PostMapping("/analyze")
    public ResponseEntity<?> analyze(@RequestBody AnalyzeRequest request) {

        String sql = request.getQuery();
        if (sql == null || sql.isBlank()) {
            return ResponseEntity.badRequest()
                    .body(Map.of("error", "Query must not be empty"));
        }

        // --- Parse the SQL query ---
        ParseResult parseResult;
        try {
            parseResult = sqlParserService.parse(sql);
        } catch (JSQLParserException e) {
            return ResponseEntity.badRequest()
                    .body(Map.of("error", "Invalid SQL: " + e.getMessage()));
        }

        // --- Build query features ---
        QueryFeatures features = new QueryFeatures(
                parseResult.getTables(),
                parseResult.getJoins(),
                parseResult.getConditions(),
                parseResult.getSubqueries(),
                parseResult.isHasWildcard(),
                parseResult.isHasOrderBy()
        );
        features.setHasGroupBy(parseResult.isHasGroupBy());
        features.setHasHaving(parseResult.isHasHaving());
        features.setHasDistinct(parseResult.isHasDistinct());
        features.setHasLimit(parseResult.isHasLimit());
        features.setWhereColumns(parseResult.getWhereColumns());
        features.setOrderByColumns(parseResult.getOrderByColumns());
        features.setGroupByColumns(parseResult.getGroupByColumns());
        features.setQueryType(parseResult.getQueryType());

        // --- Index suggestions ---
        List<String> indexSuggestions = indexSuggestionService.suggest(parseResult);

        // --- Query optimization ---
        OptimizationResult optimization = queryOptimizerService.optimize(sql, parseResult);

        // --- Heuristic-based predicted time (placeholder until ML model in Phase 5) ---
        long predictedTime = estimateTime(parseResult);
        boolean isSlow = predictedTime > 500;

        // --- Assemble response ---
        AnalyzeResponse response = new AnalyzeResponse();
        response.setPredictedTime(predictedTime);
        response.setSlow(isSlow);
        response.setSuggestedIndex(indexSuggestions.isEmpty() ? "-- No index suggestions" : indexSuggestions.get(0));
        response.setSuggestedIndexes(indexSuggestions);
        response.setOptimizedQuery(optimization.getOptimizedQuery());
        response.setOptimizationTips(optimization.getTips());
        response.setQueryFeatures(features);

        return ResponseEntity.ok(response);
    }

    /**
     * Simple heuristic to estimate query execution time (ms).
     * Will be replaced by ML prediction in Phase 5.
     */
    private long estimateTime(ParseResult r) {
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
        return base;
    }
}
