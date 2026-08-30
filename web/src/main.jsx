import React from "react";
import { createRoot } from "react-dom/client";
import {
  BarElement,
  CategoryScale,
  Chart as ChartJS,
  Filler,
  Legend as ChartJSLegend,
  LineElement,
  LinearScale,
  PointElement,
  RadialLinearScale,
  Tooltip,
} from "chart.js";
import { Line } from "react-chartjs-2";
import { Legend, LegendItemComponent, LegendLabel, LegendMarker } from "./Legend";
import {
  ChartTooltip,
  ComposedChart,
  Grid,
  Line as ComposedLine,
  SeriesBar,
  XAxis,
  YAxis,
  curveCatmullRom,
} from "./ComposedChart";
import { RadarChart, RadarGrid, RadarAxis, RadarLabels, RadarArea } from "./RadarChart";
import "./styles.css";
import {
  clusters,
  clusterShapes,
  kMetrics,
  pcaComponents,
  populationShape,
  references,
  summaryStats,
} from "./analysisData";

ChartJS.register(
  BarElement,
  CategoryScale,
  Filler,
  ChartJSLegend,
  LineElement,
  LinearScale,
  PointElement,
  RadialLinearScale,
  Tooltip,
);

const hours = Array.from({ length: 24 }, (_, hour) => `${String(hour).padStart(2, "0")}:00`);

function chartDefaults() {
  return {
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
      legend: {
        labels: {
          color: "#dbe7ec",
          boxWidth: 12,
          boxHeight: 12,
          font: { family: "Inter", size: 12 },
        },
      },
      tooltip: {
        backgroundColor: "#101722",
        borderColor: "#2d3c4d",
        borderWidth: 1,
        titleColor: "#ffffff",
        bodyColor: "#dbe7ec",
      },
    },
    scales: {
      x: {
        grid: { color: "rgba(141, 163, 176, 0.12)" },
        ticks: { color: "#94a8b4", maxRotation: 0, autoSkip: true, maxTicksLimit: 8 },
      },
      y: {
        grid: { color: "rgba(141, 163, 176, 0.12)" },
        ticks: { color: "#94a8b4" },
      },
    },
  };
}

function LoadShapeChart() {
  const data = {
    labels: hours,
    datasets: [
      {
        label: "Population average",
        data: populationShape,
        borderColor: "#71808d",
        backgroundColor: "transparent",
        borderDash: [5, 5],
        pointRadius: 0,
        tension: 0.42,
      },
      ...clusters.map((cluster) => ({
        label: cluster.name,
        data: clusterShapes[cluster.id],
        borderColor: cluster.color,
        backgroundColor: `${cluster.color}22`,
        pointRadius: 0,
        tension: 0.42,
        fill: true,
      })),
    ],
  };

  return <Line data={data} options={chartDefaults()} />;
}

// Slides shown in the "Average 24-hour load shape" carousel.
// Add more slides here and the arrows/dots update automatically.
const loadShapeSlides = [LoadShapeChart];

function LoadShapeCarousel({ tall = false }) {
  const [slide, setSlide] = React.useState(0);
  const count = loadShapeSlides.length;
  const goTo = (index) => setSlide((index + count) % count);

  const Slide = loadShapeSlides[slide];

  return (
    <div className="carousel" role="group" aria-roledescription="carousel" aria-label="Average 24-hour load shape visualizations">
      <button
        className="carousel-arrow prev"
        type="button"
        aria-label="Previous visualization"
        onClick={() => goTo(slide - 1)}
      >
        <svg viewBox="0 0 24 24" aria-hidden="true">
          <path d="M15 5l-7 7 7 7" />
        </svg>
      </button>
      <div className="carousel-stage">
        <div className={`chart-container${tall ? " tall" : ""}`}>
          <Slide />
        </div>
        <div className="carousel-dots">
          {loadShapeSlides.map((_, index) => (
            <button
              key={index}
              className={`carousel-dot${index === slide ? " active" : ""}`}
              type="button"
              aria-label={`Go to slide ${index + 1}`}
              aria-current={index === slide ? "true" : undefined}
              onClick={() => goTo(index)}
            />
          ))}
        </div>
      </div>
      <button
        className="carousel-arrow next"
        type="button"
        aria-label="Next visualization"
        onClick={() => goTo(slide + 1)}
      >
        <svg viewBox="0 0 24 24" aria-hidden="true">
          <path d="M9 5l7 7-7 7" />
        </svg>
      </button>
    </div>
  );
}

