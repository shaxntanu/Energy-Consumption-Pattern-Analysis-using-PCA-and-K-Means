import { useEffect, useRef, useState } from "react";
import { createPortal } from "react-dom";

/**
 * GlowCursor: a soft radial glow that follows the pointer.
 *
 * Earlier versions rendered the trail on a canvas inside the wrapper and
 * depended on an elastic chain, an animation loop and an idle-fade timer; in
 * practice the glow either never appeared or faded out within a second of the
 * mouse pausing, so it read as broken. This version is deliberately simple and
 * hard to break: one fixed-position orb painted with a plain CSS radial
 * gradient, moved with a transform on window pointermove (passive listener,
 * no rAF loop), shown from the moment the pointer enters the page.
 *
 * The orb is rendered through a portal to document.body, so no ancestor's
 * stacking context (the hero-copy uses isolation: isolate) can trap it behind
 * sections lower on the page; it always paints above the whole app.
 *
 * Contracts kept from the old component:
 *   - renders its children unchanged (same public usage);
 *   - honors prefers-reduced-motion (renders no orb);
 *   - never intercepts clicks (pointer-events: none).
 */
export default function GlowCursor({
  children,
  color = "#48d7c2",
  secondaryColor = "#b78cff",
  opacity = 0.5,
  className = "",
}) {
  const orbRef = useRef(null);
  const [reducedMotion, setReducedMotion] = useState(false);

  useEffect(() => {
    const mq = window.matchMedia("(prefers-reduced-motion: reduce)");
    setReducedMotion(mq.matches);
    const handler = (e) => setReducedMotion(e.matches);
    mq.addEventListener("change", handler);
    return () => mq.removeEventListener("change", handler);
  }, []);

  useEffect(() => {
    if (reducedMotion) return undefined;
    const orb = orbRef.current;
    if (!orb) return undefined;

    // The orb is anchored at (0,0) and moved by transform, so its top-left
    // corner lands on the cursor; the gradient diffuses the light around it.
    const onPointerMove = (e) => {
      orb.style.transform = `translate(${e.clientX - 120}px, ${e.clientY - 120}px)`;
    };
    const onPointerEnter = () => {
      orb.style.opacity = String(opacity);
    };
    const onPointerLeave = () => {
      orb.style.opacity = "0";
    };
    window.addEventListener("pointermove", onPointerMove, { passive: true });
    document.documentElement.addEventListener("pointerenter", onPointerEnter);
    document.documentElement.addEventListener("pointerleave", onPointerLeave);
    return () => {
      window.removeEventListener("pointermove", onPointerMove);
      document.documentElement.removeEventListener("pointerenter", onPointerEnter);
      document.documentElement.removeEventListener("pointerleave", onPointerLeave);
    };
  }, [reducedMotion, opacity]);

  return (
    <div className={`glow-cursor ${className}`} style={{ position: "relative" }}>
      {!reducedMotion &&
        createPortal(
          <div
            ref={orbRef}
            aria-hidden="true"
            className="glow-cursor__orb"
            style={{
              position: "fixed",
              left: 0,
              top: 0,
              width: 240,
              height: 240,
              borderRadius: "50%",
              pointerEvents: "none",
              zIndex: 2147483647,
              opacity: 0,
              transform: "translate(-240px, -240px)",
              transition: "opacity 0.25s ease",
              background: `radial-gradient(circle, ${color} 0%, ${secondaryColor} 42%, transparent 70%)`,
              mixBlendMode: "screen",
            }}
          />,
          document.body,
        )}
      <div style={{ position: "relative" }}>{children}</div>
    </div>
  );
}