import { useState } from "react";
import "./QueryInput.css";

export default function QueryInput({ onAnalyze, isLoading }) {
  const [query, setQuery] = useState(
    "SELECT * FROM users u JOIN orders o ON u.id = o.user_id WHERE u.active = 1 ORDER BY o.created_at DESC;"
  );

  const handleSubmit = (e) => {
    e.preventDefault();
    if (query.trim()) {
      onAnalyze(query.trim());
    }
  };

  return (
    <form className="query-input" onSubmit={handleSubmit}>
      <label htmlFor="sql-input">SQL Query</label>
      <textarea
        id="sql-input"
        value={query}
        onChange={(e) => setQuery(e.target.value)}
        placeholder="Enter your SQL query here..."
        rows={6}
        spellCheck={false}
      />
      <button type="submit" disabled={isLoading || !query.trim()}>
        {isLoading ? "Analyzing..." : "Analyze Query"}
      </button>
    </form>
  );
}
