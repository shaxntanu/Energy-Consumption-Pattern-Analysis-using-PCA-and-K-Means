import React from "react";

// Local implementation of the @bklitui/ui/charts ComposedChart component family
// (ComposedChart, SeriesBar, Line, Grid, XAxis, YAxis, ChartTooltip), following
// the same approach as `Legend.jsx`: the `@bklitui/ui/charts` package is not
// installed in this project, so this is a faithful local equivalent with the
// same composable API and call shape. It renders a real SVG composed chart -
// it is NOT a Chart.js wrapper.

// ---------------------------------------------------------------------------
// Small math helpers
// ---------------------------------------------------------------------------

function clamp(value, lo, hi) {
  return Math.min(hi, Math.max(lo, value));
}

function roundTo(value, decimals) {
  const m = 10 ** decimals;
  return Math.round(value * m) / m;
}

// "Nice" step (1 / 2 / 5 × 10^k) for readable axis ticks.
function niceNumber(value, round) {
  const exp = Math.floor(Math.log10(Math.max(value, 1e-12)));
  const f = value / 10 ** exp;
  let nf;
  if (round) {
    if (f < 1.5) nf = 1;
    else if (f < 3) nf = 2;
    else if (f < 7) nf = 5;
    else nf = 10;
  } else if (f <= 1) nf = 1;
  else if (f <= 2) nf = 2;
  else if (f <= 5) nf = 5;
  else nf = 10;
  return nf * 10 ** exp;
}

// Ticks on a domain expanded outward to clean values.
function niceTicks(min, max, count) {
  if (!(max > min)) return [min];
  const step = niceNumber((max - min) / Math.max(1, count - 1), true);
  const from = Math.floor(min / step) * step;
  const to = Math.ceil(max / step) * step;
  const ticks = [];
  for (let v = from; v <= to + step / 1e6; v += step) ticks.push(roundTo(v, 8));
  return ticks;
}

// Compact tick label ("1.20" -> "1.2", "0.30" -> "0.3").
function formatTick(value) {
  return String(Number(value.toFixed(6)));
}

// ---------------------------------------------------------------------------
// Local Catmull-Rom curve builder
//
// Equivalent to `curveCatmullRom.alpha(0.42)` from `@visx/curve`, which is not
// installed in this project. Call shape is identical, so swapping in the real
// @visx/curve later is a drop-in replacement. `alpha` is the tangent scale on
// the classic Catmull-Rom-to-cubic-Bezier conversion; endpoints are clamped
// rather than overshooting. Produces a restrained smooth line through every
// point without flattening the K-wise trend.
// ---------------------------------------------------------------------------

const curveCatmullRom = {
  alpha(alphaValue = 0.5) {
    return function buildPath(points) {
      if (points.length === 0) return "";
      let d = `M${roundTo(points[0].x, 3)} ${roundTo(points[0].y, 3)}`;
      if (points.length < 2) return d;
      const t = alphaValue;
      for (let i = 0; i < points.length - 1; i++) {
        const p0 = points[i - 1] || points[i];
        const p1 = points[i];
        const p2 = points[i + 1];
        const p3 = points[i + 2] || points[i + 1];
        const c1x = p1.x + (p2.x - p0.x) * t;
        const c1y = p1.y + (p2.y - p0.y) * t;
        const c2x = p2.x - (p3.x - p1.x) * t;
        const c2y = p2.y - (p3.y - p1.y) * t;
        d += ` C${roundTo(c1x, 3)} ${roundTo(c1y, 3)}, ${roundTo(c2x, 3)} ${roundTo(
          c2y,
          3,
        )}, ${roundTo(p2.x, 3)} ${roundTo(p2.y, 3)}`;
      }
      return d;
    };
  },
};

// ---------------------------------------------------------------------------
// Responsive measurement (no dependencies)
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
// Composable marker components. These carry configuration into ComposedChart
// (introspected via React.Children) and render nothing themselves, mirroring
// how Legend.jsx injects a shared profile into its item children.
// ---------------------------------------------------------------------------

function SeriesBar() {
  return null;
}
SeriesBar.displayName = "SeriesBar";

function Line() {
  return null;
}
Line.displayName = "Line";