function usePrefersReducedMotion() {
  const [reduced, setReduced] = React.useState(
    () => window.matchMedia("(prefers-reduced-motion: reduce)").matches,
  );
  React.useEffect(() => {
    const mq = window.matchMedia("(prefers-reduced-motion: reduce)");
    const onChange = () => setReduced(mq.matches);
    mq.addEventListener("change", onChange);
    return () => mq.removeEventListener("change", onChange);
  }, []);
  return reduced;
}

function hourLabel(value) {
  const hour = ((Math.round(value) % 24) + 24) % 24;
  return `${String(hour).padStart(2, "0")}:00`;
}

// The same four committed series used by the load-shape chart. dimmed is the
// overview strip variant: same curves, quieter styling. Values are untouched.
function buildLoadSeries(dimmed) {
  return [
    {
      label: "Population average",
      // A linear x-axis needs explicit {x, y} points (x = hour index). A flat
      // number array would only map to an x position on a category scale and
      // would render blank here.
      data: populationShape.map((y, i) => ({ x: i, y })),
      borderColor: "#71808d",
      borderDash: dimmed ? [4, 3] : [7, 4],
      borderWidth: dimmed ? 1.1 : 2.2,
      pointRadius: 0,
      tension: 0.42,
      fill: false,
    },
    ...clusters.map((cluster) => ({
      label: cluster.name,
      data: clusterShapes[cluster.id].map((y, i) => ({ x: i, y })),
      borderColor: cluster.color,
      backgroundColor: dimmed ? "transparent" : `${cluster.color}1c`,
      borderWidth: dimmed ? 1.1 : 2,
      pointRadius: 0,
      tension: 0.42,
      fill: !dimmed,
    })),
  ];
}

function hexToRgba(hex, alpha) {
  const value = hex.replace("#", "");
  const n = parseInt(value, 16);
  const r = (n >> 16) & 255;
  const g = (n >> 8) & 255;
  const b = n & 255;
  return `rgba(${r}, ${g}, ${b}, ${alpha})`;
}

// Four entries for the composable legend, in the same order as the datasets
// (0 = population, then the three archetypes in cluster order) so indices line
// up. Only the presentation is described here; values come from the data files.
const legendItems = [
  { key: "population", label: "Population average", color: "#71808d", dashed: true },
  ...clusters.map((cluster) => ({
    key: String(cluster.id),
    label: cluster.name,
    color: cluster.color,
    dashed: false,
  })),
];

// Emphasis applied when a legend item is hovered/focused: the selected series
// gets a heavier line, the rest are thinned and faded. Scientific values are
// untouched — only stroke weight/fill presentation changes.
function buildMainData(active) {
  const base = buildLoadSeries(false);
  if (active == null) return base;
  return base.map((dataset, index) => {
    if (index === active) {
      return { ...dataset, borderWidth: dataset.borderDash ? 2.8 : 2.5 };
    }
    return {
      ...dataset,
      borderWidth: 1.1,
      borderColor: hexToRgba(dataset.borderColor, 0.32),
      backgroundColor: "transparent",
      fill: false,
    };
  });
}

function axisTickDefaults() {
  return {
    color: "#94a8b4",
    font: { family: "Inter", size: 11 },
    padding: 6,
  };
}

function hourXScale(min, max) {
  return {
    type: "linear",
    min,
    max,
    border: { display: false },
    grid: { color: "rgba(141, 163, 176, 0.12)" },
    ticks: {
      ...axisTickDefaults(),
      precision: 0,
      autoSkip: true,
      maxTicksLimit: 8,
      callback: (value) => hourLabel(value),
    },
  };
}

