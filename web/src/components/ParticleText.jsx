import { useEffect, useRef, useState } from "react";

/**
 * ParticleText — Animated text made of particles that gather/disperse.
 * Adapted from @react-bits/ParticleText-TS-TW for this project's theme.
 * Replaces the H1 "Energy use is a pattern, not just a number."
 */
export default function ParticleText({
  text = "Energy use is a pattern, not just a number.",
  particleSize = 2.2,
  density = 4,
  color = "#48d7c2",
  highlight = "#48d7c2",
  scatter = 190,
  gatherDuration = 1600,
  stagger = 420,
  pointerRepel = 42,
  repelRadius = 120,
  idleDrift = 0.8,
  trigger = "mount",
  className = "",
  fontSize = "clamp(3.5rem, 13vw, 9rem)",
  fontWeight = 800,
}) {
  const containerRef = useRef(null);
  const canvasRef = useRef(null);
  const [reducedMotion, setReducedMotion] = useState(false);

  // Refs for animation loop
  const particlesRef = useRef([]);
  const animationFrameRef = useRef(null);
  const resizeFrameRef = useRef(null);
  const buildIdRef = useRef(0);
  const gatheringRef = useRef(false);
  const gatherStartRef = useRef(0);
  const pointerRef = useRef({
    active: false,
    x: 0,
    y: 0,
    smoothX: 0,
    smoothY: 0,
  });

  // Color utilities
  const hexToRgb = (hex) => {
    const h = hex.replace("#", "");
    const bigint = parseInt(h.length === 3 ? h.split("").map((c) => c + c).join("") : h, 16);
    return { r: (bigint >> 16) & 255, g: (bigint >> 8) & 255, b: bigint & 255 };
  };

  const mixRgb = (a, b, t) => ({
    r: Math.round(a.r + (b.r - a.r) * t),
    g: Math.round(a.g + (b.g - a.g) * t),
    b: Math.round(a.b + (b.b - a.b) * t),
  });

  const rgbToCss = (rgb) => `rgb(${rgb.r},${rgb.g},${rgb.b})`;

  const clamp = (v, min, max) => Math.max(min, Math.min(max, v));
  const easeOutCubic = (t) => 1 - Math.pow(1 - t, 3);

  const resolveFontSize = (fs) => {
    if (typeof fs === "number") return `${fs}px`;
    return fs;
  };

  const waitForFonts = async () => {
    if (document.fonts && document.fonts.ready) {
      await document.fonts.ready;
    }
  };

  // Start the gather animation
  const startGather = () => {
    gatheringRef.current = true;
    gatherStartRef.current = performance.now();
  };

  // Draw a single particle
  const drawParticle = (ctx, p, colorCss, progress, pointer) => {
    const size = Math.max(0.5, p.size * progress);
    const { r, g, b } = hexToRgb(colorCss);
    const alpha = p.alpha * progress;
    ctx.globalAlpha = alpha;
    ctx.fillStyle = `rgba(${r},${g},${b},${alpha})`;

    // Use fillRect for better performance at small sizes
    if (size < 2) {
      ctx.fillRect(p.x - 0.5, p.y - 0.5, 1, 1);
    } else {
      ctx.beginPath();
      ctx.arc(p.x, p.y, size, 0, Math.PI * 2);
      ctx.fill();
    }
  };

  // Sample text into particles
  const sampleText = (canvas, ctx, text, fontSizePx, particleSize, density, color, highlight) => {
    const dpr = window.devicePixelRatio || 1;
    const w = canvas.width;
    const h = canvas.height;

    // Offscreen canvas for text measurement
    const off = document.createElement("canvas");
    const offCtx = off.getContext("2d");
    off.width = w;
    off.height = h;
    offCtx.font = `${fontWeight} ${fontSizePx}px Inter, system-ui, sans-serif`;
    offCtx.textBaseline = "top";
    offCtx.fillStyle = "white";

    const metrics = offCtx.measureText(text);
    const textWidth = metrics.width;
    const maxTextWidth = w * 0.92;
    const scale = textWidth > maxTextWidth ? maxTextWidth / textWidth : 1;
    const finalFontSize = fontSizePx * scale;
    offCtx.font = `${fontWeight} ${finalFontSize}px Inter, system-ui, sans-serif`;

    const finalMetrics = offCtx.measureText(text);
    const x = (w - finalMetrics.width) / 2;
    const y = (h - finalMetrics.height) / 2;
    offCtx.fillText(text, x, y);

    const imgData = offCtx.getImageData(0, 0, w, h);
    const data = imgData.data;
    const step = Math.max(1, density);
    const maxParticles = Math.min(
      5200,
      Math.max(900, Math.floor((w * h) / 90))
    );
    const stride = Math.max(step, Math.ceil(Math.sqrt((w * h) / maxParticles)));

    const baseColor = hexToRgb(color);
    const highlightColor = hexToRgb(highlight);
    const particles = [];

    for (let py = 0; py < h; py += stride) {
      const rowOffset = py * w * 4;
      for (let px = 0; px < w; px += stride) {
        const idx = rowOffset + px * 4;
        const alpha = data[idx + 3];
        if (alpha > 40) {
          const depth = Math.random();
          const delay = depth * stagger;
          const isHighlight = Math.random() < 0.15;
          particles.push({
            x: px,
            y: py,
            targetX: px,
            targetY: py,
            size: particleSize * (0.6 + depth * 0.8),
            alpha: alpha / 255,
            color: isHighlight ? highlightColor : baseColor,
            depth,
            delay,
            vx: 0,
            vy: 0,
          });
        }
      }
    }

    return particles.slice(0, maxParticles);
  };

  // Initialize particles
  const initializeParticles = () => {
    const canvas = canvasRef.current;
    const container = containerRef.current;
    if (!canvas || !container) return;

    const dpr = window.devicePixelRatio || 1;
    const rect = container.getBoundingClientRect();
    canvas.width = rect.width * dpr;
    canvas.height = rect.height * dpr;
    canvas.style.width = `${rect.width}px`;
    canvas.style.height = `${rect.height}px`;

    const ctx = canvas.getContext("2d");
    ctx.scale(dpr, dpr);

    // Parse fontSize to pixels
    let fontSizePx = 120;
    const fsStr = resolveFontSize(fontSize);
    if (fsStr.endsWith("px")) {
      fontSizePx = parseFloat(fsStr);
    } else if (fsStr.includes("clamp")) {
      // Approximate clamp(3.5rem, 13vw, 9rem) -> use 13vw
      fontSizePx = Math.max(56, Math.min(144, window.innerWidth * 0.13));
    } else if (fsStr.endsWith("rem")) {
      fontSizePx = parseFloat(fsStr) * 16;
    } else if (fsStr.endsWith("vw")) {
      fontSizePx = (parseFloat(fsStr) / 100) * window.innerWidth;
    }

    buildIdRef.current += 1;
    const currentBuildId = buildIdRef.current;

    waitForFonts().then(() => {
      if (currentBuildId !== buildIdRef.current) return;
      particlesRef.current = sampleText(
        canvas,
        ctx,
        text,
        fontSizePx,
        particleSize,
        density,
        color,
        highlight
      );
    });
  };

  // Render loop
  const render = () => {
    const canvas = canvasRef.current;
    if (!canvas) return;

    const ctx = canvas.getContext("2d");
    const w = canvas.width / (window.devicePixelRatio || 1);
    const h = canvas.height / (window.devicePixelRatio || 1);

    ctx.clearRect(0, 0, canvas.width, canvas.height);

    const now = performance.now();
    const pointer = pointerRef.current;

    // Smooth pointer following
    pointer.smoothX += (pointer.x - pointer.smoothX) * 0.18;
    pointer.smoothY += (pointer.y - pointer.smoothY) * 0.18;

    let progress = 1;
    if (gatheringRef.current) {
      const elapsed = now - gatherStartRef.current;
      progress = clamp(elapsed / gatherDuration, 0, 1);
      progress = easeOutCubic(progress);
      if (progress >= 1) {
        gatheringRef.current = false;
      }
    }

    const particles = particlesRef.current;
    for (let i = 0; i < particles.length; i++) {
      const p = particles[i];
      const particleProgress = gatheringRef.current
        ? clamp((progress - p.delay / gatherDuration) / (1 - p.delay / gatherDuration), 0, 1)
        : 1;

      // Idle drift
      if (!gatheringRef.current && !pointer.active) {
        const driftSpeed = 0.0003 * idleDrift;
        p.targetX += Math.sin(now * driftSpeed + p.depth * 10) * 0.3;
        p.targetY += Math.cos(now * driftSpeed + p.depth * 10) * 0.2;
      }

      // Pointer repel
      if (pointer.active) {
        const dx = p.x - pointer.smoothX;
        const dy = p.y - pointer.smoothY;
        const dist = Math.hypot(dx, dy);
        if (dist < repelRadius && dist > 0) {
          const force = (pointerRepel / dist) * (1 - dist / repelRadius);
          p.vx += (dx / dist) * force * 0.5;
          p.vy += (dy / dist) * force * 0.5;
        }
      }

      // Spring to target
      const k = 0.08;
      const d = 0.85;
      const tx = gatheringRef.current ? p.targetX : p.targetX;
      const ty = gatheringRef.current ? p.targetY : p.targetY;

      p.vx += (tx - p.x) * k;
      p.vy += (ty - p.y) * k;
      p.vx *= d;
      p.vy *= d;
      p.x += p.vx;
      p.y += p.vy;

      // Draw
      const drawProgress = gatheringRef.current ? particleProgress : 1;
      drawParticle(ctx, p, rgbToCss(p.color), drawProgress, pointer);
    }

    // Draw highlight glow for gathered state
    if (gatheringRef.current && progress > 0.5) {
      const glowProgress = (progress - 0.5) * 2;
      ctx.shadowBlur = 30 * glowProgress;
      ctx.shadowColor = highlight;
    } else {
      ctx.shadowBlur = 0;
    }

    animationFrameRef.current = requestAnimationFrame(render);
  };

  // Ensure render loop is running
  const ensureRenderLoop = () => {
    if (!animationFrameRef.current) {
      render();
    }
  };

  // Queue a rebuild (resize, text change)
  const queueSample = () => {
    if (resizeFrameRef.current) cancelAnimationFrame(resizeFrameRef.current);
    resizeFrameRef.current = requestAnimationFrame(() => {
      initializeParticles();
      ensureRenderLoop();
    });
  };

  // Pointer handlers
  const onPointerMove = (e) => {
    const container = containerRef.current;
    if (!container) return;
    const rect = container.getBoundingClientRect();
    pointerRef.current.active = true;
    pointerRef.current.x = e.clientX - rect.left;
    pointerRef.current.y = e.clientY - rect.top;
  };

  const onPointerLeave = () => {
    pointerRef.current.active = false;
  };

  const onPointerDown = () => {
    if (!gatheringRef.current) startGather();
  };

  // Reduced motion
  useEffect(() => {
    const mediaQuery = window.matchMedia("(prefers-reduced-motion: reduce)");
    setReducedMotion(mediaQuery.matches);
    const handler = (e) => setReducedMotion(e.matches);
    mediaQuery.addEventListener("change", handler);
    return () => mediaQuery.removeEventListener("change", handler);
  }, []);

  // Initialize and cleanup
  useEffect(() => {
    initializeParticles();
    ensureRenderLoop();

    const container = containerRef.current;
    if (container) {
      container.addEventListener("pointermove", onPointerMove);
      container.addEventListener("pointerleave", onPointerLeave);
      container.addEventListener("pointerdown", onPointerDown);
    }

    const ro = new ResizeObserver(() => queueSample());
    if (container) ro.observe(container);

    return () => {
      if (animationFrameRef.current) cancelAnimationFrame(animationFrameRef.current);
      if (resizeFrameRef.current) cancelAnimationFrame(resizeFrameRef.current);
      if (container) {
        container.removeEventListener("pointermove", onPointerMove);
        container.removeEventListener("pointerleave", onPointerLeave);
        container.removeEventListener("pointerdown", onPointerDown);
      }
      ro.disconnect();
    };
  }, [text, particleSize, density, color, highlight, scatter, gatherDuration, stagger, pointerRepel, repelRadius, idleDrift, fontSize, fontWeight]);

  // Trigger gather on mount
  useEffect(() => {
    if (trigger === "mount") {
      startGather();
    }
  }, [trigger]);

  return (
    <div
      ref={containerRef}
      className={`particle-text ${className}`}
      style={{
        position: "relative",
        width: "100%",
        height: "100%",
        minHeight: "1.5em",
        userSelect: "none",
      }}
      role="img"
      aria-label={text}
    >
      <canvas ref={canvasRef} style={{ display: "block", width: "100%", height: "100%" }} />
      <span className="sr-only" style={{
        position: "absolute",
        width: "1px",
        height: "1px",
        padding: 0,
        margin: "-1px",
        overflow: "hidden",
        clip: "rect(0, 0, 0, 0)",
        whiteSpace: "nowrap",
        border: 0,
      }}>
        {text}
      </span>
    </div>
  );
}