function Grid() {
  return null;
}
Grid.displayName = "Grid";

function XAxis() {
  return null;
}
XAxis.displayName = "XAxis";

function YAxis() {
  return null;
}
YAxis.displayName = "YAxis";

function ChartTooltip() {
  return null;
}
ChartTooltip.displayName = "ChartTooltip";

// ---------------------------------------------------------------------------
// ComposedChart
//
// Example (BKLIT call shape, adapted to clean names for two series):
//
//   <ComposedChart data={rows} xDataKey="k" selectedIndex={1} ariaLabel="...">
//     <Grid horizontal />
//     <YAxis yAxisId="left" orientation="left" label="Silhouette" />
//     <YAxis yAxisId="right" orientation="right" label="Davies-Bouldin" />
//     <SeriesBar yAxisId="left" dataKey="silhouette" fill="var(--x)" ... />
//     <Line yAxisId="right" dataKey="daviesBouldin" curve={curveCatmullRom.alpha(0.42)} ... />
//     <ChartTooltip showCrosshair={false} />
//     <XAxis numTicks={9} />
//   </ComposedChart>
// ---------------------------------------------------------------------------

const MARGIN = { top: 12, right: 30, bottom: 34, left: 30 };
const AXIS_WIDTH = 42; // horizontal room for tick labels on each side

