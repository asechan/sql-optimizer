package com.sqloptimizer.controller;

import com.sqloptimizer.dto.AnalyzeRequest;
import com.sqloptimizer.dto.AnalyzeResponse;
import com.sqloptimizer.dto.AnalyzeResponse.QueryFeatures;
import com.sqloptimizer.service.IndexSuggestionService;
import com.sqloptimizer.service.MlPredictionService;
import com.sqloptimizer.service.MlPredictionService.PredictionResult;
import com.sqloptimizer.service.QueryOptimizerService;
import com.sqloptimizer.service.QueryOptimizerService.OptimizationResult;
import com.sqloptimizer.service.SqlParserService;
import com.sqloptimizer.service.SqlParserService.ParseResult;
import net.sf.jsqlparser.JSQLParserException;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

import java.util.List;
import java.util.Map;

@RestController
@RequestMapping("/api")
public class AnalyzeController {

    @GetMapping("/health")
    public ResponseEntity<Map<String, String>> health() {
        return ResponseEntity.ok(Map.of("status", "UP"));
    }

    private final SqlParserService sqlParserService;
    private final IndexSuggestionService indexSuggestionService;
    private final QueryOptimizerService queryOptimizerService;
    private final MlPredictionService mlPredictionService;

    public AnalyzeController(SqlParserService sqlParserService,
                             IndexSuggestionService indexSuggestionService,
                             QueryOptimizerService queryOptimizerService,
                             MlPredictionService mlPredictionService) {
        this.sqlParserService = sqlParserService;
        this.indexSuggestionService = indexSuggestionService;
        this.queryOptimizerService = queryOptimizerService;
        this.mlPredictionService = mlPredictionService;
    }

    @PostMapping("/analyze")
    public ResponseEntity<?> analyze(@RequestBody AnalyzeRequest request) {

        String sql = request.getQuery();
        if (sql == null || sql.isBlank()) {
            return ResponseEntity.badRequest()
                    .body(Map.of("error", "Query must not be empty"));
        }

        ParseResult parseResult;
        try {
            parseResult = sqlParserService.parse(sql);
        } catch (JSQLParserException e) {
            return ResponseEntity.badRequest()
                    .body(Map.of("error", "Invalid SQL: " + e.getMessage()));
        }

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

        List<String> indexSuggestions = indexSuggestionService.suggest(parseResult);
        OptimizationResult optimization = queryOptimizerService.optimize(sql, parseResult);
        PredictionResult prediction = mlPredictionService.predict(parseResult, sql);

        AnalyzeResponse response = new AnalyzeResponse();
        response.setPredictedTime(Math.round(prediction.predictedTimeMs()));
        response.setSlow(prediction.isSlow());
        response.setSlowProbability(prediction.slowProbability());
        response.setConfidence(prediction.confidence());
        response.setPredictionSource(prediction.source());
        response.setSuggestedIndex(indexSuggestions.isEmpty() ? "-- No index suggestions" : indexSuggestions.get(0));
        response.setSuggestedIndexes(indexSuggestions);
        response.setOptimizedQuery(optimization.getOptimizedQuery());
        response.setOptimizationTips(optimization.getTips());
        response.setQueryFeatures(features);

        return ResponseEntity.ok(response);
    }
}