function makeBrushMainOptions(selection, animate, setChartHover) {
  return {
    responsive: true,
    maintainAspectRatio: false,
    interaction: { mode: "index", intersect: false },
    animation: animate ? { duration: 220, easing: "easeOutQuart" } : false,
    onHover: (event, elements) => {
      // Reflect the chart crosshair in the legend: highlight the top series at
      // the hovered hour, and clear once the pointer leaves the data area.
      if (!Array.isArray(elements) || elements.length === 0) {
        setChartHover(null);
        return;
      }
      const top = elements.reduce(
        (acc, item) => (item && item.element && item.element.y > acc.element.y ? item : acc),
        elements[0],
      );
      setChartHover(top ? top.datasetIndex : null);
    },
    plugins: {
      // The composable Legend renders the series; hide Chart.js's own legend.
      legend: { display: false },
      tooltip: {
        backgroundColor: "rgba(16, 23, 34, 0.96)",
        borderColor: "#2d3c4d",
        borderWidth: 1,
        titleColor: "#ffffff",
        bodyColor: "#dbe7ec",
        titleFont: { family: "Inter", size: 12, weight: "700" },
        bodyFont: { family: "Inter", size: 12 },
        padding: 10,
        cornerRadius: 6,
        boxPadding: 4,
        usePointStyle: true,
        // Flat All-Day is a real series in this dataset. Keep it (and every
        // other series) in the crosshair listing instead of letting a default
        // interaction filter drop a row at any hour.
        filter: () => true,
        callbacks: {
          title: (items) => {
            const value = items[0]?.parsed?.x;
            return value == null ? "" : hourLabel(value);
          },
          label: (ctx) => ` ${ctx.dataset.label}: ${Number(ctx.parsed.y).toFixed(4)}`,
        },
      },
    },
    scales: {
      x: hourXScale(selection[0], selection[1]),
      y: {
        border: { display: false },
        grid: { color: "rgba(141, 163, 176, 0.12)" },
        ticks: { ...axisTickDefaults(), maxTicksLimit: 5 },
      },
    },
  };
}

const brushStripOptions = {
  responsive: true,
  maintainAspectRatio: false,
  animation: false,
  plugins: { legend: { display: false }, tooltip: { enabled: false } },
  scales: {
    x: {
      type: "linear",
      min: 0,
      max: 23,
      border: { display: false },
      grid: { display: false },
      ticks: { display: false },
    },
    y: {
      display: false,
      border: { display: false },
      grid: { display: false },
      ticks: { display: false },
    },
  },
};

const BRUSH_MIN_WIDTH = 2;

