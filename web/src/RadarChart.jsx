import React from "react";

// Local implementation of the @bklitui/ui/charts RadarChart component family
// (RadarChart, RadarGrid, RadarAxis, RadarLabels, RadarArea), following the same
// approach as `Legend.jsx` and `ComposedChart.jsx`: the `@bklitui/ui/charts`
// package is not installed in this project, so this is a faithful local
// equivalent with the same composable API and call shape:
//
//   <RadarChart data={data} metrics={metrics} levels={5} animate seriesDim={i}>
//     <RadarGrid />
//     <RadarAxis />
//     <RadarLabels />
//     {data.map((item, index) => <RadarArea key={item.label} index={index} />)}
//   </RadarChart>
//
// It renders a real SVG radar chart; it is NOT a Chart.js wrapper.
//
// `data` is an array of profiles: { label, color, values: { <metricKey>: 0..100 } }.
// `metrics` is an ordered array of { key, label } describing the radial axes.
// Values are expected on a 0 to 100 scale (BKLIT RadarArea contract); the caller
// normalizes at the visualization boundary and leaves the stored analysis data
// untouched.

// ---------------------------------------------------------------------------
// Responsive measurement (no dependencies; same as ComposedChart.jsx)
// ---------------------------------------------------------------------------

function useMeasuredSize() {
  const ref = React.useRef(null);
  const [size, setSize] = React.useState({ width: 0, height: 0 });
  React.useEffect(() => {
    const el = ref.current;
    if (!el) return undefined;
    const update = () => {
      const rect = el.getBoundingClientRect();
      setSize({ width: rect.width, height: rect.height });
    };
    update();
    if (typeof ResizeObserver === "undefined") {
      window.addEventListener("resize", update);
      return () => window.removeEventListener("resize", update);
    }
    const observer = new ResizeObserver(update);
    observer.observe(el);
    return () => observer.disconnect();
  }, []);
  return [ref, size];
}

// ---------------------------------------------------------------------------
// Composable marker components. These carry configuration into RadarChart via
// React.Children; they render nothing on their own.
// ---------------------------------------------------------------------------

function RadarGrid() {
  return null;
}
RadarGrid.displayName = "RadarGrid";

function RadarAxis() {
  return null;
}
RadarAxis.displayName = "RadarAxis";

function RadarLabels() {
  return null;
}
RadarLabels.displayName = "RadarLabels";

// One radar area. `index` selects which `data` profile to draw; optional
// per-area styling (fillOpacity, strokeWidth) can be passed for fine control.
function RadarArea({ index }) {
  return null;
}
RadarArea.displayName = "RadarArea";

// ---------------------------------------------------------------------------
// RadarChart
// ---------------------------------------------------------------------------

