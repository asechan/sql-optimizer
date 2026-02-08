import { useEffect, useRef } from "react";

/* ─────────────────────────────────────────────
   Minimal 3-D Simplex Noise (self-contained)
   ───────────────────────────────────────────── */
class SimplexNoise {
  constructor() {
    this.grad3 = [
      [1,1,0],[-1,1,0],[1,-1,0],[-1,-1,0],
      [1,0,1],[-1,0,1],[1,0,-1],[-1,0,-1],
      [0,1,1],[0,-1,1],[0,1,-1],[0,-1,-1],
    ];
    const p = [];
    for (let i = 0; i < 256; i++) p[i] = (Math.random() * 256) | 0;
    this.perm = new Array(512);
    this.permMod12 = new Array(512);
    for (let i = 0; i < 512; i++) {
      this.perm[i] = p[i & 255];
      this.permMod12[i] = this.perm[i] % 12;
    }
  }

  noise3D(x, y, z) {
    const { grad3, perm, permMod12 } = this;
    const F3 = 1 / 3, G3 = 1 / 6;
    const s = (x + y + z) * F3;
    const i = Math.floor(x + s),
          j = Math.floor(y + s),
          k = Math.floor(z + s);
    const t = (i + j + k) * G3;
    const X0 = i - t, Y0 = j - t, Z0 = k - t;
    const x0 = x - X0, y0 = y - Y0, z0 = z - Z0;

    let i1, j1, k1, i2, j2, k2;
    if (x0 >= y0) {
      if (y0 >= z0)      { i1=1;j1=0;k1=0;i2=1;j2=1;k2=0; }
      else if (x0 >= z0) { i1=1;j1=0;k1=0;i2=1;j2=0;k2=1; }
      else               { i1=0;j1=0;k1=1;i2=1;j2=0;k2=1; }
    } else {
      if (y0 < z0)       { i1=0;j1=0;k1=1;i2=0;j2=1;k2=1; }
      else if (x0 < z0)  { i1=0;j1=1;k1=0;i2=0;j2=1;k2=1; }
      else               { i1=0;j1=1;k1=0;i2=1;j2=1;k2=0; }
    }

    const x1 = x0 - i1 + G3, y1 = y0 - j1 + G3, z1 = z0 - k1 + G3;
    const x2 = x0 - i2 + 2*G3, y2 = y0 - j2 + 2*G3, z2 = z0 - k2 + 2*G3;
    const x3 = x0 - 1 + 3*G3, y3 = y0 - 1 + 3*G3, z3 = z0 - 1 + 3*G3;

    const ii = i & 255, jj = j & 255, kk = k & 255;

    const dot = (g, a, b, c) => g[0]*a + g[1]*b + g[2]*c;
    const contrib = (g, a, b, c) => {
      let t0 = 0.6 - a*a - b*b - c*c;
      return t0 < 0 ? 0 : (t0 *= t0, t0 * t0 * dot(g, a, b, c));
    };

    const n0 = contrib(grad3[permMod12[ii + perm[jj + perm[kk]]]], x0, y0, z0);
    const n1 = contrib(grad3[permMod12[ii + i1 + perm[jj + j1 + perm[kk + k1]]]], x1, y1, z1);
    const n2 = contrib(grad3[permMod12[ii + i2 + perm[jj + j2 + perm[kk + k2]]]], x2, y2, z2);
    const n3 = contrib(grad3[permMod12[ii + 1 + perm[jj + 1 + perm[kk + 1]]]], x3, y3, z3);

    return 32 * (n0 + n1 + n2 + n3);
  }
}

/* ─────────────────────────────────────────────
   Utilities
   ───────────────────────────────────────────── */
const TAU = 2 * Math.PI;
const cos = Math.cos;
const sin = Math.sin;
const rand  = (n) => Math.random() * n;
const randRange = (n) => n - rand(2 * n);
const lerp  = (a, b, t) => (1 - t) * a + t * b;
const fadeInOut = (life, ttl) => {
  const half = ttl * 0.5;
  return life < half
    ? life / half
    : 1 - (life - half) / half;
};

/* ─────────────────────────────────────────────
   Swirl configuration (tuned for dark theme)
   ───────────────────────────────────────────── */
const PARTICLE_COUNT   = 900;
const PROP_COUNT       = 9;
const PROPS_LENGTH     = PARTICLE_COUNT * PROP_COUNT;
const RANGE_Y          = 150;
const BASE_TTL         = 60;
const RANGE_TTL        = 200;
const BASE_SPEED       = 0.1;
const RANGE_SPEED      = 2;
const BASE_RADIUS      = 1;
const RANGE_RADIUS     = 5;
const BASE_HUE         = 220;   // blue to match theme
const RANGE_HUE        = 100;   // blue -> violet range
const NOISE_STEPS      = 8;
const X_OFF            = 0.00125;
const Y_OFF            = 0.00125;
const Z_OFF            = 0.0005;
const BG_COLOR         = "hsla(230, 30%, 5%, 1)";

