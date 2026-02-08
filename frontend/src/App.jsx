import { useState } from "react";
import QueryInput from "./components/QueryInput";
import ResultsPanel from "./components/ResultsPanel";
import { analyzeQuery } from "./api";
import { mockAnalysis } from "./mockData";
import "./App.css";

function App() {
  const [result, setResult] = useState(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState(null);

  const handleAnalyze = async (query) => {
    setIsLoading(true);
    setResult(null);
    setError(null);

    try {
      const data = await analyzeQuery(query);
      setResult({ ...data, originalQuery: query });
    } catch (err) {
      console.warn("Backend unavailable, using mock data:", err.message);
      setResult({ ...mockAnalysis, originalQuery: query });
      setError("Backend offline — showing mock data");
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="app">
      <header className="app-header">
        <div className="logo">
          <span className="logo-icon">⚡</span>
          <h1>SQL Query Optimizer</h1>
        </div>
        <p className="tagline">AI-powered query analysis and optimization</p>
      </header>

      <main className="app-main">
        <section className="input-section">
          <QueryInput onAnalyze={handleAnalyze} isLoading={isLoading} />
        </section>

        <section className="results-section">
          {error && <div className="error-banner">{error}</div>}
          {isLoading && (
            <div className="loading">
              <div className="spinner" />
              <span>Analyzing query...</span>
            </div>
          )}
          <ResultsPanel result={result} />
        </section>
      </main>

      <footer className="app-footer">
        <span>AI SQL Optimizer</span>
      </footer>
    </div>
  );
}

export default App;
