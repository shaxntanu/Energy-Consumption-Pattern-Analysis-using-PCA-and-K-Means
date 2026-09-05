import { useEffect, useRef, useState, memo } from "react";

/**
 * LogoLoop — Infinite logo scroller with fade-out edges.
 * Adapted from @react-bits/LogoLoop-JS-CSS for this project's theme.
 * Uses react-icons for tech logos.
 */
import {
  SiReact,
  SiNextdotjs,
  SiTypescript,
  SiTailwindcss,
  SiVite,
  SiChartdotjs,
  SiThreedotjs,
  SiNpm,
  SiGit,
  SiGithub,
} from "react-icons/si";

const LOGOS = [
  { Component: SiReact, label: "React" },
  { Component: SiNextdotjs, label: "Next.js" },
  { Component: SiTypescript, label: "TypeScript" },
  { Component: SiTailwindcss, label: "Tailwind CSS" },
  { Component: SiVite, label: "Vite" },
  { Component: SiChartdotjs, label: "Chart.js" },
  { Component: SiThreedotjs, label: "Three.js" },
  { Component: SiNpm, label: "npm" },
  { Component: SiGit, label: "Git" },
  { Component: SiGithub, label: "GitHub" },
];

const ANIMATION_CONFIG = {
  SMOOTH_TAU: 0.25,
  MIN_COPIES: 2,
  COPY_HEADROOM: 2,
};

const LOGO_SIZE = 48; // Base logo size in px

