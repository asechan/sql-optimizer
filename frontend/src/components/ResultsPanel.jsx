import "./ResultsPanel.css";

export default function ResultsPanel({ result }) {
  if (!result) return null;

  const { predictedTime, isSlow, suggestedIndex, optimizedQuery, queryFeatures } = result;

  return (
    <div className="results-panel">
      <h2>Analysis Results</h2>

      <div className="results-grid">
        {/* Performance Badge */}
        <div className="result-card performance-card">
          <span className="card-label">Performance</span>
          <span className={`badge ${isSlow ? "badge-slow" : "badge-fast"}`}>
            {isSlow ? "SLOW" : "FAST"}
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
        </div>
      </div>

      {/* Suggested Index */}
      <div className="result-section">
        <h3>Suggested Index</h3>
        <pre className="code-block">{suggestedIndex}</pre>
      </div>

      {/* Optimized Query */}
      <div className="result-section">
        <h3>Optimized Query</h3>
        <pre className="code-block">{optimizedQuery}</pre>
      </div>
    </div>
  );
}