function ComposedChart({
  data,
  xDataKey,
  margin = MARGIN,
  aspectRatio,
  barGap = 0,
  maxBarSize = 32,
  selectedIndex = null,
  seriesDim = null, // "first" | "second", legend-driven series emphasis
  ariaLabel = "Chart",
  children,
}) {
  const [containerRef, { width, height }] = useMeasuredSize();
  const [active, setActive] = React.useState(null); // hovered/focused category index
  const [pinned, setPinned] = React.useState(false); // click/keyboard kept active
  const [pointer, setPointer] = React.useState(null); // {x, y} in px
  const pinnedRef = React.useRef(false);
  const setPin = (value) => {
    pinnedRef.current = value;
    setPinned(value);
  };

  const childrenArray = React.Children.toArray(children);
  const series = childrenArray.filter(
    (child) =>
      React.isValidElement(child) &&
      (child.type === SeriesBar || child.type === Line),
  );
  const gridChild = childrenArray.find(
    (child) => React.isValidElement(child) && child.type === Grid,
  );
  const xAxisChild = childrenArray.find(
    (child) => React.isValidElement(child) && child.type === XAxis,
  );
  const yAxisChildren = childrenArray.filter(
    (child) => React.isValidElement(child) && child.type === YAxis,
  );
  const tooltipChild = childrenArray.find(
    (child) => React.isValidElement(child) && child.type === ChartTooltip,
  );

  const n = data.length;
  const plotLeft = margin.left + AXIS_WIDTH;
  const plotRight = width - margin.right - AXIS_WIDTH;
  const plotTop = margin.top;
  const plotBottom = height - margin.bottom;
  const plotW = plotRight - plotLeft;
  const plotH = plotBottom - plotTop;
  const band = n > 0 ? plotW / n : 0;
  const xCenter = (i) => plotLeft + (i + 0.5) * band;

  // Build per-axis linear scales from the series bound to that yAxisId.
  const buildAxis = (axisSeries, fromZero, tickCount, domain) => {
    if (axisSeries.length === 0) return null;
    const values = data
      .map((row) => row[axisSeries[0].props.dataKey])
      .filter((v) => Number.isFinite(v));
    if (values.length === 0) return null;
    const min = Math.min(...values);
    const max = Math.max(...values);
    let domainMin;
    let domainMax;
    if (domain) {
      domainMin = domain[0];
      domainMax = domain[1];
    } else if (fromZero) {
      domainMin = 0;
      domainMax = max * 1.12;
    } else {
      const span = max - min || Math.max(Math.abs(max) * 0.05, 0.1);
      const pad = span * 0.16;
      domainMin = min - pad;
      domainMax = max + pad;
    }
    const ticks = niceTicks(domainMin, domainMax, tickCount);
    const lo = ticks[0];
    const hi = ticks[ticks.length - 1];
    const scale = (v) => plotBottom - ((v - lo) / (hi - lo)) * plotH;
    return { scale, ticks, lo, hi, domainMin, domainMax };
  };

  const leftSeries = series.filter(
    (s) => (s.props.yAxisId || "left") === "left",
  );
  const rightSeries = series.filter((s) => s.props.yAxisId === "right");
  const leftYAxis =
    yAxisChildren.find((y) => (y.props.yAxisId || "left") === "left") || null;
  const rightYAxis =
    yAxisChildren.find((y) => y.props.yAxisId === "right") || null;
  // A from-zero scale is the default when a left axis holds bars (their natural
  // baseline), but an explicit domain ("domain" prop on the YAxis) wins and is used
  // for a single shared percentage axis such as PCA variance (0% → 100%).
  const leftAxis = buildAxis(
    leftSeries,
    leftYAxis ? leftYAxis.props.fromZero ?? true : true,
    (leftYAxis && leftYAxis.props.tickCount) || 4,
    (leftYAxis && leftYAxis.props.domain) || null,
  );
  const rightAxis = buildAxis(
    rightSeries,
    rightYAxis ? rightYAxis.props.fromZero ?? false : false,
    (rightYAxis && rightYAxis.props.tickCount) || 4,
    (rightYAxis && rightYAxis.props.domain) || null,
  );
  // A line is drawn against the axis it is bound to. Most charts put bars on
  // the left (from-zero) axis and the line on the right (padded) axis, but a
  // single-shared-percentage-axis chart binds both bar and line to "left".
  const leftLine = leftSeries.find((s) => s.type === Line) || null;
  const rightLine = rightSeries.find((s) => s.type === Line) || null;

  // Human label for a data row ("PC3", "K = 3", …) used in titles and tooltips.
  const rowLabel = (row, i) =>
    row.label ||
    (row.kNumber != null
      ? `K = ${row.kNumber}`
      : `${row[xDataKey] ?? i + 1}`);

  const leftTickFmt =
    leftYAxis && typeof leftYAxis.props.tickFormat === "function"
      ? leftYAxis.props.tickFormat
      : formatTick;
  const rightTickFmt =
    rightYAxis && typeof rightYAxis.props.tickFormat === "function"
      ? rightYAxis.props.tickFormat
      : formatTick;

  // Minimum x-label gap; keeps PC1/PC14 readable while thinning middle labels.
  const MIN_X_GAP = 30;

  const showPlot = width > 0 && height > 0 && plotW > 20 && plotH > 20;

  const indexAt = (x) => {
    if (!showPlot || n === 0) return 0;
    return clamp(Math.floor((x - plotLeft) / band), 0, n - 1);
  };

  const handlePointerMove = (e) => {
    if (pinnedRef.current) return;
    const rect = containerRef.current.getBoundingClientRect();
    const x = e.clientX - rect.left;
    setPointer({ x, y: e.clientY - rect.top });
    setActive(indexAt(x));
  };

  const handlePointerLeave = () => {
    if (pinnedRef.current) return;
    setActive(null);
    setPointer(null);
  };

  const handleClick = (e) => {
    if (!showPlot) return;
    const rect = containerRef.current.getBoundingClientRect();
    const x = e.clientX - rect.left;
    const y = e.clientY - rect.top;
    const index = indexAt(x);
    setPointer({ x, y });
    setActive(index);
    setPin(true); // a tap keeps the reading visible on touch screens
  };

  const handleKeyDown = (e) => {
    if (!showPlot || n === 0) return;
    if (!["ArrowLeft", "ArrowRight", "Home", "End", "Escape"].includes(e.key)) {
      return;
    }
    e.preventDefault();
    const current = active == null ? 0 : active;
    let next = current;
    if (e.key === "ArrowRight") next = Math.min(n - 1, current + 1);
    else if (e.key === "ArrowLeft") next = Math.max(0, current - 1);
    else if (e.key === "Home") next = 0;
    else if (e.key === "End") next = n - 1;
    else {
      setActive(null);
      setPointer(null);
      setPin(false);
      return;
    }
    setActive(next);
    setPin(true);
    setPointer({ x: xCenter(next), y: plotTop + plotH / 2 });
  };

  const handleBlur = () => {
    setActive(null);
    setPointer(null);
    setPin(false);
  };

  // ---- derived series rendering config -----------------------------------

  const bars = leftSeries
    .filter((s) => s.type === SeriesBar)
    .map((s) => ({
      ...s.props,
      dataKey: s.props.dataKey,
      isBarSeries: true,
      axis: leftAxis,
    }))
    .filter((s) => s.axis && s.dataKey in (data[0] || {}));
  const line = leftLine
    ? {
        ...leftLine.props,
        dataKey: leftLine.props.dataKey,
        axis: leftAxis,
      }
    : rightLine
      ? {
          ...rightLine.props,
          dataKey: rightLine.props.dataKey,
          axis: rightAxis,
        }
      : null;

  const formatSeriesValue = (conf) => (value) =>
    typeof conf.format === "function" ? conf.format(value) : Number(value).toFixed(2);

  const barsDimmedByLegend = seriesDim === "second" ? 0.28 : 1;
  const lineDimmedByLegend = seriesDim === "first" ? 0.35 : 1;

  const baselineY = leftAxis ? leftAxis.scale(leftAxis.lo) : plotBottom;
  const barWidth = (s) =>
    clamp(band * 0.6, 6, s.maxBarSize || maxBarSize);

  const roundedTopBar = (x, y, w, h, r) => {
    if (!(h > 0)) return "";
    const rr = Math.min(r, w / 2, h);
    return (
      `M${x} ${baselineY} L${x} ${y + rr} ` +
      `Q${x} ${y} ${x + rr} ${y} ` +
      `L${x + w - rr} ${y} Q${x + w} ${y} ${x + w} ${y + rr} ` +
      `L${x + w} ${baselineY} Z`
    );
  };

  const currentRow = active == null ? null : data[active];

  // Tooltip position: follow pointer, else anchor to the active band center.
  const tooltipWidth = 168;
  const tooltipHeight = 78;
  const anchorX = pointer ? pointer.x : currentRow ? xCenter(active) : 0;
  const anchorY = pointer ? pointer.y : currentRow ? plotTop + plotH / 2 : 0;
  const tipX = clamp(anchorX - tooltipWidth / 2, 6, Math.max(6, width - tooltipWidth - 6));
  const tipY = clamp(anchorY - 10, 8, Math.max(8, height - tooltipHeight - 8));

  if (!showPlot) {
    return (
      <div
        ref={containerRef}
        className="composed-chart"
        role="group"
        aria-label={ariaLabel}
        tabIndex={0}
        style={{ position: "relative", width: "100%", height: "100%", minWidth: 0 }}
      />
    );
  }

  const activeTitle = currentRow ? rowLabel(currentRow, active) : "";

  return (
    <div
      ref={containerRef}
      className="composed-chart"
      role="group"
      aria-label={ariaLabel}
      tabIndex={0}
      style={{ position: "relative", width: "100%", height: "100%", minWidth: 0 }}
      onPointerMove={handlePointerMove}
      onPointerLeave={handlePointerLeave}
      onClick={handleClick}
      onKeyDown={handleKeyDown}
      onBlur={handleBlur}
    >
      <svg width={width} height={height} className="composed-chart-svg">
        {/* faint band behind the selected K (K=3) */}
        {selectedIndex != null && (
          <rect
            x={xCenter(selectedIndex) - band / 2}
            y={plotTop}
            width={band}
            height={plotH}
            style={{ fill: "var(--cyan)" }}
            opacity={0.045}
            pointerEvents="none"
          />
        )}

        {/* horizontal grid + baseline */}
        {gridChild && leftAxis
          ? leftAxis.ticks.map((tick) => {
              const gy = leftAxis.scale(tick);
              const isBaseline = Math.abs(tick) < 1e-9 && leftAxis.lo === 0;
              return (
                <line
                  key={tick}
                  x1={plotLeft}
                  x2={plotRight}
                  y1={gy}
                  y2={gy}
                  style={{ stroke: "var(--line)" }}
                  opacity={isBaseline ? 0.9 : 0.55}
                  strokeWidth={1}
                />
              );
            })
          : null}

        {/* bars */}
        {bars.flatMap((s) =>
          data.map((row, i) => {
            const value = row[s.dataKey];
            if (!Number.isFinite(value)) return null;
            const y = leftAxis.scale(value);
            const h = baselineY - y;
            const w = barWidth(s);
            const x = xCenter(i) - w / 2;
            const isSelected = i === selectedIndex;
            const isActive = active === i;
            const hoverOpacity = active == null || isActive ? 1 : s.fadedOpacity ?? 0.3;
            const opacity = barsDimmedByLegend * hoverOpacity;
            return (
              <path
                key={`${s.dataKey}-${i}`}
                className="cc-fade"
                d={roundedTopBar(x, y, w, h, s.radius || 0)}
                style={{ fill: isSelected ? s.selectedFill || s.fill : s.fill }}
                opacity={opacity}
                pointerEvents="none"
              >
                <title>{`${rowLabel(row, i)}, ${s.label || s.dataKey}: ${formatSeriesValue(s)(value)}`}</title>
              </path>
            );
          }),
        )}

        {/* line + points */}
        {line && line.axis && (
          <g opacity={lineDimmedByLegend}>
            <path
              className="cc-fade"
              d={
                line.curve
                  ? line.curve(
                      data.map((row, i) => ({
                        x: xCenter(i),
                        y: line.axis.scale(row[line.dataKey]),
                      })),
                    )
                  : ""
              }
              fill="none"
              style={{ stroke: line.stroke }}
              strokeWidth={line.strokeWidth ?? 2.25}
              strokeLinejoin="round"
              strokeLinecap="round"
              pointerEvents="none"
            />
            {data.map((row, i) => {
              const cx = xCenter(i);
              const cy = line.axis.scale(row[line.dataKey]);
              const isActive = active === i;
              return (
                <g key={`${line.dataKey}-pt-${i}`} className="cc-fade" opacity={active == null || isActive ? 1 : 0.6}>
                  {isActive && (
                    <circle
                      cx={cx}
                      cy={cy}
                      r={8}
                      style={{ fill: line.stroke }}
                      opacity={0.22}
                      pointerEvents="none"
                    />
                  )}
                  <circle
                    cx={cx}
                    cy={cy}
                    r={isActive ? 4 : 2.2}
                    style={{ fill: line.stroke }}
                    pointerEvents="none"
                  >
                    <title>{`${rowLabel(row, i)}, ${line.label || line.dataKey}: ${formatSeriesValue(line)(row[line.dataKey])}`}</title>
                  </circle>
                </g>
              );
            })}
          </g>
        )}

        {/* left axis */}
        {leftAxis && (
          <g>
            {leftAxis.ticks.map((tick) => {
              const gy = leftAxis.scale(tick);
              const isBaseline = Math.abs(tick) < 1e-9 && leftAxis.lo === 0;
              return (
                <g key={`lt-${tick}`}>
                  <line
                    x1={plotLeft - 5}
                    x2={plotLeft}
                    y1={gy}
                    y2={gy}
                    style={{ stroke: "var(--muted)" }}
                    opacity={0.35}
                  />
                  <text
                    x={plotLeft - 8}
                    y={gy + 3}
                    textAnchor="end"
                    style={{ fill: isBaseline ? "var(--text)" : "var(--muted)" }}
                    fontSize={9.5}
                    fontFamily='"IBM Plex Mono", ui-monospace, monospace'
                  >
                    {leftTickFmt(tick)}
                  </text>
                </g>
              );
            })}
            {yAxisChildren
              .filter((y) => (y.props.yAxisId || "left") === "left")
              .map((y) => (
                <text
                  key="left-title"
                  x={margin.left * 0.45}
                  y={plotTop + plotH / 2}
                  transform={`rotate(-90 ${margin.left * 0.45} ${plotTop + plotH / 2})`}
                  textAnchor="middle"
                  style={{ fill: "var(--muted)", textTransform: "uppercase" }}
                  fontSize={9}
                  letterSpacing="0.06em"
                >
                  {y.props.label || ""}
                </text>
              ))}
          </g>
        )}

        {/* right axis */}
        {rightAxis && (
          <g>
            {rightAxis.ticks.map((tick) => {
              const gy = rightAxis.scale(tick);
              return (
                <g key={`rt-${tick}`}>
                  <line
                    x1={plotRight}
                    x2={plotRight + 5}
                    y1={gy}
                    y2={gy}
                    style={{ stroke: "var(--muted)" }}
                    opacity={0.35}
                  />
                  <text
                    x={plotRight + 8}
                    y={gy + 3}
                    textAnchor="start"
                    style={{ fill: "var(--muted)" }}
                    fontSize={9.5}
                    fontFamily='"IBM Plex Mono", ui-monospace, monospace'
                  >
                    {rightTickFmt(tick)}
                  </text>
                </g>
              );
            })}
            {yAxisChildren
              .filter((y) => y.props.yAxisId === "right")
              .map((y) => (
                <text
                  key="right-title"
                  x={width - margin.right * 0.45}
                  y={plotTop + plotH / 2}
                  transform={`rotate(90 ${width - margin.right * 0.45} ${plotTop + plotH / 2})`}
                  textAnchor="middle"
                  style={{ fill: "var(--muted)", textTransform: "uppercase" }}
                  fontSize={9}
                  letterSpacing="0.06em"
                >
                  {y.props.label || ""}
                </text>
              ))}
          </g>
        )}

        {/* x axis labels. Horizontal labels thin the crowded middles; a
            tickRotation (e.g. -90 for vertical) gives every label a tiny
            horizontal footprint, so instead each tick is labelled without any clash. */}
        <g>
          {(() => {
            const rotation =
              typeof xAxisChild?.props.tickRotation === "number"
                ? xAxisChild.props.tickRotation
                : 0;
            let prevX = -Infinity;
            return data.map((row, i) => {
              const x = xCenter(i);
              const first = i === 0;
              const last = i === n - 1;
              if (rotation === 0 && !first && !last && x - prevX < MIN_X_GAP) return null;
              if (!last) prevX = x;
              const isSelected = i === selectedIndex;
              const y = plotBottom + 16;
              return (
                <text
                  key={`x-${i}`}
                  x={x}
                  y={y}
                  textAnchor="middle"
                  transform={rotation ? `rotate(${rotation} ${x} ${y})` : undefined}
                  style={{ fill: isSelected ? "var(--cyan)" : "var(--muted)" }}
                  fontSize={9.5}
                  fontFamily='"IBM Plex Mono", ui-monospace, monospace'
                  fontWeight={isSelected ? 700 : 400}
                >
                  {row[xDataKey] ?? i}
                </text>
              );
            });
          })()}
        </g>
      </svg>

      {/* tooltip */}
      {tooltipChild && active != null && currentRow && (
        <div className="k-tooltip" style={{ left: tipX, top: tipY }}>
          <p className="k-tooltip-title">{activeTitle}</p>
          {series.map((s) => {
            const isBar = s.type === SeriesBar;
            const color = isBar ? s.props.fill : s.props.stroke;
            const value = currentRow[s.props.dataKey];
            return (
              <div className="k-tooltip-row" key={s.props.dataKey}>
                <span
                  className="k-tooltip-marker"
                  style={{
                    background: color,
                    width: isBar ? 10 : 12,
                    height: isBar ? 10 : 3,
                    borderRadius: isBar ? 3 : 2,
                  }}
                />
                <span className="k-tooltip-label">{s.props.label || s.props.dataKey}</span>
                <span className="k-tooltip-value">
                  {typeof s.props.format === "function"
                    ? s.props.format(value)
                    : Number(value).toFixed(2)}
                </span>
              </div>
            );
          })}
        </div>
      )}

      <span className="visually-hidden" aria-live="polite">
        {pinned && activeTitle && currentRow
          ? `${activeTitle}: ${series
              .map((s) => {
                const value = currentRow[s.props.dataKey];
                const isBar = s.type === SeriesBar;
                return `${s.props.label || s.props.dataKey} ${
                  typeof s.props.format === "function"
                    ? s.props.format(value)
                    : Number(value).toFixed(2)
                }`;
              })
              .join(", ")}`
          : ""}
      </span>
    </div>
  );
}

export {
  ComposedChart,
  SeriesBar,
  Line,
  Grid,
  XAxis,
  YAxis,
  ChartTooltip,
  curveCatmullRom,
};
