import { useEffect, useRef, useState } from "react";

/**
 * ParticleText — "Future Interfaces"-style particle title.
 *
 * Ported faithfully to JSX from the public TypeScript component
 * @react-bits/ParticleText-TS-TW (added via `npx shadcn@latest add`). It
 * samples the rendered text on an off-screen canvas and spawns one particle
 * per lit pixel, then eases the particles from a scattered state into place,
 * with optional pointer repulsion and a glow pass on top.
 *
 * API follows the shadcn component: `highlightColor` (not `highlight`), an
 * explicit `glow` toggle, and `trigger`="mount" | "visible" | null for when the
 * gather animation starts.
 */
export default function ParticleText({
  text = "Future Interfaces",
  color = "#f8fafc",
  highlightColor = "#8b5cf6",
  particleSize = 3,
  density = 3,
  fontSize = "6rem",
  fontWeight = 800,
  fontFamily = "inherit",
  scatter = 240,
  gatherDuration = 1500,
  stagger = 330,
  pointerRepel = 30,
  repelRadius = 100,
  idleDrift = 1,
  glow = false,
  trigger = "mount",
  className = "",
  style = {},
}) {
  const containerRef = useRef(null);
  const [phase, setPhase] = useState(trigger === "mount" ? "gather" : "idle");
  const [isVisible, setIsVisible] = useState(false);

  const propsRef = useRef({});
  propsRef.current = {
    text,
    color,
    highlightColor,
    particleSize: Math.max(particleSize, 1),
    density: Math.max(density, 1),
    fontSize,
    stagger,
    gatherDuration,
    pointerRepel,
    repelRadius,
    glow,
    phase,
    fontWeight,
  };

  const hexToRgb = (hex) => {
    const h = hex.replace("#", "");
    const full =
      h.length === 3
        ? h
            .split("")
            .map((c) => c + c)
            .join("")
        : h;
    const bigint = parseInt(full, 16);
    return { r: (bigint >> 16) & 255, g: (bigint >> 8) & 255, b: bigint & 255 };
  };

  const mixRgb = (from, to, amount) => {
    const clamped = Math.max(0, Math.min(1, amount));
    return {
      r: Math.round(from.r + (to.r - from.r) * clamped),
      g: Math.round(from.g + (to.g - from.g) * clamped),
      b: Math.round(from.b + (to.b - from.b) * clamped),
    };
  };

  const rgbToCss = ({ r, g, b }) => `rgb(${r}, ${g}, ${b})`;

  const clamp = (v, min, max) => Math.max(min, Math.min(max, v));

  const easeOutCubic = (t) => 1 - Math.pow(1 - t, 3);

  const waitForFonts = (font) =>
    new Promise((resolve) => {
      if (!document.fonts?.ready) return resolve();
      document.fonts.ready.then(() => {
        if (document.fonts.check(font)) return resolve();
        let tries = 0;
        const check = setInterval(() => {
          tries += 1;
          if (document.fonts.check(font) || tries > 50) {
            clearInterval(check);
            resolve();
          }
        }, 100);
      });
    });

  const resolveFontSize = (value, container, fallbackWeight, resolvedFamily) => {
    const probe = document.createElement("div");
    probe.style.position = "absolute";
    probe.style.visibility = "hidden";
    probe.style.whiteSpace = "nowrap";
    probe.style.fontFamily = resolvedFamily;
    probe.style.fontWeight = String(fallbackWeight);
    probe.textContent = "M";
    container.appendChild(probe);
    let numeric = typeof value === "number" ? value : parseFloat(value);
    if (Number.isNaN(numeric)) numeric = 96;
    const measured = probe.getBoundingClientRect().height || numeric;
    probe.remove();
    return measured;
  };

  // Visibility wiring for trigger="visible".
  useEffect(() => {
    if (trigger === "visible") {
      const observer = new IntersectionObserver(
        ([entry]) => {
          if (entry.isIntersecting) {
            setIsVisible(true);
            setPhase("gather");
            observer.disconnect();
          }
        },
        { threshold: 0.1 }
      );
      if (containerRef.current) observer.observe(containerRef.current);
      return () => observer.disconnect();
    }
    if (trigger === "mount") {
      setIsVisible(true);
    }
    return undefined;
  }, [trigger]);

  // Main particle engine.
  useEffect(() => {
    const container = containerRef.current;
    if (!container) return;
    if (trigger !== null && !isVisible) return;
    if (trigger === null) setPhase("gather");

    const canvas = container.querySelector(".particle-text__canvas");
    if (!canvas) return;
    const ctx = canvas.getContext("2d");

    let width = container.getBoundingClientRect().width;
    let controlHeight = container.getBoundingClientRect().height;

    const props = propsRef.current;
    const resolvedFamily =
      fontFamily === "inherit" ? getComputedStyle(container).fontFamily : fontFamily;
    const currentFontSize = resolveFontSize(fontSize, container, fontWeight, resolvedFamily);
    const resolvedFont = `${fontWeight} ${currentFontSize * 1.1}px ${resolvedFamily}`;

    const paintText = () => {
      ctx.clearRect(0, 0, width, controlHeight);
      ctx.fillStyle = "#ffffff";
      ctx.font = `${fontWeight} ${currentFontSize * 1.1}px ${resolvedFamily}`;
      ctx.textAlign = "center";
      ctx.textBaseline = "middle";
      ctx.fillText(text, width / 2, controlHeight / 2);
    };

    canvas.width = width * 2;
    canvas.height = controlHeight * 2;
    ctx.scale(2, 2);
    paintText();

    waitForFonts(resolvedFont).then(paintText);

    // Sample lit pixels.
    const offCanvas = document.createElement("canvas");
    offCanvas.width = canvas.width;
    offCanvas.height = canvas.height;
    const offCtx = offCanvas.getContext("2d");
    offCtx.drawImage(canvas, 0, 0);
    const imageData = offCtx.getImageData(0, 0, offCanvas.width, offCanvas.height);

    const samples = [];
    const threshold = 220;
    const step = Math.max(1, Math.floor(props.density / 2));
    let idx = 0;
    for (let y = 0; y < offCanvas.height; y += step) {
      for (let x = 0; x < offCanvas.width; x += step) {
        const o = idx * 4;
        if (
          imageData.data[o] > threshold &&
          imageData.data[o + 1] > threshold &&
          imageData.data[o + 2] > threshold
        ) {
          samples.push({ x: x / 2, y: y / 2 });
        }
        idx += 1;
      }
    }

    const target = { source: new Float32Array(samples.length * 2), count: samples.length };
    samples.forEach((s, i) => {
      target.source[i * 2] = s.x;
      target.source[i * 2 + 1] = s.y;
    });

    let particles = Array.from({ length: target.count }, (_, i) => ({
      startX: target.source[i * 2],
      startY: target.source[i * 2 + 1],
      currentX: Math.random() * width,
      currentY: Math.random() * controlHeight,
      targetIndex: i * 2,
      delay: Math.random() * props.stagger * 5,
    }));

    const pointer = {
      x: width / 2,
      y: controlHeight / 2,
      vx: 0,
      vy: 0,
    };

    let lastTime = performance.now();
    let animationTime = 0;
    let rafId = 0;

    const pointerInside = () => {
      const rect = container.getBoundingClientRect();
      return pointer.x >= 0 && pointer.x <= rect.width && pointer.y >= 0 && pointer.y <= rect.height;
    };

    const render = (now) => {
      const dt = Math.min((now - lastTime) / 1000, 0.05);
      lastTime = now;
      animationTime += dt;

      let avgX = 0;
      let avgY = 0;
      const n = particles.length;
      const distXTotal = pointer.vx;
      const distYTotal = pointer.vy;

      for (const p of particles) {
        const tx = target.source[p.targetIndex];
        const ty = target.source[p.targetIndex + 1];

        if (phase === "gather") {
          const t = Math.min(Math.max(0, animationTime - p.delay) / props.gatherDuration, 1);
          const eased = easeOutCubic(t);
          p.currentX = p.startX + (tx - p.startX) * eased;
          p.currentY = p.startY + (ty - p.startY) * eased;
        } else {
          p.currentX += (tx - p.currentX) * 0.08;
          p.currentY += (ty - p.currentY) * 0.08;
        }

        let dxx = pointer.x - p.currentX;
        let dyy = pointer.y - p.currentY;
        const dist = Math.sqrt(dxx * dxx + dyy * dyy);
        const r = props.repelRadius * 1.0;
        if (dist < r * (1 + props.pointerRepel * 0.02) && pointerInside()) {
          const force = ((r - dist) / r) * props.pointerRepel;
          dxx = dxx / (dist || 0.0001);
          dyy = dyy / (dist || 0.0001);
          const push = (force * 12) / (1 + r * 0.12);
          p.currentX += dxx * push;
          p.currentY += dyy * push;
        }

        avgX += p.currentX;
        avgY += p.currentY;
      }

      avgX = n ? avgX / n : width / 2;
      avgY = n ? avgY / n : controlHeight / 2;
      const maxDist = Math.max(props.repelRadius, props.repelRadius * 2);

      ctx.clearRect(0, 0, width, controlHeight);
      ctx.save();
      ctx.translate(width / 2, controlHeight / 2);
      ctx.rotate(Math.sin(animationTime * 0.01) * 0.01);
      ctx.translate(-avgX, -avgY);

      const colorRgb = hexToRgb(props.color);
      const highlightRgb = hexToRgb(props.highlightColor);

      for (const p of particles) {
        const totalDist = Math.max(
          Math.sqrt((p.currentX - avgX) ** 2 + (p.currentY - avgY) ** 2),
          0.01
        );
        const fade = clamp(totalDist / maxDist, 0, 1);
        const mixed = mixRgb(highlightRgb, colorRgb, easeOutCubic(fade));

        const gidx = Math.floor(p.targetIndex / 2);
        const cycle = Math.sin(animationTime * 2 + gidx * 0.05) * 0.5 + 0.5;

        ctx.beginPath();
        ctx.arc(
          p.currentX,
          p.currentY,
          (props.particleSize / 2) * (idleDrift ? 1 + cycle * 0.1 : 1),
          0,
          Math.PI * 2
        );
        ctx.fillStyle = rgbToCss(mixed);
        ctx.globalAlpha = 1 - fade * 0.55;
        ctx.fill();

        if (props.glow) {
          ctx.shadowColor = rgbToCss(mixed);
          ctx.shadowBlur = props.particleSize * 2;
          ctx.fill();
          ctx.shadowBlur = 0;
        }
      }

      ctx.restore();
      ctx.globalAlpha = 1;

      rafId = requestAnimationFrame(render);
    };

    const onPointerMove = (e) => {
      const rect = container.getBoundingClientRect();
      const newX = e.clientX - rect.left;
      const newY = e.clientY - rect.top;
      pointer.vx = (newX - pointer.x) * 0.1;
      pointer.vy = (newY - pointer.y) * 0.1;
      pointer.x = newX;
      pointer.y = newY;
    };

    const onPointerLeave = () => {
      pointer.vx = 0;
      pointer.vy = 0;
    };

    // React to container resizes by re-sampling so the glyph stays sharp.
    const handleResize = () => {
      const rect = container.getBoundingClientRect();
      const newWidth = rect.width;
      const newControlHeight = rect.height;
      if (newWidth === width && newControlHeight === controlHeight) return;

      canvas.width = newWidth * 2;
      canvas.height = newControlHeight * 2;
      ctx.setTransform(2, 0, 0, 2, 0, 0);
      ctx.font = `${fontWeight} ${currentFontSize * 1.1}px ${resolvedFamily}`;
      ctx.textAlign = "center";
      ctx.textBaseline = "middle";
      ctx.fillText(text, newWidth / 2, newControlHeight / 2);

      // Re-sample lit pixels for the new size.
      const off = document.createElement("canvas");
      off.width = canvas.width;
      off.height = canvas.height;
      const octx = off.getContext("2d");
      octx.drawImage(canvas, 0, 0);
      const id = octx.getImageData(0, 0, off.width, off.height);
      const rebuilt = [];
      let counter = 0;
      for (let yy = 0; yy < off.height; yy += step) {
        for (let xx = 0; xx < off.width; xx += step) {
          const o = counter * 4;
          if (
            id.data[o] > threshold &&
            id.data[o + 1] > threshold &&
            id.data[o + 2] > threshold
          ) {
            rebuilt.push({ x: xx / 2, y: yy / 2 });
          }
          counter += 1;
        }
      }
      const newCount = rebuilt.length;
      particles = Array.from({ length: newCount }, (_, i) => ({
        startX: rebuilt[i].x,
        startY: rebuilt[i].y,
        currentX: Math.random() * newWidth,
        currentY: Math.random() * newControlHeight,
        targetIndex: i * 2,
        delay: Math.random() * props.stagger * 5,
      }));
      target.count = newCount;
      target.source = new Float32Array(newCount * 2);
      rebuilt.forEach((s, i) => {
        target.source[i * 2] = s.x;
        target.source[i * 2 + 1] = s.y;
      });

      width = newWidth;
      controlHeight = newControlHeight;

      ctx.clearRect(0, 0, width, controlHeight);
    };

    const ro = new ResizeObserver(handleResize);
    ro.observe(container);
    container.addEventListener("pointermove", onPointerMove);
    container.addEventListener("pointerleave", onPointerLeave);
    rafId = requestAnimationFrame(render);

    return () => {
      cancelAnimationFrame(rafId);
      ro.disconnect();
      container.removeEventListener("pointermove", onPointerMove);
      container.removeEventListener("pointerleave", onPointerLeave);
    };
  }, [isVisible, trigger, text, color, highlightColor, fontSize, fontWeight, fontFamily, density, particleSize, stagger, gatherDuration, pointerRepel, repelRadius, idleDrift, glow]);

  return (
    <div
      ref={containerRef}
      className={`particle-text ${className}`}
      style={style}
      aria-label={text}
    >
      <canvas className="particle-text__canvas" aria-hidden="true" />
      <span className="particle-text__sr">{text}</span>
    </div>
  );
}