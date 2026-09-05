import { useEffect, useRef, useState } from "react";

/**
 * GlowCursor: a soft radial glow trail that follows the pointer.
 *
 * The original WebGL implementation (ogl) never drew correctly because its
 * fragment shader measured distances between a clip-space UV and a set of
 * pixel-space point uniforms, so the trail either flooded the panel or never
 * showed. This version keeps the exact same public API and props but renders
 * with plain Canvas 2D: an elastic chain of points trails the cursor and each
 * node draws a radial-gradient glow blob, composited additively for a bright,
 * smooth tail. No WebGL, no ogl import.
 *
 * Honors prefers-reduced-motion (renders nothing when active) and falls back to
 * just its children when a 2D canvas is unavailable.
 */
export default function GlowCursor({
  children,
  color = "#48d7c2",
  secondaryColor = "#b78cff",
  trailLength = 40,
  trailWidth = 8,
  trailTaper = 0.8,
  followSpeed = 0.16,
  glowIntensity = 1.9,
  glowSpread = 1.2,
  hotspot = 0.65,
  brightness = 1.25,
  opacity = 1,
  pulseSpeed = 1.1,
  noiseStrength = 0,
  idleFade = true,
  idleTimeout = 700,
  fadeDuration = 900,
  blendMode = "screen",
  className = "",
}) {
  const containerRef = useRef(null);
  const canvasRef = useRef(null);
  const propsRef = useRef({});
  const [canvasSupported, setCanvasSupported] = useState(true);
  const [reducedMotion, setReducedMotion] = useState(false);

  // Keep the latest props reachable from inside the rAF closure.
  propsRef.current = {
    color,
    secondaryColor,
    trailLength,
    trailWidth,
    trailTaper,
    followSpeed,
    glowIntensity,
    glowSpread,
    hotspot,
    brightness,
    opacity,
    idleFade,
    idleTimeout,
    fadeDuration,
    blendMode,
  };

  const hexToRgb = (hex) => {
    const h = hex.replace("#", "").trim();
    const full = h.length === 3 ? h.split("").map((c) => c + c).join("") : h;
    const bigint = parseInt(full, 16);
    if (Number.isNaN(bigint)) return { r: 72, g: 215, b: 194 };
    return { r: (bigint >> 16) & 255, g: (bigint >> 8) & 255, b: bigint & 255 };
  };

  useEffect(() => {
    const probe = document.createElement("canvas");
    const ctx = probe.getContext && probe.getContext("2d");
    setCanvasSupported(!!ctx);

    const mediaQuery = window.matchMedia("(prefers-reduced-motion: reduce)");
    setReducedMotion(mediaQuery.matches);
    const handler = (e) => setReducedMotion(e.matches);
    mediaQuery.addEventListener("change", handler);
    return () => mediaQuery.removeEventListener("change", handler);
  }, []);

  useEffect(() => {
    // No usable canvas or reduced motion: still render the children, just
    // without the trailing glow. The engine is gated here rather than with an
    // early return between hooks, so the hook order never changes between
    // renders and React never sees a different hook count.
    const container = containerRef.current;
    const canvas = canvasRef.current;
    if (!container || !canvas || !canvasSupported || reducedMotion) return undefined;

    const dpr = Math.min(window.devicePixelRatio || 1, 2);
    const ctx = canvas.getContext("2d");
    if (!ctx) return undefined;

    let width = 0;
    let height = 0;
    let raf = 0;
    let disposed = false;

    // Elastic chain: each node chases the one in front of it, the front node
    // chases the raw pointer. Same direction as followSpeed but stable at any
    // pointer event rate.
    const nodes = [];
    const head = { x: 0, y: 0 };

    const resize = () => {
      const rect = container.getBoundingClientRect();
      width = Math.max(1, rect.width);
      height = Math.max(1, rect.height);
      canvas.width = Math.floor(width * dpr);
      canvas.height = Math.floor(height * dpr);
      canvas.style.width = `${width}px`;
      canvas.style.height = `${height}px`;
      ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
    };

    const ensureChain = () => {
      const n = Math.max(1, Math.min(200, propsRef.current.trailLength));
      while (nodes.length < n) {
        nodes.push({ x: head.x, y: head.y });
      }
      nodes.length = n;
    };

    resize();
    ensureChain();

    let pointerActive = false;
    let lastPointerTime = 0;

    const onPointerEnter = (e) => {
      pointerActive = true;
      const rect = container.getBoundingClientRect();
      head.x = e.clientX - rect.left;
      head.y = e.clientY - rect.top;
      ensureChain();
      nodes.forEach((node) => { node.x = head.x; node.y = head.y; });
      lastPointerTime = performance.now();
    };

    const onPointerMove = (e) => {
      if (!pointerActive) pointerActive = true;
      const rect = container.getBoundingClientRect();
      head.x = e.clientX - rect.left;
      head.y = e.clientY - rect.top;
      lastPointerTime = performance.now();
    };

    const onPointerLeave = () => {
      pointerActive = false;
    };

    const clamp = (v, min, max) => Math.max(min, Math.min(max, v));

    const draw = (time) => {
      if (disposed) return;
      const props = propsRef.current;

      // Advance the chain toward the pointer.
      const ease = clamp(props.followSpeed, 0.02, 0.9);
      if (pointerActive) {
        nodes[0].x += (head.x - nodes[0].x) * ease;
        nodes[0].y += (head.y - nodes[0].y) * ease;
      }
      for (let i = 1; i < nodes.length; i++) {
        nodes[i].x += (nodes[i - 1].x - nodes[i].x) * ease;
        nodes[i].y += (nodes[i - 1].y - nodes[i].y) * ease;
      }

      // Idle fade: after idleTimeout of no movement, fade to invisible over
      // fadeDuration.
      let globalFade = 1;
      if (props.idleFade) {
        const idle = time - lastPointerTime;
        if (idle > props.idleTimeout) {
          const progress = (idle - props.idleTimeout) / Math.max(1, props.fadeDuration);
          globalFade = clamp(1 - progress, 0, 1);
        }
      }
      if (globalFade <= 0.004) {
        ctx.clearRect(0, 0, width, height);
        raf = requestAnimationFrame(draw);
        return;
      }

      ctx.clearRect(0, 0, width, height);
      ctx.globalCompositeOperation = props.blendMode === "normal" ? "source-over" : "lighter";

      const c1 = hexToRgb(props.color);
      const c2 = hexToRgb(props.secondaryColor);
      const n = nodes.length;
      const pulse = 1 + Math.sin(time / 1000 * props.pulseSpeed) * 0.15;

      // Nodes are in chase order (0 = closest to the pointer), so the newest
      // and brightest node is nodes[0] at the cursor and the trail fades
      // toward the far end of the chain.
      for (let i = 0; i < n; i++) {
        const node = nodes[i];
        // Taper: 1 at the cursor, trailTaper at the far end.
        const scale = 1 - i / Math.max(1, n - 1); // 1 -> 0 toward tail
        const taper = props.trailTaper + (1 - props.trailTaper) * scale;
        const radius = Math.max(1.5, props.trailWidth * taper);

        // Falloff: strong near the cursor (glowSpread exponent), boosted by the
        // hotspot at the very head.
        let amp = Math.pow(scale, props.glowSpread);
        if (i === 0) amp = clamp(amp * props.hotspot, 0, 1);

        const baseAlpha = amp * globalFade * props.opacity;
        if (baseAlpha <= 0.004) continue;

        // Interpolate color from secondary at the tail to primary at the head.
        const r = Math.round(c2.r + (c1.r - c2.r) * scale);
        const g = Math.round(c2.g + (c1.g - c2.g) * scale);
        const b = Math.round(c2.b + (c1.b - c2.b) * scale);

        // Small film-grain jitter keyed to time so the tail stays lively.
        const jitter = props.noiseStrength ? (Math.sin(time + i * 13.7) * props.noiseStrength * radius) : 0;
        const grad = ctx.createRadialGradient(node.x, node.y, 0, node.x, node.y, radius * 2 + Math.abs(jitter));
        grad.addColorStop(0, `rgba(${r}, ${g}, ${b}, ${clamp(baseAlpha * props.glowIntensity * pulse * props.brightness, 0, 1)})`);
        grad.addColorStop(1, `rgba(${r}, ${g}, ${b}, 0)`);
        ctx.fillStyle = grad;
        ctx.beginPath();
        ctx.arc(node.x, node.y, radius * 2 + Math.abs(jitter), 0, Math.PI * 2);
        ctx.fill();
      }

      ctx.globalCompositeOperation = "source-over";
      raf = requestAnimationFrame(draw);
    };

    container.addEventListener("pointerenter", onPointerEnter);
    container.addEventListener("pointermove", onPointerMove);
    container.addEventListener("pointerleave", onPointerLeave);
    const ro = new ResizeObserver(resize);
    ro.observe(container);
    window.addEventListener("resize", resize);

    raf = requestAnimationFrame(draw);

    return () => {
      disposed = true;
      cancelAnimationFrame(raf);
      container.removeEventListener("pointerenter", onPointerEnter);
      container.removeEventListener("pointermove", onPointerMove);
      container.removeEventListener("pointerleave", onPointerLeave);
      ro.disconnect();
      window.removeEventListener("resize", resize);
    };
  }, [canvasSupported, reducedMotion]);

  return (
    <div
      ref={containerRef}
      className={`glow-cursor ${className}`}
      style={{ position: "relative", width: "100%", height: "100%" }}
    >
      <canvas
        ref={canvasRef}
        aria-hidden="true"
        style={{
          position: "absolute",
          inset: 0,
          width: "100%",
          height: "100%",
          pointerEvents: "none",
          zIndex: 10,
        }}
      />
      <div style={{ position: "relative", zIndex: 1 }}>{children}</div>
    </div>
  );
}