import { useEffect, useState } from "react";
import QueryInput from "./components/QueryInput";
import ResultsPanel from "./components/ResultsPanel";
import DotGrid from "./components/DotGrid";
import LightRays from "./components/LightRays";
import { analyzeQuery } from "./api";
import { mockAnalysis } from "./mockData";
import "./App.css";

function App() {
  const [result, setResult] = useState(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState(null);
  const [atScrollEnd, setAtScrollEnd] = useState(false);

  useEffect(() => {
    const handleScroll = () => {
      const doc = document.documentElement;
      const bottomReached = window.scrollY + window.innerHeight >= doc.scrollHeight - 6;
      setAtScrollEnd(bottomReached);
    };

    const observer = new IntersectionObserver(
      (entries) => {
        entries.forEach((entry) => {
          entry.target.classList.toggle("is-centered", entry.isIntersecting);
        });
      },
      { threshold: 0.45 }
    );

    const stages = document.querySelectorAll(".scroll-stage");
    stages.forEach((stage) => observer.observe(stage));

    window.addEventListener("scroll", handleScroll, { passive: true });
    handleScroll();

    return () => {
      window.removeEventListener("scroll", handleScroll);
      observer.disconnect();
    };
  }, []);

  useEffect(() => {
    const cards = Array.from(document.querySelectorAll(".rb-border-glow"));
    if (!cards.length) return undefined;

    const sensitivity = 112;
    const cleanups = [];

    cards.forEach((card) => {
      let rafId = 0;
      let px = 50;
      let py = 50;
      let pa = 0;

      const render = () => {
        rafId = 0;
        card.style.setProperty("--bg-x", `${px}%`);
        card.style.setProperty("--bg-y", `${py}%`);
        card.style.setProperty("--bg-alpha", pa.toFixed(3));
      };

      const schedule = () => {
        if (!rafId) rafId = window.requestAnimationFrame(render);
      };

      const onMove = (event) => {
        const rect = card.getBoundingClientRect();
        const x = event.clientX - rect.left;
        const y = event.clientY - rect.top;

        px = (x / rect.width) * 100;
        py = (y / rect.height) * 100;

        const minEdge = Math.min(x, y, rect.width - x, rect.height - y);
        const edgeFactor = Math.max(0, 1 - minEdge / sensitivity);
        pa = Math.min(1, Math.pow(edgeFactor, 0.55) * 1.15);
        schedule();
      };

      const onLeave = () => {
        pa = 0;
        schedule();
      };

      card.addEventListener("pointermove", onMove);
      card.addEventListener("pointerleave", onLeave);

      cleanups.push(() => {
        if (rafId) window.cancelAnimationFrame(rafId);
        card.removeEventListener("pointermove", onMove);
        card.removeEventListener("pointerleave", onLeave);
      });
    });

    return () => {
      cleanups.forEach((fn) => fn());
    };
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
    <div className="app-shell">
      <div className="mesh mesh-a" />
      <div className="mesh mesh-b" />
      <LightRays
        raysOrigin="right"
        raysColor="#ffffff"
        raysSpeed={0.7}
        lightSpread={0.5}
        rayLength={3}
        followMouse={false}
        mouseInfluence={0}
        noiseAmount={0.03}
        distortion={0.1}
        fadeDistance={1}
        saturation={1}
        className="base-rays"
      />
      <DotGrid
        dotSize={2.4}
        gap={16}
        baseColor="#1b2940"
        activeColor="#79b9f5"
        proximity={125}
        shockRadius={230}
        shockStrength={4.2}
        resistance={760}
        returnDuration={1.45}
        className="dotgrid-bg"
      />
      <div className="grain" />


      <div className="app">
        <header className="topbar scroll-stage is-centered">
          <div className="brand-block">
            <p className="brand-name">AI SQL OPTIMIZER</p>
          </div>
        </header>

        <section className="hero scroll-stage is-centered">
          <h1>Ship faster queries with premium-grade analysis</h1>
          <p className="tagline">
            Drop in a SQL statement and get execution risk, index guidance, and rewrite recommendations in seconds.
          </p>
        </section>

        <main className="app-main scroll-stage is-centered">
          <section className="panel input-section magic-bento-card rb-border-glow">
            <div className="section-head">
              <h2>Query Studio</h2>
              <span>Paste, edit, analyze</span>
            </div>
            <QueryInput onAnalyze={handleAnalyze} isLoading={isLoading} />
          </section>

          <section className="panel results-section magic-bento-card rb-border-glow">
            <div className="section-head">
              <h2>Performance Report</h2>
              <span>Prediction, tips, rewrites</span>
            </div>
            {error && <div className="error-banner">{error}</div>}
            {isLoading && (
              <div className="loading">
                <div className="spinner-container">
                  <div className="spinner" />
                </div>
                <span>Running analysis...</span>
                <div className="loading-progress" />
              </div>
            )}
            <ResultsPanel result={result} />
          </section>
        </main>
      </div>
    </div>
  );
}

export default App;