function LoadShapeBrushChart() {
  const reduced = usePrefersReducedMotion();
  const [selection, setSelection] = React.useState([0, 23]);
  const [interacting, setInteracting] = React.useState(false);
  const [hover, setHover] = React.useState("default");
  const [geometry, setGeometry] = React.useState({ left: 0, right: 0 });
  // legendActive = which legend row is highlighted (driven by the legend and by
  // the chart crosshair). emphasized = which series the chart thickens (driven
  // only by an explicit legend hover/focus, so the crosshair doesn't re-thin
  // the curves while you are still reading the tooltip).
  const [legendActive, setLegendActive] = React.useState(null);
  const [emphasized, setEmphasized] = React.useState(null);
  const handleLegendFocus = React.useCallback((index) => {
    setLegendActive(index);
    setEmphasized(index);
  }, []);

  const wrapRef = React.useRef(null);
  const stripChartRef = React.useRef(null);
  const dragRef = React.useRef(null);

  const stripData = React.useMemo(() => ({ datasets: buildLoadSeries(true) }), []);
  const mainData = React.useMemo(() => ({ datasets: buildMainData(emphasized) }), [emphasized]);
  // Pause the gentle series animation while an explicit legend hover is going
  // on so the emphasise/thin switch feels immediate rather than animated.
  const animate = !reduced && !interacting && emphasized == null;
  const mainOptions = React.useMemo(
    () => makeBrushMainOptions(selection, animate, setLegendActive),
    [selection, reduced, interacting, animate],
  );

  const isFull = selection[0] <= 0 && selection[1] >= 23;

  // The strip has no visible axes, so its plot area fills the container
  // exactly: hour 0 maps to x=0 and hour 23 to the container's full width.
  // We keep geometry in state only so the overlay re-positions on resize.
  const readGeometry = () => {
    const rect = wrapRef.current?.getBoundingClientRect();
    if (!rect || rect.width < 10) return null;
    return { left: 0, right: rect.width };
  };

  React.useEffect(() => {
    const update = () => {
      const g = readGeometry();
      if (g) {
        setGeometry((prev) => (prev.left === g.left && prev.right === g.right ? prev : g));
      }
    };
    update();
    const ro =
      typeof ResizeObserver !== "undefined" && wrapRef.current
        ? new ResizeObserver(update)
        : null;
    if (ro) ro.observe(wrapRef.current);
    window.addEventListener("resize", update);
    return () => {
      if (ro) ro.disconnect();
      window.removeEventListener("resize", update);
    };
  }, []);

  const valueFromClientX = (clientX) => {
    const rect = wrapRef.current?.getBoundingClientRect();
    if (!rect || rect.width < 10) return null;
    const px = clientX - rect.left;
    return Math.max(0, Math.min(23, (px / rect.width) * 23));
  };

  // Drag tracking runs on window-level listeners so the gesture keeps working
  // even if the pointer leaves the small strip during a drag.
  const dragMoveRef = React.useRef(null);
  const dragUpRef = React.useRef(null);
  React.useEffect(
    () => () => {
      if (dragMoveRef.current) window.removeEventListener("pointermove", dragMoveRef.current);
      if (dragUpRef.current) window.removeEventListener("pointerup", dragUpRef.current);
      if (dragUpRef.current) window.removeEventListener("pointercancel", dragUpRef.current);
    },
    [],
  );

  const onPointerDown = (event) => {
    if (event.pointerType === "mouse" && event.button !== 0) return; // left button only
    const value = valueFromClientX(event.clientX);
    const rect = wrapRef.current?.getBoundingClientRect();
    if (value == null || !rect || rect.width < 10) return;
    const px = event.clientX - rect.left;
    const width = rect.width;
    const [s0, s1] = selection;
    const pxStart = (s0 / 23) * width;
    const pxEnd = (s1 / 23) * width;
    const full = s0 <= 0 && s1 >= 23;
    let mode = "draw";
    if (px <= pxStart + 8) mode = "resizeL";
    else if (px >= pxEnd - 8) mode = "resizeR";
    // Moving is only meaningful when the window has room to slide. At full
    // range the whole strip is "inside" the window, so fall through to draw
    // and let a drag start a fresh, smaller window instead of doing nothing.
    else if (!full && px > pxStart + 2 && px < pxEnd - 2) mode = "move";
    dragRef.current = { mode, startValue: value, startSel: [s0, s1], moved: false };

    dragMoveRef.current = (ev) => {
      const drag = dragRef.current;
      if (!drag) return;
      const v = valueFromClientX(ev.clientX);
      if (v == null) return;
      if (Math.abs(v - drag.startValue) > 0.02) drag.moved = true;
      let next;
      if (drag.mode === "resizeL") {
        next = [Math.min(v, drag.startSel[1] - BRUSH_MIN_WIDTH), drag.startSel[1]];
      } else if (drag.mode === "resizeR") {
        next = [drag.startSel[0], Math.max(v, drag.startSel[0] + BRUSH_MIN_WIDTH)];
      } else if (drag.mode === "move") {
        const w = drag.startSel[1] - drag.startSel[0];
        const start = Math.max(0, Math.min(23 - w, drag.startSel[0] + (v - drag.startValue)));
        next = [start, start + w];
      } else {
        let a = Math.min(drag.startValue, v);
        let b = Math.max(drag.startValue, v);
        if (b - a < BRUSH_MIN_WIDTH) {
          const anchor = Math.max(0, Math.min(23 - BRUSH_MIN_WIDTH, drag.startValue));
          a = anchor;
          b = anchor + BRUSH_MIN_WIDTH;
        }
        next = [a, b];
      }
      setSelection(next);
    };

    dragUpRef.current = () => {
      const drag = dragRef.current;
      dragRef.current = null;
      if (dragMoveRef.current) window.removeEventListener("pointermove", dragMoveRef.current);
      if (dragUpRef.current) window.removeEventListener("pointerup", dragUpRef.current);
      if (dragUpRef.current) window.removeEventListener("pointercancel", dragUpRef.current);
      // A plain tap on the strip (no drag) returns to the full 24-hour view.
      if (drag && drag.mode === "draw" && !drag.moved) setSelection([0, 23]);
      setInteracting(false);
    };

    window.addEventListener("pointermove", dragMoveRef.current);
    window.addEventListener("pointerup", dragUpRef.current);
    window.addEventListener("pointercancel", dragUpRef.current);
    setInteracting(true);
    try {
      if (wrapRef.current.setPointerCapture) wrapRef.current.setPointerCapture(event.pointerId);
    } catch {
      /* capture is optional; window listeners still track the drag */
    }
    event.preventDefault();
  };

  const onPointerLeave = () => {
    if (!dragRef.current) setHover("default");
  };

  const onHoverMove = (event) => {
    if (dragRef.current) return;
    const rect = wrapRef.current?.getBoundingClientRect();
    if (!rect || rect.width < 10) return;
    const px = event.clientX - rect.left;
    const width = rect.width;
    const [s0, s1] = selection;
    const pxStart = (s0 / 23) * width;
    const pxEnd = (s1 / 23) * width;
    if (px <= pxStart + 8) setHover("left");
    else if (px >= pxEnd - 8) setHover("right");
    else if (px > pxStart && px < pxEnd) setHover("window");
    else setHover("track");
  };

  // Keyboard alternative to dragging (WCAG 2.2: not drag-only).
  const onKeyDown = (event) => {
    let [start, end] = selection;
    const width = end - start;
    switch (event.key) {
      case "ArrowLeft":
        event.preventDefault();
        if (event.shiftKey) {
          start = Math.max(0, start - 1);
        } else {
          start = Math.max(0, start - 1);
          end = start + width;
        }
        break;
      case "ArrowRight":
        event.preventDefault();
        if (event.shiftKey) {
          end = Math.min(23, end + 1);
        } else {
          end = Math.min(23, end + 1);
          start = end - width;
        }
        break;
      case "Home":
        event.preventDefault();
        setSelection([0, 23]);
        return;
      default:
        return;
    }
    setSelection([start, end]);
  };

  const span = geometry.right - geometry.left;
  const pxStart = span > 0 ? geometry.left + (selection[0] / 23) * span : 0;
  const pxWidth = span > 0 ? geometry.left + (selection[1] / 23) * span - pxStart : 0;

  const cursor =
    hover === "left" || hover === "right"
      ? "ew-resize"
      : hover === "window"
        ? interacting
          ? "grabbing"
          : "grab"
        : "default";

  return (
    <div className="load-chart">
      <Legend hoveredIndex={legendActive} onHoverChange={handleLegendFocus}>
        {legendItems.map((item) => (
          <LegendItemComponent key={item.key} label={item.label}>
            <LegendMarker color={item.color} dashed={item.dashed} />
            <LegendLabel>{item.label}</LegendLabel>
          </LegendItemComponent>
        ))}
      </Legend>
      <div className="load-chart-main">
        <Line data={mainData} options={mainOptions} />
      </div>
      <div
        ref={wrapRef}
        className="load-chart-brush"
        role="group"
        aria-label="Time range brush. Drag the window to move it, drag its edges to resize it, or drag across the strip to draw a new window."
        style={{ cursor }}
        onPointerDown={onPointerDown}
        onPointerMove={onHoverMove}
        onPointerLeave={onPointerLeave}
        onDoubleClick={() => setSelection([0, 23])}
      >
        <Line ref={stripChartRef} data={stripData} options={brushStripOptions} />
        {span > 0 && pxWidth > 0 && (
          <div
            className="brush-window"
            style={{ left: pxStart, width: pxWidth }}
            role="slider"
            tabIndex={0}
            aria-label="Selected time window"
            aria-valuemin={0}
            aria-valuemax={23}
            aria-valuenow={Math.round(selection[0])}
            aria-valuetext={`${hourLabel(selection[0])} to ${hourLabel(selection[1])}`}
            aria-describedby="brush-help"
            onKeyDown={onKeyDown}
          >
            <div className="brush-handle left" aria-hidden="true" />
            <div className="brush-handle right" aria-hidden="true" />
          </div>
        )}
      </div>
      <div className="load-chart-footer" id="brush-help">
        <span className="brush-hint">
          {isFull
            ? "Drag across the strip to zoom into a time window. Double-click or press Home to reset."
            : `Showing ${hourLabel(selection[0])} – ${hourLabel(selection[1])}. Arrow keys move the window, Shift+arrows resize it.`}
        </span>
        {!isFull && (
          <button type="button" className="brush-reset" onClick={() => setSelection([0, 23])}>
            Reset to 24h
          </button>
        )}
      </div>
    </div>
  );
}

