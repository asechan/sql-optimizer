import { useCallback, useEffect, useMemo, useRef } from "react";
import "./DotGrid.css";

function hexToRgb(hex) {
  const m = hex.match(/^#?([a-f\d]{2})([a-f\d]{2})([a-f\d]{2})$/i);
  if (!m) return { r: 0, g: 0, b: 0 };
  return {
    r: parseInt(m[1], 16),
    g: parseInt(m[2], 16),
    b: parseInt(m[3], 16),
  };
}

function lerp(a, b, t) {
  return a + (b - a) * t;
}

export default function DotGrid({
  dotSize = 5,
  gap = 15,
  baseColor = "#1c283d",
  activeColor = "#7ccff9",
  proximity = 120,
  shockRadius = 250,
  shockStrength = 5,
  resistance = 750,
  returnDuration = 1.5,
  className = "",
  style,
}) {
  const wrapperRef = useRef(null);
  const canvasRef = useRef(null);
  const dotsRef = useRef([]);
  const rafRef = useRef(0);
  const pointerRafRef = useRef(0);

  const pointerRef = useRef({
    x: -9999,
    y: -9999,
    vx: 0,
    vy: 0,
    speed: 0,
    lastX: 0,
    lastY: 0,
    lastTime: 0,
    pendingX: 0,
    pendingY: 0,
  });

  const baseRgb = useMemo(() => hexToRgb(baseColor), [baseColor]);
  const activeRgb = useMemo(() => hexToRgb(activeColor), [activeColor]);

  const buildGrid = useCallback(() => {
    const canvas = canvasRef.current;
    const wrap = wrapperRef.current;
    if (!canvas || !wrap) return;

    const dpr = Math.min(window.devicePixelRatio || 1, 2);
    const width = Math.floor(wrap.clientWidth);
    const height = Math.floor(wrap.clientHeight);

    canvas.width = Math.floor(width * dpr);
    canvas.height = Math.floor(height * dpr);
    canvas.style.width = `${width}px`;
    canvas.style.height = `${height}px`;

    const ctx = canvas.getContext("2d", { alpha: true });
    if (!ctx) return;
    ctx.setTransform(dpr, 0, 0, dpr, 0, 0);

    const dots = [];
    const offsetX = gap / 2;
    const offsetY = gap / 2;

    for (let y = offsetY; y < height; y += gap) {
      for (let x = offsetX; x < width; x += gap) {
        dots.push({ x, y, glow: 0, shock: 0 });
      }
    }

    dotsRef.current = dots;
  }, [gap]);

  useEffect(() => {
    buildGrid();
    const onResize = () => buildGrid();
    window.addEventListener("resize", onResize);
    return () => window.removeEventListener("resize", onResize);
  }, [buildGrid]);

  useEffect(() => {
    const onMove = (e) => {
      const wrap = wrapperRef.current;
      if (!wrap) return;

      const rect = wrap.getBoundingClientRect();
      const p = pointerRef.current;
      p.pendingX = e.clientX - rect.left;
      p.pendingY = e.clientY - rect.top;

      if (pointerRafRef.current) return;
      pointerRafRef.current = window.requestAnimationFrame((time) => {
        pointerRafRef.current = 0;
        const now = time || performance.now();
        const dt = Math.max((now - (p.lastTime || now)) / 1000, 0.001);
        const dx = p.pendingX - p.lastX;
        const dy = p.pendingY - p.lastY;

        p.vx = dx / dt;
        p.vy = dy / dt;
        p.speed = Math.min(Math.hypot(p.vx, p.vy), 5000);
        p.x = p.pendingX;
        p.y = p.pendingY;
        p.lastX = p.pendingX;
        p.lastY = p.pendingY;
        p.lastTime = now;
      });
    };

    const onLeave = () => {
      const p = pointerRef.current;
      p.x = -9999;
      p.y = -9999;
      p.speed = 0;
    };

    window.addEventListener("pointermove", onMove, { passive: true });
    window.addEventListener("pointerleave", onLeave);

    return () => {
      if (pointerRafRef.current) window.cancelAnimationFrame(pointerRafRef.current);
      window.removeEventListener("pointermove", onMove);
      window.removeEventListener("pointerleave", onLeave);
    };
  }, []);

  useEffect(() => {
    let last = performance.now();

    const tick = (now) => {
      const dt = Math.min((now - last) / 1000, 0.05);
      last = now;

      const canvas = canvasRef.current;
      if (!canvas) {
        rafRef.current = requestAnimationFrame(tick);
        return;
      }

      const dpr = Math.min(window.devicePixelRatio || 1, 2);
      const width = canvas.width / dpr;
      const height = canvas.height / dpr;
      const ctx = canvas.getContext("2d", { alpha: true });
      if (!ctx) {
        rafRef.current = requestAnimationFrame(tick);
        return;
      }

      ctx.clearRect(0, 0, width, height);

      const p = pointerRef.current;
      const dots = dotsRef.current;
      const speedFactor = Math.min(p.speed / 1200, 1) * shockStrength;
      const decay = Math.exp(-dt * (resistance / 120));
      const settle = Math.min(dt / Math.max(returnDuration, 0.08) * 6, 1);

      for (let i = 0; i < dots.length; i += 1) {
        const dot = dots[i];
        const dx = p.x - dot.x;
        const dy = p.y - dot.y;
        const dist = Math.hypot(dx, dy);

        const near = Math.max(0, 1 - dist / proximity);
        const shock = Math.max(0, 1 - dist / shockRadius) * speedFactor;

        dot.shock = dot.shock * decay + shock * 0.2;
        const target = Math.max(near, Math.min(dot.shock, 1));
        dot.glow = lerp(dot.glow, target, settle);

        const t = Math.min(dot.glow, 1);
        const r = Math.round(lerp(baseRgb.r, activeRgb.r, t));
        const g = Math.round(lerp(baseRgb.g, activeRgb.g, t));
        const b = Math.round(lerp(baseRgb.b, activeRgb.b, t));

        const radius = dotSize * 0.5 + t * dotSize * 0.45;

        ctx.beginPath();
        ctx.fillStyle = `rgba(${r}, ${g}, ${b}, ${0.35 + t * 0.65})`;
        ctx.arc(dot.x, dot.y, radius, 0, Math.PI * 2);
        ctx.fill();
      }

      rafRef.current = requestAnimationFrame(tick);
    };

    rafRef.current = requestAnimationFrame(tick);
    return () => cancelAnimationFrame(rafRef.current);
  }, [
    activeRgb.b,
    activeRgb.g,
    activeRgb.r,
    baseRgb.b,
    baseRgb.g,
    baseRgb.r,
    dotSize,
    proximity,
    resistance,
    returnDuration,
    shockRadius,
    shockStrength,
  ]);

  return (
    <div ref={wrapperRef} className={`dot-grid ${className}`.trim()} style={style} aria-hidden="true">
      <div className="dot-grid__wrap">
        <canvas ref={canvasRef} className="dot-grid__canvas" />
      </div>
    </div>
  );
}
