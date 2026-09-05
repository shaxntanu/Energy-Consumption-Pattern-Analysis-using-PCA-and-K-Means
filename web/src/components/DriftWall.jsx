import { useEffect, useRef, useState, useMemo } from "react";

/**
 * DriftWall — 3D perspective drifting wall gallery for matplotlib images.
 * Adapted from @react-bits/DriftWall-JS-CSS for this project's theme.
 * Items should be images from /public/results/ (matplotlib outputs).
 */
export default function DriftWall({
  columns = 5,
  tileWidth = 200,
  tileHeight = 132,
  gap = 18,
  radius = 14,
  tilt = 16,
  turn = -14,
  roll = 0,
  perspective = 1200,
  depth = 120,
  speed = 42,
  direction = "up",
  variance = 0.45,
  parallax = 0.6,
  pauseOnHover = true,
  lift = 64,
  fade = 0.6,
  dim = 0.55,
  grayscale = false,
  overlay = "#060010",
  items = [],
  className = "",
}) {
  const containerRef = useRef(null);
  const planeRef = useRef(null);
  const trackRefsRef = useRef([]);
  const [containerHeight, setContainerHeight] = useState(0);
  const [activeId, setActiveId] = useState(null);
  const [prefersReducedMotion, setPrefersReducedMotion] = useState(false);

  const offsetsRef = useRef([]);
  const velocitiesRef = useRef([]);
  const hoveredColRef = useRef(null);
  const wallHoveredRef = useRef(false);
  const pointerRef = useRef({ x: 0, y: 0 });
  const pointerDampedRef = useRef({ x: 0, y: 0 });
  const lastTsRef = useRef(0);

  // Default items - matplotlib output images from /public/results/
  const DEFAULT_ITEMS = useMemo(() => [
    { id: "load-shapes", image: "/results/load_shapes.png", title: "Average Load Shapes", href: "#charts" },
    { id: "pca-variance", image: "/results/pca_variance.png", title: "PCA Explained Variance", href: "#charts" },
    { id: "k-selection", image: "/results/k_selection.png", title: "K-Selection Metrics", href: "#charts" },
    { id: "cluster-radar", image: "/results/cluster_radar.png", title: "Cluster Profiles Radar", href: "#charts" },
    { id: "cluster-0", image: "/results/cluster_0_profile.png", title: "Cluster 0: Night Owls", href: "#charts" },
    { id: "cluster-1", image: "/results/cluster_1_profile.png", title: "Cluster 1: Early Birds", href: "#charts" },
    { id: "cluster-2", image: "/results/cluster_2_profile.png", title: "Cluster 2: Day Workers", href: "#charts" },
    { id: "cluster-3", image: "/results/cluster_3_profile.png", title: "Cluster 3: Evening Peak", href: "#charts" },
    { id: "seasonal", image: "/results/seasonal_stability.png", title: "Seasonal Stability", href: "#charts" },
    { id: "longitudinal", image: "/results/longitudinal_ari.png", title: "Longitudinal ARI", href: "#charts" },
    { id: "validation", image: "/results/validation_sweep.png", title: "Validation Sweep", href: "#charts" },
    { id: "explainability", image: "/results/explainability.png", title: "Feature Importance", href: "#charts" },
    { id: "real-world", image: "/results/real_world.png", title: "Real-World Demo", href: "#charts" },
    { id: "benchmark", image: "/results/benchmark.png", title: "C++ Benchmark", href: "#performance" },
    { id: "pipeline", image: "/results/pipeline.png", title: "Pipeline Flow", href: "#about" },
  ], []);

  const displayItems = items.length > 0 ? items : DEFAULT_ITEMS;

  // cx helper for column factor
  const cx = useMemo(() => {
    const arr = [];
    for (let i = 0; i < columns; i++) {
      // Golden ratio-ish distribution
      arr.push(0.618 + Math.sin(i * 1.37) * 0.382);
    }
    return arr;
  }, [columns]);

  // Check reduced motion
  useEffect(() => {
    const mediaQuery = window.matchMedia("(prefers-reduced-motion: reduce)");
    setPrefersReducedMotion(mediaQuery.matches);
    const handler = (e) => setPrefersReducedMotion(e.matches);
    mediaQuery.addEventListener("change", handler);
    return () => mediaQuery.removeEventListener("change", handler);
  }, []);

  // Distribute items into columns
  const columnItems = useMemo(() => {
    const cols = Array.from({ length: columns }, () => []);
    displayItems.forEach((item, i) => {
      cols[i % columns].push(item);
    });
    return cols;
  }, [displayItems, columns]);

  // Column metadata
  const columnMeta = useMemo(() => {
    const copyHeight = tileHeight + gap;
    return columnItems.map((col) => {
      const copies = Math.ceil((containerHeight * 1.6) / copyHeight) + 1;
      return { copyHeight, copies };
    });
  }, [columnItems, containerHeight, tileHeight, gap]);

  // Container height via ResizeObserver
  useEffect(() => {
    const container = containerRef.current;
    if (!container) return;

    const ro = new ResizeObserver((entries) => {
      for (const entry of entries) {
        setContainerHeight(entry.contentRect.height);
      }
    });
    ro.observe(container);

    // Initialize offsets and velocities
    const dirSign = direction === "up" ? -1 : 1;
    offsetsRef.current = Array.from({ length: columns }, (_, i) => Math.random() * columnMeta[i]?.copyHeight || 0);
    velocitiesRef.current = columnMeta.map((meta, i) => {
      const altSign = i % 2 === 0 ? 1 : -1;
      return dirSign * speed * (cx[i] || 1) * altSign;
    });

    return () => ro.disconnect();
  }, [columns, columnMeta, cx, direction, speed]);

  // Apply plane transform (perspective tilt)
  const applyPlaneTransform = () => {
    const plane = planeRef.current;
    if (!plane) return;
    const { x: px, y: py } = pointerDampedRef.current;
    plane.style.transform = `translate(-50%, -50%) scale(1.18) rotateX(${tilt + py}deg) rotateY(${turn + px}deg) rotateZ(${roll}deg) translateZ(${-depth}px)`;
  };

  // Animation loop
  useEffect(() => {
    if (prefersReducedMotion) return;

    const animate = (ts) => {
      if (!lastTsRef.current) lastTsRef.current = ts;
      const dt = Math.min((ts - lastTsRef.current) / 1000, 0.1);
      lastTsRef.current = ts;

      // Damp pointer for parallax
      const damp = Math.exp(-dt / 0.12);
      pointerDampedRef.current.x = pointerDampedRef.current.x * damp + pointerRef.current.x * (1 - damp);
      pointerDampedRef.current.y = pointerDampedRef.current.y * damp + pointerRef.current.y * (1 - damp);

      applyPlaneTransform();

      if (!prefersReducedMotion) {
        columnItems.forEach((col, colIdx) => {
          const track = trackRefsRef.current[colIdx];
          if (!track) return;
          const meta = columnMeta[colIdx];
          if (!meta) return;

          // Pause on hover
          let pauseFactor = 1;
          if (pauseOnHover && wallHoveredRef.current) {
            if (hoveredColRef.current === colIdx) {
              pauseFactor = 0.15;
            } else {
              pauseFactor = 0.6;
            }
          }

          const ease = Math.exp(-dt / 0.28);
          const v = velocitiesRef.current[colIdx] * pauseFactor;
          offsetsRef.current[colIdx] += v * dt;

          // Modulo wrap
          const copyHeight = meta.copyHeight;
          offsetsRef.current[colIdx] = ((offsetsRef.current[colIdx] % copyHeight) + copyHeight) % copyHeight;

          track.style.transform = `translate3d(0, ${-offsetsRef.current[colIdx]}px, 0)`;
        });
      }

      requestAnimationFrame(animate);
    };

    requestAnimationFrame(animate);
  }, [columnItems, columnMeta, pauseOnHover, prefersReducedMotion]);

  // Pointer handlers
  const handlePointerMove = (e) => {
    const container = containerRef.current;
    if (!container) return;
    const rect = container.getBoundingClientRect();
    const nx = (e.clientX - rect.left) / rect.width - 0.5;
    const ny = (e.clientY - rect.top) / rect.height - 0.5;
    pointerRef.current.x = nx * parallax * 8;
    pointerRef.current.y = ny * parallax * 8;

    // Find hovered column
    const el = document.elementFromPoint(e.clientX, e.clientY);
    const tile = el?.closest("[data-tile-id]");
    if (tile) {
      const col = parseInt(tile.dataset.col, 10);
      hoveredColRef.current = col;
    }
  };

  const handlePointerLeaveWall = () => {
    wallHoveredRef.current = false;
    hoveredColRef.current = null;
    pointerRef.current = { x: 0, y: 0 };
  };

  const handlePointerEnterWall = () => {
    wallHoveredRef.current = true;
  };

  // Tile classes
  const tileClass = "driftwall-tile";
  const innerClass = "driftwall-inner";
  const imgClass = "driftwall-img";
  const overlayClass = "driftwall-overlay";

  // Mask style
  const maskStyle = {
    maskImage: `radial-gradient(ellipse 65% 75% at 50% 50%, black 40%, transparent 100%), linear-gradient(to bottom, transparent 10%, black 40%, black 60%, transparent 90%)`,
    WebkitMaskImage: `radial-gradient(ellipse 65% 75% at 50% 50%, black 40%, transparent 100%), linear-gradient(to bottom, transparent 10%, black 40%, black 60%, transparent 90%)`,
  };

  // CSS variables
  const cssVars = {
    "--dw-tile-w": `${tileWidth}px`,
    "--dw-tile-h": `${tileHeight}px`,
    "--dw-gap": `${gap}px`,
    "--dw-radius": `${radius}px`,
    "--dw-lift": `${lift}px`,
    "--dw-dim": dim,
    "--dw-gray": grayscale ? 1 : 0,
    "--dw-overlay": overlay,
    "--dw-edge-perspective": `${perspective}px`,
  };

  // Render a single tile
  const renderTile = (item, colIdx, copyIdx, itemIdx) => {
    const tileId = `${item.id}-${colIdx}-${copyIdx}`;
    const isActive = activeId === tileId;
    const zIndex = isActive ? 10 : 5;

    const commonProps = {
      "data-tile-id": tileId,
      "data-col": colIdx,
      onFocus: () => setActiveId(tileId),
      onBlur: () => setActiveId(activeId === tileId ? null : activeId),
    };

    const tileStyle = {
      width: tileWidth,
      height: tileHeight,
      flexShrink: 0,
      position: "relative",
      zIndex,
      perspective: perspective,
      transformStyle: "preserve-3d",
      transition: "transform 0.4s cubic-bezier(0.22, 1, 0.36, 1), opacity 0.4s ease, box-shadow 0.4s ease",
      filter: grayscale ? "grayscale(1)" : "none",
      opacity: isActive ? 1 : 1 - fade,
    };

    const innerStyle = {
      display: "block",
      width: "100%",
      height: "100%",
      borderRadius: radius,
      overflow: "hidden",
      transformStyle: "preserve-3d",
      transformOrigin: "center center",
      transition: "transform 0.3s ease, box-shadow 0.3s ease",
      boxShadow: isActive
        ? `0 ${lift}px ${lift * 2}px rgba(0, 0, 0, 0.5), 0 0 0 1px rgba(72, 215, 194, 0.3)`
        : `0 0 ${lift / 2}px rgba(0, 0, 0, 0.3)`,
    };

    const imgStyle = {
      width: "100%",
      height: "100%",
      objectFit: "cover",
      display: "block",
      transition: "transform 0.4s ease, filter 0.4s ease",
      filter: `brightness(${isActive ? 1 : dim})`,
    };

    const overlayStyle = {
      position: "absolute",
      inset: 0,
      background: overlay,
      opacity: isActive ? 0 : fade,
      borderRadius: radius,
      transition: "opacity 0.3s ease",
      pointerEvents: "none",
    };

    const content = (
      <span className={innerClass} style={innerStyle}>
        <img
          className={imgClass}
          src={item.image}
          alt={item.title}
          style={imgStyle}
          loading="lazy"
        />
        <span className={overlayClass} style={overlayStyle} />
      </span>
    );

    if (item.href) {
      return (
        <a
          key={tileId}
          href={item.href}
          className={tileClass}
          style={tileStyle}
          {...commonProps}
        >
          {content}
        </a>
      );
    }

    return (
      <div
        key={tileId}
        className={tileClass}
        style={tileStyle}
        role="button"
        tabIndex={0}
        {...commonProps}
      >
        {content}
      </div>
    );
  };

  return (
    <div
      ref={containerRef}
      className={`driftwall ${className}`}
      style={{
        position: "relative",
        width: "100%",
        height: 520,
        overflow: "hidden",
        ...cssVars,
      }}
      onPointerMove={handlePointerMove}
      onPointerLeave={handlePointerLeaveWall}
      onPointerEnter={handlePointerEnterWall}
    >
      <div
        ref={planeRef}
        className="driftwall-plane"
        style={{
          position: "absolute",
          top: "50%",
          left: "50%",
          width: "100%",
          height: "100%",
          display: "flex",
          flexDirection: "row",
          alignItems: "center",
          justifyContent: "center",
          gap: gap,
          transformStyle: "preserve-3d",
          willChange: "transform",
        }}
      >
        {columnItems.map((col, colIdx) => (
          <div
            key={colIdx}
            ref={(el) => (trackRefsRef.current[colIdx] = el)}
            className="driftwall-track"
            style={{
              display: "flex",
              flexDirection: "column",
              gap: gap,
              willChange: "transform",
              alignItems: "center",
            }}
          >{col.map((item, itemIdx) => {
              const meta = columnMeta[colIdx];
              if (!meta) return null;
              return Array.from({ length: meta.copies }, (_, copyIdx) =>
                renderTile(item, colIdx, copyIdx, itemIdx)
              );
            })}
          </div>
        ))}
      </div>
      <div style={maskStyle} aria-hidden="true" />
    </div>
  );
}