function KSelectionChart() {
  const rows = kMetrics.map((row) => ({
    k: `K=${row.k}`,
    kNumber: row.k,
    silhouette: row.silhouette,
    daviesBouldin: row.daviesBouldin,
  }));
  const selectedIndex = kMetrics.findIndex((row) => row.selected);
  const selectedK = kMetrics.find((row) => row.selected)?.k;
  const [legendSeries, setLegendSeries] = React.useState(null); // "first" | "second"

  return (
    <div className="chart-container">
      <div className="k-chart-inner">
        <div className="k-chart-top">
          <Legend
            hoveredIndex={legendSeries === "first" ? 0 : legendSeries === "second" ? 1 : null}
            onHoverChange={(i) => setLegendSeries(i === 0 ? "first" : i === 1 ? "second" : null)}
          >
            <LegendItemComponent label="Silhouette">
              <LegendMarker color="var(--cyan)" variant="bar" />
              <LegendLabel>Silhouette</LegendLabel>
            </LegendItemComponent>
            <LegendItemComponent label="Davies-Bouldin">
              <LegendMarker color="var(--amber)" />
              <LegendLabel>Davies-Bouldin</LegendLabel>
            </LegendItemComponent>
          </Legend>
          {selectedK != null && (
            <span className="k-selected-tag">Selected · K={selectedK}</span>
          )}
        </div>
        <ComposedChart
          data={rows}
          xDataKey="k"
          selectedIndex={selectedIndex}
          seriesDim={legendSeries}
          maxBarSize={26}
          ariaLabel="K-selection chart: Silhouette bars and Davies-Bouldin line from K=2 to K=10"
        >
          <Grid horizontal />
          <YAxis yAxisId="left" orientation="left" label="Silhouette" />
          <YAxis yAxisId="right" orientation="right" label="Davies-Bouldin" />
          <SeriesBar
            yAxisId="left"
            dataKey="silhouette"
            label="Silhouette"
            fill="var(--k-bar)"
            selectedFill="var(--cyan)"
            radius={4}
            maxBarSize={22}
            fadedOpacity={0.24}
            format={(v) => Number(v).toFixed(3)}
          />
          <ComposedLine
            yAxisId="right"
            dataKey="daviesBouldin"
            label="Davies-Bouldin"
            stroke="var(--amber)"
            strokeWidth={2.25}
            curve={curveCatmullRom.alpha(0.42)}
            format={(v) => Number(v).toFixed(3)}
          />
          <ChartTooltip showCrosshair={false} />
          <XAxis numTicks={9} />
        </ComposedChart>
      </div>
    </div>
  );
}

