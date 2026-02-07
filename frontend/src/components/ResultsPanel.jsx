import "./ResultsPanel.css";

export default function ResultsPanel({ result }) {
  if (!result) return null;

  const {
    predictedTime,
    isSlow,
    slow,
    suggestedIndex,
    suggestedIndexes,
    optimizedQuery,
    optimizationTips,
    queryFeatures,
  } = result;

  // Backend serializes "isSlow" as "slow" in JSON
  const isSlowQuery = isSlow || slow;

  return (
    <div className="results-panel">
      <h2>Analysis Results</h2>

      <div className="results-grid">
        {/* Performance Badge */}
        <div className="result-card performance-card">
          <span className="card-label">Performance</span>
          <span className={`badge ${isSlowQuery ? "badge-slow" : "badge-fast"}`}>
            {isSlowQuery ? "SLOW" : "FAST"}
          </span>
        </div>

        {/* Predicted Time */}
        <div className="result-card">
          <span className="card-label">Predicted Time</span>
          <span className="card-value">
            {predictedTime >= 1000
              ? `${(predictedTime / 1000).toFixed(1)}s`
              : `${predictedTime}ms`}
          </span>
        </div>

        {/* Query Type */}
        {queryFeatures?.queryType && (
          <div className="result-card">
            <span className="card-label">Query Type</span>
            <span className="card-value type-value">{queryFeatures.queryType}</span>
          </div>
        )}

        {/* Query Features */}
        <div className="result-card features-card">
          <span className="card-label">Query Features</span>
          {queryFeatures && (
            <div className="features-grid">
              <div className="feature">
                <span className="feature-value">{queryFeatures.tables?.length || 0}</span>
                <span className="feature-label">Tables</span>
              </div>
              <div className="feature">
                <span className="feature-value">{queryFeatures.joins}</span>
                <span className="feature-label">Joins</span>
              </div>
              <div className="feature">
                <span className="feature-value">{queryFeatures.conditions}</span>
                <span className="feature-label">Conditions</span>
              </div>
              <div className="feature">
                <span className="feature-value">{queryFeatures.subqueries}</span>
                <span className="feature-label">Subqueries</span>
              </div>
            </div>
          )}
          {/* Feature flags */}
          {queryFeatures && (
            <div className="feature-flags">
              {queryFeatures.hasWildcard && <span className="flag flag-warn">SELECT *</span>}
              {queryFeatures.hasOrderBy && <span className="flag">ORDER BY</span>}
              {queryFeatures.hasGroupBy && <span className="flag">GROUP BY</span>}
              {queryFeatures.hasDistinct && <span className="flag">DISTINCT</span>}
              {queryFeatures.hasLimit && <span className="flag flag-good">LIMIT</span>}
              {queryFeatures.hasHaving && <span className="flag">HAVING</span>}
            </div>
          )}
        </div>
      </div>

      {/* Optimization Tips */}
      {optimizationTips && optimizationTips.length > 0 && (
        <div className="result-section tips-section">
          <h3>Optimization Tips</h3>
          <ul className="tips-list">
            {optimizationTips.map((tip, i) => (
              <li key={i} className="tip-item">{tip}</li>
            ))}
          </ul>
        </div>
      )}

      {/* Suggested Indexes */}
      <div className="result-section">
        <h3>Suggested Indexes</h3>
        {suggestedIndexes && suggestedIndexes.length > 0 ? (
          <div className="index-list">
            {suggestedIndexes.map((idx, i) => (
              <pre key={i} className="code-block">{idx}</pre>
            ))}
          </div>
        ) : (
          <pre className="code-block">{suggestedIndex || "-- No index suggestions"}</pre>
        )}
      </div>

      {/* Optimized Query */}
      <div className="result-section">
        <h3>Optimized Query</h3>
        <pre className="code-block">{optimizedQuery}</pre>
      </div>
    </div>
  );
}