export default function LogoLoop({
  speed = 100,
  direction = "left",
  logoHeight = 60,
  gap = 60,
  pauseOnHover = true,
  hoverSpeed = 0,
  scaleOnHover = true,
  fadeOut = true,
  fadeOutColor = "#070b10",
  className = "",
  ariaLabel = "Technology stack",
}) {
  const containerRef = useRef(null);
  const trackRef = useRef(null);
  const seqRef = useRef(null);
  const [prefersReducedMotion, setPrefersReducedMotion] = useState(false);
  const [containerWidth, setContainerWidth] = useState(0);
  const [sequenceRect, setSequenceRect] = useState({ width: 0, height: 0 });

  const offsetRef = useRef(0);
  const velocityRef = useRef(0);
  const targetVelocityRef = useRef(0);
  const isHoveredRef = useRef(false);
  const rafRef = useRef(null);
  const lastTimeRef = useRef(0);

  // Animation config
  const directionMultiplier = direction === "left" ? -1 : 1;
  const effectiveHoverSpeed = hoverSpeed === 0 ? speed * 0.1 : hoverSpeed;

  useEffect(() => {
    const mediaQuery = window.matchMedia("(prefers-reduced-motion: reduce)");
    setPrefersReducedMotion(mediaQuery.matches);
    const handler = (e) => setPrefersReducedMotion(e.matches);
    mediaQuery.addEventListener("change", handler);
    return () => mediaQuery.removeEventListener("change", handler);
  }, []);

  // Update dimensions
  const updateDimensions = () => {
    const container = containerRef.current;
    const seq = seqRef.current;
    if (!container || !seq) return;

    const cw = container.offsetWidth;
    const sr = seq.getBoundingClientRect();

    setContainerWidth(cw);
    setSequenceRect({ width: sr.width, height: sr.height });

    // Calculate copies needed
    const copiesNeeded = Math.ceil(cw / sr.width) + ANIMATION_CONFIG.COPY_HEADROOM;
    // The actual duplication is handled in render
  };

  // Animation loop
  const animate = (time) => {
    if (!lastTimeRef.current) lastTimeRef.current = time;
    const dt = Math.min((time - lastTimeRef.current) / 1000, 0.1);
    lastTimeRef.current = time;

    if (prefersReducedMotion) {
      rafRef.current = requestAnimationFrame(animate);
      return;
    }

    // Smooth velocity transition
    velocityRef.current += (targetVelocityRef.current - velocityRef.current) * (1 - Math.exp(-dt / ANIMATION_CONFIG.SMOOTH_TAU));
    offsetRef.current += velocityRef.current * dt;

    // Apply transform
    const seq = seqRef.current;
    if (seq) {
      seq.style.transform = `translate3d(${offsetRef.current}px, 0, 0)`;
    }

    // Wrap offset
    const seqWidth = sequenceRect.width;
    if (seqWidth > 0) {
      if (directionMultiplier === -1) {
        if (offsetRef.current <= -seqWidth) {
          offsetRef.current += seqWidth;
        } else if (offsetRef.current > 0) {
          offsetRef.current -= seqWidth;
        }
      } else {
        if (offsetRef.current >= seqWidth) {
          offsetRef.current -= seqWidth;
        } else if (offsetRef.current < -seqWidth) {
          offsetRef.current += seqWidth;
        }
      }
    }

    rafRef.current = requestAnimationFrame(animate);
  };

  // Handle hover
  const handleMouseEnter = () => {
    if (!pauseOnHover) return;
    isHoveredRef.current = true;
    targetVelocityRef.current = directionMultiplier * effectiveHoverSpeed;
  };

  const handleMouseLeave = () => {
    if (!pauseOnHover) return;
    isHoveredRef.current = false;
    targetVelocityRef.current = directionMultiplier * speed;
  };

  // Initialize
  useEffect(() => {
    targetVelocityRef.current = directionMultiplier * speed;
    velocityRef.current = directionMultiplier * speed;

    updateDimensions();

    const ro = new ResizeObserver(updateDimensions);
    const container = containerRef.current;
    if (container) ro.observe(container);

    rafRef.current = requestAnimationFrame(animate);

    return () => {
      if (rafRef.current) cancelAnimationFrame(rafRef.current);
      ro.disconnect();
    };
  }, [speed, direction, pauseOnHover, hoverSpeed, prefersReducedMotion]);

  // Update target velocity when speed/direction changes
  useEffect(() => {
    if (!isHoveredRef.current) {
      targetVelocityRef.current = directionMultiplier * speed;
    }
  }, [speed, direction]);

  // Render logo item
  const renderLogoItem = (logo, index) => {
    const { Component, label } = logo;
    const logoStyle = {
      display: "flex",
      alignItems: "center",
      justifyContent: "center",
      width: logoHeight,
      height: logoHeight,
      flexShrink: 0,
      color: "var(--text)",
      opacity: 0.8,
      transition: "opacity 0.3s ease, transform 0.3s ease",
    };

    if (scaleOnHover) {
      logoStyle.transform = "scale(1)";
    }

    return (
      <div
        key={index}
        style={logoStyle}
        className="logoloop-logo"
        onMouseEnter={scaleOnHover ? () => (logoStyle.transform = "scale(1.2)") : undefined}
        onMouseLeave={scaleOnHover ? () => (logoStyle.transform = "scale(1)") : undefined}
        role="img"
        aria-label={label}
      >
        <Component width={logoHeight * 0.7} height={logoHeight * 0.7} />
      </div>
    );
  };

  // Build logo lists (duplicated for seamless loop)
  const baseLogos = LOGOS;
  const copiesNeeded = Math.max(ANIMATION_CONFIG.MIN_COPIES, Math.ceil((containerWidth || 1920) / (logoHeight + gap)) + ANIMATION_CONFIG.COPY_HEADROOM);
  const logoLists = Array.from({ length: copiesNeeded }, (_, i) =>
    baseLogos.map((logo, j) => ({ ...logo, key: `${i}-${j}` }))
  ).flat();

  // CSS variables for fade
  const cssVariables = {
    "--logoloop-gap": `${gap}px`,
    "--logoloop-logo-height": `${logoHeight}px`,
    "--logoloop-fade-color": fadeOutColor,
  };

  const rootClasses = "logoloop";
  const trackClasses = "logoloop-track";

  return (
    <div
      ref={containerRef}
      className={`logoloop-container ${className}`}
      style={{
        position: "relative",
        overflow: "hidden",
        width: "100%",
        height: logoHeight,
        ...cssVariables,
      }}
      onMouseEnter={handleMouseEnter}
      onMouseLeave={handleMouseLeave}
      role="region"
      aria-label={ariaLabel}
    >
      {/* Fade gradients */}
      {fadeOut && (
        <>
          <div
            className="logoloop-fade logoloop-fade-left"
            style={{
              position: "absolute",
              inset: 0,
              zIndex: 2,
              pointerEvents: "none",
              background: `linear-gradient(to right, var(--logoloop-fade-color), transparent)`,
              width: "150px",
              left: 0,
            }}
          />
          <div
            className="logoloop-fade logoloop-fade-right"
            style={{
              position: "absolute",
              inset: 0,
              zIndex: 2,
              pointerEvents: "none",
              background: `linear-gradient(to left, var(--logoloop-fade-color), transparent)`,
              width: "150px",
              right: 0,
            }}
          />
        </>
      )}

      <div
        ref={trackRef}
        className={trackClasses}
        style={{
          display: "flex",
          willChange: "transform",
          width: "max-content",
        }}
      >
        <div
          ref={seqRef}
          className="logoloop-sequence"
          style={{
            display: "flex",
            alignItems: "center",
            gap: gap,
            padding: `0 ${gap}px`,
            minWidth: "max-content",
          }}
        >
          {logoLists.map((logo, index) => renderLogoItem(logo, index))}
        </div>
      </div>
    </div>
  );
}