function PcaVarianceChart() {
  const rows = pcaComponents.map((row) => ({
    component: `PC${row.component}`,
    label: `PC${row.component}`,
    explainedVariance: row.explainedVariance,
    cumulativeVariance: row.cumulativeVariance,
  }));
  const [legendSeries, setLegendSeries] = React.useState(null); // "first" | "second"
  const pct = (v) => `${(v * 100).toFixed(1)}%`;
  return (
    <div className="chart-container">
      <div className="pca-chart-inner">
        <div className="pca-chart-top">
          <Legend
            hoveredIndex={legendSeries === "first" ? 0 : legendSeries === "second" ? 1 : null}
            onHoverChange={(i) => setLegendSeries(i === 0 ? "first" : i === 1 ? "second" : null)}
          >
            <LegendItemComponent label="Explained variance">
              <LegendMarker color="var(--blue)" variant="bar" />
              <LegendLabel>Explained variance</LegendLabel>
            </LegendItemComponent>
            <LegendItemComponent label="Cumulative variance">
              <LegendMarker color="var(--cyan)" />
              <LegendLabel>Cumulative variance</LegendLabel>
            </LegendItemComponent>
          </Legend>
        </div>
        <ComposedChart
          data={rows}
          xDataKey="component"
          seriesDim={legendSeries}
          maxBarSize={28}
          ariaLabel="PCA variance: explained variance bars and cumulative variance line from PC1 to PC14"
        >
          <Grid horizontal />
          <YAxis
            orientation="left"
            label="Variance (%)"
            domain={[0, 1]}
            tickCount={6}
            tickFormat={(v) => `${Math.round(v * 100)}%`}
          />
          <SeriesBar
            dataKey="explainedVariance"
            label="Explained variance"
            fill="var(--blue)"
            radius={3}
            maxBarSize={20}
            fadedOpacity={0.24}
            format={pct}
          />
          <ComposedLine
            dataKey="cumulativeVariance"
            label="Cumulative variance"
            stroke="var(--cyan)"
            strokeWidth={2.25}
            curve={curveCatmullRom.alpha(0.42)}
            format={pct}
          />
          <ChartTooltip showCrosshair={false} />
          <XAxis />
        </ComposedChart>
      </div>
    </div>
  );
}

// The six behavioural dimensions shared by every cluster profile.
const RADAR_METRICS = [
  { key: "morning", label: "Morning" },
  { key: "afternoon", label: "Afternoon" },
  { key: "evening", label: "Evening" },
  { key: "night", label: "Night" },
  { key: "baseLoad", label: "Base Load" },
  { key: "variation", label: "Variation" },
];

// Established archetype colour identity, bound to the app theme tokens.
const ARCHETYPE_COLOR = {
  "Midday-Peaking": "var(--amber)",
  "Flat All-Day": "var(--cyan)",
  "Evening-Peaking": "var(--violet)",
};