export default function SwirlBackground() {
  const containerRef = useRef(null);
  const animRef      = useRef(null);
  const stateRef     = useRef(null);

  useEffect(() => {
    const container = containerRef.current;
    if (!container) return;

    /* Canvas setup (dual-buffer for glow compositing) */
    const canvasA = document.createElement("canvas");
    const canvasB = document.createElement("canvas");
    canvasB.className = "swirl-visible-canvas";
    container.appendChild(canvasB);

    const ctxA = canvasA.getContext("2d");
    const ctxB = canvasB.getContext("2d");
    const center = [0, 0];

    const simplex = new SimplexNoise();
    const particleProps = new Float32Array(PROPS_LENGTH);
    let tick = 0;

    stateRef.current = {
      canvasA, canvasB, ctxA, ctxB, center,
      simplex, particleProps, tick,
    };

    /* ── helpers ── */
    function resize() {
      const { innerWidth: w, innerHeight: h } = window;
      canvasA.width  = w; canvasA.height = h;
      ctxA.drawImage(canvasB, 0, 0);
      canvasB.width  = w; canvasB.height = h;
      ctxB.drawImage(canvasA, 0, 0);
      center[0] = 0.5 * w;
      center[1] = 0.5 * h;
    }

    function initParticle(i) {
      particleProps.set([
        rand(canvasA.width),           // x
        center[1] + randRange(RANGE_Y),// y
        0,                             // vx
        0,                             // vy
        0,                             // life
        BASE_TTL + rand(RANGE_TTL),    // ttl
        BASE_SPEED + rand(RANGE_SPEED),// speed
        BASE_RADIUS + rand(RANGE_RADIUS), // radius
        BASE_HUE + rand(RANGE_HUE),   // hue
      ], i);
    }

    function initParticles() {
      for (let i = 0; i < PROPS_LENGTH; i += PROP_COUNT) initParticle(i);
    }

    function updateParticle(i) {
      const i2=i+1, i3=i+2, i4=i+3, i5=i+4, i6=i+5, i7=i+6, i8=i+7, i9=i+8;
      const x     = particleProps[i];
      const y     = particleProps[i2];
      const n     = simplex.noise3D(x * X_OFF, y * Y_OFF, tick * Z_OFF)
                    * NOISE_STEPS * TAU;
      const vx    = lerp(particleProps[i3], cos(n), 0.5);
      const vy    = lerp(particleProps[i4], sin(n), 0.5);
      const life  = particleProps[i5];
      const ttl   = particleProps[i6];
      const speed = particleProps[i7];
      const x2    = x + vx * speed;
      const y2    = y + vy * speed;
      const radius = particleProps[i8];
      const hue    = particleProps[i9];

      /* draw segment */
      ctxA.save();
      ctxA.lineCap = "round";
      ctxA.lineWidth = radius;
      ctxA.strokeStyle =
        `hsla(${hue},100%,70%,${fadeInOut(life, ttl)})`;
      ctxA.beginPath();
      ctxA.moveTo(x, y);
      ctxA.lineTo(x2, y2);
      ctxA.stroke();
      ctxA.closePath();
      ctxA.restore();

      /* advance state */
      particleProps[i]  = x2;
      particleProps[i2] = y2;
      particleProps[i3] = vx;
      particleProps[i4] = vy;
      particleProps[i5] = life + 1;

      if (x2 > canvasA.width || x2 < 0 || y2 > canvasA.height || y2 < 0 || life > ttl) {
        initParticle(i);
      }
    }

    function drawParticles() {
      for (let i = 0; i < PROPS_LENGTH; i += PROP_COUNT) updateParticle(i);
    }

    function renderGlow() {
      ctxB.save();
      ctxB.filter = "blur(12px) brightness(250%)";
      ctxB.globalCompositeOperation = "lighter";
      ctxB.drawImage(canvasA, 0, 0);
      ctxB.restore();

      ctxB.save();
      ctxB.filter = "blur(6px) brightness(220%)";
      ctxB.globalCompositeOperation = "lighter";
      ctxB.drawImage(canvasA, 0, 0);
      ctxB.restore();

      ctxB.save();
      ctxB.filter = "blur(2px) brightness(180%)";
      ctxB.globalCompositeOperation = "lighter";
      ctxB.drawImage(canvasA, 0, 0);
      ctxB.restore();
    }

    function renderToScreen() {
      ctxB.save();
      ctxB.globalCompositeOperation = "lighter";
      ctxB.drawImage(canvasA, 0, 0);
      ctxB.restore();
    }

    function draw() {
      tick++;
      ctxA.clearRect(0, 0, canvasA.width, canvasA.height);
      ctxB.fillStyle = BG_COLOR;
      ctxB.fillRect(0, 0, canvasA.width, canvasA.height);

      drawParticles();
      renderGlow();
      renderToScreen();

      animRef.current = requestAnimationFrame(draw);
    }

    /* ── kick off ── */
    resize();
    initParticles();
    draw();

    window.addEventListener("resize", resize);

    return () => {
      window.removeEventListener("resize", resize);
      if (animRef.current) cancelAnimationFrame(animRef.current);
      if (canvasB.parentNode) canvasB.parentNode.removeChild(canvasB);
    };
  }, []);

  return <div className="swirl-bg" ref={containerRef} />;
}
