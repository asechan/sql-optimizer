package com.sqloptimizer.service;

import com.sqloptimizer.service.SqlParserService.ParseResult;
import org.springframework.stereotype.Service;

import java.util.*;
import java.util.stream.Collectors;

@Service
public class IndexSuggestionService {

    public List<String> suggest(ParseResult result) {
        List<String> suggestions = new ArrayList<>();

        if (result.getTables().isEmpty()) {
            return suggestions;
        }

        String primaryTable = result.getTables().get(0);

    // 1. Index on WHERE columns
        List<String> whereColumns = result.getWhereColumns().stream()
                .distinct()
                .collect(Collectors.toList());

        if (!whereColumns.isEmpty()) {
            if (whereColumns.size() == 1) {
                suggestions.add(formatIndex(primaryTable, whereColumns));
            } else {
                // Composite index on all WHERE columns
                suggestions.add(formatIndex(primaryTable, whereColumns));
                // Individual indexes as alternatives
                for (String col : whereColumns) {
                    suggestions.add(formatIndex(primaryTable, List.of(col)));
                }
            }
        }

        // 2. Covering index: WHERE + ORDER BY
        if (!whereColumns.isEmpty() && !result.getOrderByColumns().isEmpty()) {
            List<String> coveringCols = new ArrayList<>(whereColumns);
            for (String ob : result.getOrderByColumns()) {
                if (!coveringCols.contains(ob)) {
                    coveringCols.add(ob);
                }
            }
            if (coveringCols.size() > whereColumns.size()) {
                suggestions.add(formatIndex(primaryTable, coveringCols));
            }
        }

        // 3. Index on ORDER BY alone (if no WHERE)
        if (whereColumns.isEmpty() && !result.getOrderByColumns().isEmpty()) {
            List<String> obCols = result.getOrderByColumns().stream()
                    .distinct()
                    .collect(Collectors.toList());
            suggestions.add(formatIndex(primaryTable, obCols));
        }

        // 4. GROUP BY index
        if (!result.getGroupByColumns().isEmpty()) {
            List<String> gbCols = result.getGroupByColumns().stream()
                    .distinct()
                    .collect(Collectors.toList());
            // Only add if not already suggested
            String gbIndex = formatIndex(primaryTable, gbCols);
            if (!suggestions.contains(gbIndex)) {
                suggestions.add(gbIndex);
            }
        }

        // 5. Wildcard warning
        if (result.isHasWildcard() && result.getJoins() > 0) {
            suggestions.add("-- TIP: Replace SELECT * with specific columns to enable covering-index optimization");
        }

        // De-duplicate while maintaining order
        return suggestions.stream().distinct().collect(Collectors.toList());
    }

    private String formatIndex(String table, List<String> columns) {
        String indexName = "idx_" + table + "_" + String.join("_", columns);
        String colList = String.join(", ", columns);
        return String.format("CREATE INDEX %s ON %s(%s);", indexName, table, colList);
    }
}