function RadarChart({
  data = [],
  metrics = [],
  size,
  levels = 5,
  animate = true,
  seriesDim = null,
  ariaLabel = "Radar chart",
  className = "",
  children,
}) {
  const [containerRef, { width, height }] = useMeasuredSize();
  const [hover, setHover] = React.useState(null); // pointer hovered profile index

  // Introspect children for the composable markers.
  const kids = React.Children.toArray(children);
  const showGrid = kids.some((c) => React.isValidElement(c) && c.type === RadarGrid);
  const showAxes = kids.some((c) => React.isValidElement(c) && c.type === RadarAxis);
  const showLabels = kids.some((c) => React.isValidElement(c) && c.type === RadarLabels);
  const areaChildren = kids.filter((c) => React.isValidElement(c) && c.type === RadarArea);

  // Plot geometry. The radar is a centered square; radius is the tightest fit of
  // the available box with gutters for the six radial labels (which hang off the
  // outer ring) so none are clipped or pushed against the card edge.
  const centerX = width / 2;
  const centerY = height / 2;
  const labelBudget = 32; // horizontal room for a side label from the center
  const verticalBudget = 30; // vertical room for the top/bottom labels
  const bounded = Math.min(centerX - labelBudget, centerY - verticalBudget);
  const maxR = size ? Math.min(size / 2 - 4, bounded) : bounded;
  const R = Math.max(26, maxR);

  const metricCount = metrics.length;
  const N = Math.max(1, metricCount);
  const angleRad = (i) => -Math.PI / 2 + (i * 2 * Math.PI) / N; // index 0 = top
  const polar = (i, radius) => ({
    x: centerX + Math.cos(angleRad(i)) * radius,
    y: centerY + Math.sin(angleRad(i)) * radius,
  });

  // Level rings + spokes (decorative; rendered behind the areas).
  const rings = showGrid
    ? Array.from({ length: levels }, (_, lvl) => {
        const frac = (lvl + 1) / levels;
        const pts = metrics.map((_, i) => polar(i, R * frac));
        return pts;
      }).filter(() => R > 0)
    : [];

  // Fill + read behavior for each area, composing pointer hover with the legend
  // hover (seriesDim). A hovered profile stays at full strength; the others fade.
  const areaOpacity = (i) => {
    let o = 1;
    let hi = false;
    if (hover != null && hover !== i) o *= 0.24;
    if (hover === i) hi = true;
    if (seriesDim != null && seriesDim !== i) o *= 0.45;
    return { o, hi };
  };

  return (
    <div
      ref={containerRef}
      className={`radar-chart${className ? ` ${className}` : ""}`}
      role="group"
      aria-label={ariaLabel}
      tabIndex={0}
      style={{ position: "relative", width: "100%", height: "100%", minWidth: 0 }}
      onPointerLeave={() => setHover(null)}
    >
      {width > 0 && height > 0 && (
        <svg width={width} height={height} viewBox={`0 0 ${width} ${height}`}>
          <title>{ariaLabel}</title>

          {/* concentric level rings */}
          {rings.map((pts, lvl) => (
            <polygon
              key={lvl}
              points={pts.map((p) => `${p.x},${p.y}`).join(" ")}
              fill="none"
              style={{ stroke: "var(--line)" }}
              opacity={lvl === levels - 1 ? 0.55 : 0.3}
              strokeWidth={1}
              pointerEvents="none"
            />
          ))}

          {/* radial axes (spokes) */}
          {showAxes &&
            metrics.map((m, i) => {
              const p = polar(i, R);
              return (
                <line
                  key={m.key}
                  x1={centerX}
                  y1={centerY}
                  x2={p.x}
                  y2={p.y}
                  style={{ stroke: "var(--line)" }}
                  opacity={0.3}
                  strokeWidth={1}
                  pointerEvents="none"
                />
              );
            })}

          {/* ring value labels along the bottom spoke (index = metricCount - 3 is the
              bottom axis for 6 metrics; fall back to the last axis otherwise). */}
          {showAxes &&
            rings.map((pts, lvl) => {
              const bottomIdx = metricCount % 2 === 0 ? Math.floor(metricCount / 2) : 0;
              const value = Math.round(((lvl + 1) / levels) * 100);
              const p = polar(bottomIdx, R * ((lvl + 1) / levels));
              return (
                <text
                  key={value}
                  x={p.x}
                  y={p.y + 3.5}
                  textAnchor="middle"
                  className="radar-ring-label"
                  pointerEvents="none"
                >
                  {value}
                </text>
              );
            })}

          {/* metric labels (readable text, kept above the areas so nothing is hidden) */}
          {showLabels &&
            metrics.map((m, i) => {
              const rad = angleRad(i);
              const sn = Math.sin(rad);
              // Side labels ("Afternoon", "Variation", ...) hang just outside the
              // ring at the vertex; top/bottom labels sit above/below the polygon.
              const labelR = R + 7;
              let x = centerX + Math.cos(rad) * labelR;
              let y = centerY + sn * labelR;
              let dy = 4;
              if (sn <= -0.7) {
                y = centerY - R - 11;
                dy = 0;
              } else if (sn >= 0.7) {
                y = centerY + R + 17;
                dy = 0;
              } else {
                dy = sn > 0 ? 13 : 2;
              }
              // Safety clamp so a label can never leave the SVG box.
              x = Math.min(Math.max(x, 6), width - 6);
              y = Math.min(Math.max(y, 12), height - 6);
              return (
                <text
                  key={m.key}
                  x={x}
                  y={y}
                  dy={dy}
                  textAnchor="middle"
                  className="radar-label"
                >
                  {m.label}
                </text>
              );
            })}

          {/* radar areas */}
          {areaChildren.map((child, idx) => {
            const areaIndex = child.props.index ?? idx;
            const item = data[areaIndex];
            if (!item) return null;
            const { o, hi } = areaOpacity(areaIndex);
            const rad = (i) => polar(i, R * Math.min(Math.max(item.values[metrics[i]?.key] ?? 0, 0) / 100, 1));
            const pts = metrics.map((_, i) => rad(i));
            const fillOpacity = child.props.fillOpacity ?? 0.16;
            const strokeWidth = hi ? 2.3 : child.props.strokeWidth ?? 1.6;
            const valueTitle = metrics
              .map((m) => `${m.label} ${Math.round((item.values[m.key] ?? 0) * 10) / 10}%`)
              .join(" · ");
            return (
              <g
                key={item.label || areaIndex}
                opacity={o}
                onMouseEnter={() => setHover(areaIndex)}
                onMouseLeave={() => setHover((h) => (h === areaIndex ? null : h))}
              >
                <g
                  className={animate ? "radar-area-in" : ""}
                  style={{
                    transformOrigin: `${centerX}px ${centerY}px`,
                    animationDelay: animate ? `${areaIndex * 0.12}s` : "0s",
                  }}
                >
                  <path
                    d={`M${pts.map((p) => `${p.x} ${p.y}`).join(" L")} Z`}
                    style={{ fill: item.color, stroke: item.color }}
                    fillOpacity={fillOpacity}
                    strokeOpacity={1}
                    strokeWidth={strokeWidth}
                    strokeLinejoin="round"
                    strokeLinecap="round"
                    pointerEvents="all"
                  >
                    <title>{`${item.label}: ${valueTitle}`}</title>
                  </path>
                  {pts.map((p, i) => (
                    <circle
                      key={metrics[i]?.key}
                      cx={p.x}
                      cy={p.y}
                      r={hi ? 3.4 : 2.7}
                      style={{ fill: item.color }}
                      stroke="var(--bg)"
                      strokeWidth={1}
                      pointerEvents="none"
                    >
                      <title>{`${item.label} · ${metrics[i]?.label} ${Math.round((item.values[metrics[i]?.key] ?? 0) * 10) / 10}%`}</title>
                    </circle>
                  ))}
                </g>
              </g>
            );
          })}
        </svg>
      )}
    </div>
  );
}

export { RadarChart, RadarGrid, RadarAxis, RadarLabels, RadarArea };