function ClusterRadarChart() {
  // Map the committed analysis values into the radar's 0-100 scale. This happens
  // only at the visualization boundary; the stored cluster data is untouched.
  const radarData = clusters.map((cluster) => {
    const values = {
      morning: cluster.morningShare * 100,
      afternoon: cluster.afternoonShare * 100,
      evening: cluster.eveningShare * 100,
      night: cluster.nightShare * 100,
      baseLoad: cluster.baseLoadShare * 100,
      variation: cluster.coefficientOfVariation * 100,
    };
    return {
      label: cluster.name,
      color: ARCHETYPE_COLOR[cluster.name] || cluster.color,
      values,
    };
  });
  const [legendHover, setLegendHover] = React.useState(null);
  return (
    <div className="radar-chart-inner">
      <div className="radar-chart-top">
        <Legend hoveredIndex={legendHover} onHoverChange={setLegendHover}>
          {radarData.map((d) => (
            <LegendItemComponent key={d.label} label={d.label}>
              <LegendMarker color={d.color} variant="bar" />
              <LegendLabel>{d.label}</LegendLabel>
            </LegendItemComponent>
          ))}
        </Legend>
      </div>
      <RadarChart
        data={radarData}
        metrics={RADAR_METRICS}
        levels={5}
        animate
        seriesDim={legendHover}
        ariaLabel="Cluster profile comparison: three household archetypes across six load-shape dimensions"
      >
        <RadarGrid />
        <RadarAxis />
        <RadarLabels />
        {radarData.map((d, i) => (
          <RadarArea key={d.label} index={i} />
        ))}
      </RadarChart>
    </div>
  );
}

function StatCard({ label, value, note }) {
  return (
    <div className="stat-card">
      <span>{label}</span>
      <strong>{value}</strong>
      {note ? <small>{note}</small> : null}
    </div>
  );
}

function SectionHeader({ eyebrow, title, children }) {
  return (
    <div className="section-header">
      <span className="eyebrow">{eyebrow}</span>
      <h2>{title}</h2>
      {children ? <p>{children}</p> : null}
    </div>
  );
}

