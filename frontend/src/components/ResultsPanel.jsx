import { useEffect, useRef } from "react";
import "./ResultsPanel.css";

export default function ResultsPanel({ result }) {
  const panelRef = useRef(null);

  // Trigger stagger animation on mount
  useEffect(() => {
    if (!result || !panelRef.current) return;
    const cards = panelRef.current.querySelectorAll(".result-card, .result-section");
    cards.forEach((card, i) => {
      card.style.animationDelay = `${i * 0.07}s`;
    });
  }, [result]);

  if (!result) return null;

  const {
    predictedTime,
    isSlow,
    slow,
    slowProbability,
    confidence,
    predictionSource,
    suggestedIndex,
    suggestedIndexes,
    optimizedQuery,
    optimizationTips,
    queryFeatures,
  } = result;

  const isSlowQuery = isSlow || slow;
  const slowPct = slowProbability != null ? (slowProbability * 100).toFixed(1) : null;

  const formatTime = (ms) => {
    if (ms >= 1000) return `${(ms / 1000).toFixed(1)}s`;
    return `${ms}ms`;
  };

  return (
    <div className="results-panel" ref={panelRef}>
      <div className="rp-header">
        <h2>Analysis Results</h2>
        <div className="rp-header-line" />
      </div>

      {/* ---- Metric Cards Grid ---- */}
      <div className="results-grid">
        {/* Performance */}
        <div className={`result-card performance-card ${isSlowQuery ? "card-slow" : "card-fast"}`}>
          <span className="card-label">Performance</span>
          <span className={`perf-badge ${isSlowQuery ? "badge-slow" : "badge-fast"}`}>
            {isSlowQuery ? "SLOW" : "FAST"}
          </span>
          <div className="perf-indicator">
            <div
              className={`perf-bar ${isSlowQuery ? "bar-slow" : "bar-fast"}`}
              style={{ "--bar-width": isSlowQuery ? "85%" : "25%" }}
            />
          </div>
        </div>

        {/* Predicted Time */}
        <div className="result-card time-card">
          <span className="card-label">Predicted Time</span>
          <span className="card-value value-time">{formatTime(predictedTime)}</span>
        </div>

        {/* Confidence */}
        {confidence && (
          <div className="result-card">
            <span className="card-label">Confidence</span>
            <span className={`card-value confidence-val confidence-${confidence}`}>
              {confidence.toUpperCase()}
            </span>
          </div>
        )}

        {/* Slow Probability */}
        {slowPct != null && (
          <div className="result-card">
            <span className="card-label">Slow Probability</span>
            <span className="card-value">{slowPct}%</span>
            <div className="prob-bar-track">
              <div
                className="prob-bar-fill"
                style={{ "--prob": `${slowPct}%` }}
              />
            </div>
          </div>
        )}

        {/* Source */}
        {predictionSource && (
          <div className="result-card">
            <span className="card-label">Source</span>
            <span className={`card-value source-tag source-${predictionSource}`}>
              {predictionSource === "ml" ? "ML Model" : "Heuristic"}
            </span>
          </div>
        )}

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
              {[
                { v: queryFeatures.tables?.length || 0, l: "Tables" },
                { v: queryFeatures.joins, l: "Joins" },
                { v: queryFeatures.conditions, l: "Conditions" },
                { v: queryFeatures.subqueries, l: "Subqueries" },
              ].map(({ v, l }) => (
                <div className="feature" key={l}>
                  <span className="feature-value">{v}</span>
                  <span className="feature-label">{l}</span>
                </div>
              ))}
            </div>
          )}
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

      {/* ---- Optimization Tips ---- */}
      {optimizationTips && optimizationTips.length > 0 && (
        <div className="result-section tips-section">
          <h3>Optimization Tips</h3>
          <ul className="tips-list">
            {optimizationTips.map((tip, i) => (
              <li key={i} className="tip-item" style={{ animationDelay: `${0.6 + i * 0.1}s` }}>
                <span className="tip-marker">{String(i + 1).padStart(2, "0")}</span>
                <span className="tip-text">{tip}</span>
              </li>
            ))}
          </ul>
        </div>
      )}

      {/* ---- Suggested Indexes ---- */}
      <div className="result-section">
        <h3>Suggested Indexes</h3>
        {suggestedIndexes && suggestedIndexes.length > 0 ? (
          <div className="index-list">
            {suggestedIndexes.map((idx, i) => (
              <pre key={i} className="code-block" style={{ animationDelay: `${0.7 + i * 0.08}s` }}>
                {idx}
              </pre>
            ))}
          </div>
        ) : (
          <pre className="code-block">{suggestedIndex || "-- No index suggestions"}</pre>
        )}
      </div>

      {/* ---- Optimized Query ---- */}
      <div className="result-section">
        <h3>Optimized Query</h3>
        <pre className="code-block code-optimized">{optimizedQuery}</pre>
      </div>
    </div>
  );
}
