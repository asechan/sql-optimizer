import { useEffect, useMemo, useRef } from "react";
import "./MagnetLines.css";

export default function MagnetLines({
  rows = 9,
  columns = 9,
  containerSize = "80vmin",
  lineColor = "#efefef",
  lineWidth = "1vmin",
  lineHeight = "6vmin",
  baseAngle = -10,
  className = "",
  style = {},
}) {
  const containerRef = useRef(null);

  useEffect(() => {
    const container = containerRef.current;
    if (!container) return undefined;

    const items = Array.from(container.querySelectorAll("span"));
    let centers = [];
    let rafId = 0;
    let resizeRaf = 0;
    let pending = null;

    const refreshCenters = () => {
      centers = items.map((item) => {
        const rect = item.getBoundingClientRect();
        return {
          cx: rect.x + rect.width / 2,
          cy: rect.y + rect.height / 2,
          item,
        };
      });
    };

    const render = () => {
      rafId = 0;
      if (!pending) return;

      const { x, y } = pending;
      centers.forEach(({ cx, cy, item }) => {
        const b = x - cx;
        const a = y - cy;
        const r = (Math.atan2(a, b) * 180) / Math.PI;
        item.style.setProperty("--rotate", `${r}deg`);
      });
    };

    const onPointerMove = (event) => {
      pending = { x: event.clientX, y: event.clientY };
      if (!rafId) rafId = window.requestAnimationFrame(render);
    };

    const onResize = () => {
      if (resizeRaf) window.cancelAnimationFrame(resizeRaf);
      resizeRaf = window.requestAnimationFrame(refreshCenters);
    };

    refreshCenters();
    window.addEventListener("pointermove", onPointerMove, { passive: true });
    window.addEventListener("resize", onResize);

    if (centers.length) {
      const middle = centers[Math.floor(centers.length / 2)];
      pending = { x: middle.cx, y: middle.cy };
      rafId = window.requestAnimationFrame(render);
    }

    return () => {
      if (rafId) window.cancelAnimationFrame(rafId);
      if (resizeRaf) window.cancelAnimationFrame(resizeRaf);
      window.removeEventListener("pointermove", onPointerMove);
      window.removeEventListener("resize", onResize);
    };
  }, []);

  const spans = useMemo(() => {
    return Array.from({ length: rows * columns }, (_, i) => (
      <span
        key={i}
        style={{
          "--rotate": `${baseAngle}deg`,
          backgroundColor: lineColor,
          width: lineWidth,
          height: lineHeight,
        }}
      />
    ));
  }, [baseAngle, columns, lineColor, lineHeight, lineWidth, rows]);

  return (
    <div
      ref={containerRef}
      className={`magnetLines-container ${className}`.trim()}
      style={{
        display: "grid",
        gridTemplateColumns: `repeat(${columns}, 1fr)`,
        gridTemplateRows: `repeat(${rows}, 1fr)`,
        width: containerSize,
        height: containerSize,
        ...style,
      }}
      aria-hidden="true"
    >
      {spans}
    </div>
  );
}
