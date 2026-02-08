import { useState, useEffect, useRef, useCallback } from "react";
import QueryInput from "./components/QueryInput";
import ResultsPanel from "./components/ResultsPanel";
import SwirlBackground from "./components/SwirlBackground";
import { analyzeQuery } from "./api";
import { mockAnalysis } from "./mockData";
import "./App.css";

function App() {
  const [result, setResult] = useState(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState(null);
  const [introDone, setIntroDone] = useState(false);
  const cursorGlowRef = useRef(null);
  const noiseSpotRef = useRef(null);
  const rafRef = useRef(null);
  const mousePos = useRef({ x: 0, y: 0 });

  // Cursor-following glow + noise spotlight
  const handleMouseMove = useCallback((e) => {
    mousePos.current = { x: e.clientX, y: e.clientY };
    if (!rafRef.current) {
      rafRef.current = requestAnimationFrame(() => {
        const { x, y } = mousePos.current;
        if (cursorGlowRef.current) {
          cursorGlowRef.current.style.transform = `translate(${x}px, ${y}px)`;
        }
        if (noiseSpotRef.current) {
          noiseSpotRef.current.style.transform = `translate(${x}px, ${y}px)`;
        }
        rafRef.current = null;
      });
    }
  }, []);

  useEffect(() => {
    window.addEventListener("mousemove", handleMouseMove);
    return () => {
      window.removeEventListener("mousemove", handleMouseMove);
      if (rafRef.current) cancelAnimationFrame(rafRef.current);
    };
  }, [handleMouseMove]);

  // Intro animation timer
  useEffect(() => {
    const timer = setTimeout(() => setIntroDone(true), 1800);
    return () => clearTimeout(timer);
  }, []);

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
      setError("Backend offline -- showing mock data");
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <>
      {/* Cursor glow */}
      <div className="cursor-glow" ref={cursorGlowRef} />

      {/* Noise texture overlay (always visible, brighter near cursor) */}
      <div className="noise-overlay" />
      <div className="noise-spotlight" ref={noiseSpotRef} />

      {/* Ambient swirl canvas background */}
      <SwirlBackground />

      {/* Intro overlay */}
      <div className={`intro-overlay ${introDone ? "intro-done" : ""}`}>
        <div className="intro-content">
          <div className="intro-title">SQL Query Optimizer</div>
          <div className="intro-line" />
          <div className="intro-sub">AI-Powered Analysis</div>
        </div>
      </div>

      <div className={`app ${introDone ? "app-visible" : "app-hidden"}`}>
        <header className="app-header">
          <div className="logo">
            <h1>SQL Query Optimizer</h1>
          </div>
          <div className="header-line" />
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
                <div className="spinner-container">
                  <div className="spinner" />
                </div>
                <span>Analyzing query</span>
                <div className="loading-progress" />
              </div>
            )}
            <ResultsPanel result={result} />
          </section>
        </main>

        <footer className="app-footer">
          <span>AI SQL Optimizer - Built with Spring Boot, FastAPI &amp; React</span>
          <span className="footer-credit">Made by Asechan Chib</span>
        </footer>
      </div>
    </>
  );
}

export default App;
