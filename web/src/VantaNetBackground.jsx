// VANTA.NET hero background, with clean framework integration.
//
// Deliberately scoped to the hero *copy* column only (`.hero-copy`), never to
// the whole page and never behind the chart carousel, the charts band, tables,
// or any dense dashboard, so the animation is decoration on the hero, not
// visual noise behind results. The canvas is `aria-hidden` and has
// `pointer-events: none`, so it can never intercept clicks meant for the hero
// buttons.
//
// Accessibility / performance contract:
//   - skipped entirely under `prefers-reduced-motion: reduce`;
//   - skipped when WebGL is unavailable (the page keeps its plain dark
//     background, so no error is thrown and no gradient needs to be "fixed");
//   - destroyed on unmount so there are no leaked rAF loops or contexts;
//   - colors come from the project's theme tokens (--cyan #48d7c2 points on
//     --bg #070b10), and mouse interaction is limited to a gentle parallax so
//     the page does not feel like a game.
//
// The minified vendor code is NOT copied into this repository: `vanta` and its
// peer `three` are regular npm dependencies imported here, exactly as the
// library's React integration is documented.

import { useEffect, useRef } from "react";
import * as THREE from "three";
import NET from "vanta/dist/vanta.net.min.js";

export default function VantaNetBackground() {
  const hostRef = useRef(null);
  const effectRef = useRef(null);

  useEffect(() => {
    const host = hostRef.current;
    if (!host) return undefined;

    // Respect the user's motion preference first: no animation at all.
    if (window.matchMedia("(prefers-reduced-motion: reduce)").matches) {
      return undefined;
    }
    // No WebGL, no animation: the hero simply keeps its plain dark ground.
    if (!window.WebGLRenderingContext) {
      return undefined;
    }

    let cancelled = false;
    // Give the hero text its first paint before the canvas work starts, so
    // the largest contentful paint is not delayed by the shader setup.
    const start = window.setTimeout(() => {
      if (cancelled || !host) return;
      try {
        effectRef.current = NET({
          el: host,
          THREE,
          mouseControls: true, // gentle parallax only, with no click effects
          touchControls: true,
          gyroControls: false,
          minHeight: 240,
          minWidth: 240,
          scale: 1.0,
          scaleMobile: 1.0,
          points: 12,
          maxDistance: 22,
          spacing: 16,
          showDots: true,
          color: 0x48d7c2, // --cyan, the project's accent
          backgroundColor: 0x070b10, // --bg, the page ground
        });
      } catch (err) {
        // Context creation or shader compile failure: fall back to the plain
        // background rather than breaking the hero.
        console.warn("VANTA.NET background unavailable:", err);
      }
    }, 150);

    return () => {
      cancelled = true;
      window.clearTimeout(start);
      if (effectRef.current && typeof effectRef.current.destroy === "function") {
        effectRef.current.destroy();
      }
      effectRef.current = null;
    };
  }, []);

  return <div ref={hostRef} className="vanta-bg" aria-hidden="true" />;
}