function App() {
  return (
    <div>
      <nav className="site-nav" aria-label="Main navigation">
        <a className="brand" href="#top">Load Shape Lab</a>
        <div className="nav-links">
          <a href="#about">About</a>
          <a href="#charts">Charts</a>
          <a href="#references">References</a>
          <a href="https://energy-consumption-pattern-vqrh.streamlit.app/" target="_blank" rel="noopener noreferrer">Simulator</a>
        </div>
      </nav>

      <header className="hero" id="top">
        <div className="hero-copy">
          <span className="eyebrow">PCA plus K-Means energy clustering</span>
          <h1>Energy use is a pattern, not just a number.</h1>
          <p>
            This project simulates household electricity readings, turns each day into a
            load shape, compresses the features with PCA, and uses K-Means to find daily
            rhythms that are easier to explain.
          </p>
          <div className="hero-actions">
            <a className="button primary" href="#charts">Explore the charts</a>
            <a className="button secondary" href="#about">What is this project about?</a>
          </div>
        </div>
        <div className="hero-panel chart-panel tall">
          <LoadShapeCarousel tall />
        </div>
      </header>

      <main>
        <section className="band" id="about">
          <SectionHeader eyebrow="What is this project about" title="A simple way to find daily energy rhythms">
            The analysis asks whether consumers can be grouped by when they use power. It
            uses synthetic data, so the result is a controlled demonstration of the method,
            not a claim about real households.
          </SectionHeader>
          <div className="stats-grid">
            <StatCard label="Records" value={summaryStats.records} note="hourly synthetic readings" />
            <StatCard label="Consumers" value={summaryStats.consumers} />
            <StatCard label="Features" value={summaryStats.features} note="behavioural shape descriptors" />
            <StatCard label="PCA components" value={summaryStats.pcaComponents} note="95.3% variance retained" />
            <StatCard label="Selected clusters" value={summaryStats.clusters} />
            <StatCard label="Silhouette" value={summaryStats.silhouette} note="modest but useful separation" />
          </div>
        </section>

        <section className="band" id="charts">
          <SectionHeader eyebrow="Chart.js dashboard" title="The matplotlib results, rebuilt for the web">
            The charts below use the committed analysis artifacts, including cluster load
            shapes, PCA variance, K-selection metrics, and cluster profiles.
          </SectionHeader>
          <div className="chart-grid">
            <article className="chart-panel wide">
              <div className="panel-heading">
                <h3>Average 24-hour load shape</h3>
                <p>Each curve is normalized so timing matters more than total consumption.</p>
              </div>
              <LoadShapeBrushChart />
            </article>
            <article className="chart-panel">
              <div className="panel-heading">
                <h3>K selection</h3>
                <p>K=3 balances separation with stable, non-tiny clusters.</p>
              </div>
              <KSelectionChart />
            </article>
            <article className="chart-panel">
              <div className="panel-heading">
                <h3>PCA Variance</h3>
                <p>Fourteen components keep just over 95% of the variation.</p>
              </div>
              <div className="chart-container">
                <PcaVarianceChart />
              </div>
            </article>
            <article className="chart-panel">
              <div className="panel-heading">
                <h3>Cluster Profile Comparison</h3>
                <p>Shares describe timing; variation describes how peaked the shape is.</p>
              </div>
              <div className="chart-container">
                <ClusterRadarChart />
              </div>
            </article>
          </div>
        </section>

        <section className="band">
          <SectionHeader eyebrow="Cluster stories" title="Three readable patterns">
            The names are intentionally plain. They describe the daily curve rather than
            implying anything about household identity.
          </SectionHeader>
          <div className="cluster-grid">
            {clusters.map((cluster) => (
              <article className="cluster-card" key={cluster.id} style={{ "--accent": cluster.color }}>
                <span className="cluster-index">Cluster {cluster.id}</span>
                <h3>{cluster.name}</h3>
                <p>{cluster.description}</p>
                <dl>
                  <div><dt>Consumers</dt><dd>{cluster.size}</dd></div>
                  <div><dt>Share</dt><dd>{Math.round(cluster.sizeShare * 1000) / 10}%</dd></div>
                  <div><dt>Peak</dt><dd>{String(cluster.peakHour).padStart(2, "0")}:00</dd></div>
                </dl>
              </article>
            ))}
          </div>
        </section>

        <section className="band references" id="references">
          <SectionHeader eyebrow="References" title="Research behind the method">
            These sources guided the feature engineering, PCA step, K-Means validation,
            and load-shape framing used in the project.
          </SectionHeader>
          <div className="reference-grid">
            {references.map((reference) => (
              <a 
                className="reference-card" 
                href={reference.url} 
                key={reference.title}
                target="_blank"
                rel="noopener noreferrer"
              >
                <div className="ref-corner"></div>
                <div className="ref-star">★</div>
                <div className="ref-title-area">
                  <strong>{reference.title}</strong>
                </div>
                <div className="ref-body">
                  <span>{reference.meta}</span>
                </div>
              </a>
            ))}
          </div>
        </section>

        <section className="band" style={{ textAlign: "center", paddingTop: "2rem", paddingBottom: "3rem" }}>
          <a href="https://github.com/shaxntanu/Energy-Consumption-Pattern-Analysis-using-PCA-and-K-Means" target="_blank" rel="noopener noreferrer" className="button github-footer-button">
            <svg height="24" aria-hidden="true" viewBox="0 0 16 16" version="1.1" width="24">
              <path fillRule="evenodd" d="M8 0C3.58 0 0 3.58 0 8c0 3.54 2.29 6.53 5.47 7.59.4.07.55-.17.55-.38 0-.19-.01-.82-.01-1.49-2.01.37-2.53-.49-2.69-.94-.09-.23-.48-.94-.82-1.13-.28-.15-.68-.52-.01-.53.63-.01 1.08.58 1.23.82.72 1.21 1.87.87 2.33.66.07-.52.28-.87.51-1.07-1.78-.2-3.64-.89-3.64-3.95 0-.87.31-1.59.82-2.15-.08-.2-.36-1.02.08-2.12 0 0 .67-.21 2.2.82.64-.18 1.32-.27 2-.27.68 0 1.36.09 2 .27 1.53-1.04 2.2-.82 2.2-.82.44 1.1.16 1.92.08 2.12.51.56.82 1.27.82 2.15 0 3.07-1.87 3.75-3.65 3.95.29.25.54.73.54 1.48 0 1.07-.01 1.93-.01 2.2 0 .21.15.46.55.38A8.013 8.013 0 0016 8c0-4.42-3.58-8-8-8z"></path>
            </svg>
            <span className="text">View on GitHub</span>
          </a>
        </section>
      </main>
    </div>
  );
}

createRoot(document.getElementById("root")).render(<App />);
