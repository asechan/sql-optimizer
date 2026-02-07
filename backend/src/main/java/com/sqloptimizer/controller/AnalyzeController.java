package com.sqloptimizer.controller;

import com.sqloptimizer.dto.AnalyzeRequest;
import com.sqloptimizer.dto.AnalyzeResponse;
import com.sqloptimizer.dto.AnalyzeResponse.QueryFeatures;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

import java.util.List;

/**
 * REST controller for SQL query analysis.
 * Phase 2: returns a fixed dummy response.
 * Phase 3+: will integrate real SQL parsing & ML prediction.
 */
@RestController
@RequestMapping("/api")
public class AnalyzeController {

    @PostMapping("/analyze")
    public ResponseEntity<AnalyzeResponse> analyze(@RequestBody AnalyzeRequest request) {

        // Phase 2: fixed dummy response — will be replaced with real logic
        AnalyzeResponse response = new AnalyzeResponse();
        response.setPredictedTime(120);
        response.setSlow(true);
        response.setSuggestedIndex("CREATE INDEX idx_user_id ON users(id);");
        response.setOptimizedQuery("SELECT id, name FROM users WHERE id = ?");
        response.setQueryFeatures(new QueryFeatures(
                List.of("users", "orders"),
                1,   // joins
                2,   // conditions
                0,   // subqueries
                true, // hasWildcard
                true  // hasOrderBy
        ));

        return ResponseEntity.ok(response);
    }
}
