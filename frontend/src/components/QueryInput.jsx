import { useState, useRef, useCallback } from "react";
import "./QueryInput.css";

export default function QueryInput({ onAnalyze, isLoading }) {
  const [query, setQuery] = useState(
    "SELECT * FROM users u JOIN orders o ON u.id = o.user_id WHERE u.active = 1 ORDER BY o.created_at DESC;"
  );
  const [isFocused, setIsFocused] = useState(false);
  const buttonRef = useRef(null);

  const handleSubmit = (e) => {
    e.preventDefault();
    if (query.trim()) {
      onAnalyze(query.trim());
    }
  };

  const handleRipple = useCallback((e) => {
    const button = buttonRef.current;
    if (!button) return;
    const rect = button.getBoundingClientRect();
    const ripple = document.createElement("span");
    ripple.className = "btn-ripple";
    ripple.style.left = `${e.clientX - rect.left}px`;
    ripple.style.top = `${e.clientY - rect.top}px`;
    button.appendChild(ripple);
    setTimeout(() => ripple.remove(), 600);
  }, []);

  const lineCount = query.split("\n").length;

  return (
    <form className="query-input" onSubmit={handleSubmit}>
      <div className="qi-header">
        <label htmlFor="sql-input">SQL Query</label>
        <span className="qi-meta">
          {query.length} chars / {lineCount} {lineCount === 1 ? "line" : "lines"}
        </span>
      </div>

      <div className={`textarea-wrapper ${isFocused ? "focused" : ""}`}>
        <div className="line-numbers" aria-hidden="true">
          {Array.from({ length: Math.max(lineCount, 6) }, (_, i) => (
            <span key={i + 1}>{i + 1}</span>
          ))}
        </div>
        <textarea
          id="sql-input"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          onFocus={() => setIsFocused(true)}
          onBlur={() => setIsFocused(false)}
          placeholder="Enter your SQL query here..."
          rows={6}
          spellCheck={false}
          autoComplete="off"
        />
      </div>

      <div className="qi-actions">
        <button
          ref={buttonRef}
          type="submit"
          className={`analyze-btn ${isLoading ? "loading" : ""}`}
          disabled={isLoading || !query.trim()}
          onClick={handleRipple}
        >
          <span className="btn-text">
            {isLoading ? "Analyzing" : "Analyze Query"}
          </span>
          {isLoading && <span className="btn-dots"><i/><i/><i/></span>}
        </button>
      </div>
    </form>
  );
}
