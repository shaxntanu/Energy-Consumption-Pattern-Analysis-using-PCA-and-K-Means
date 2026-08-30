import React from "react";
import { createRoot } from "react-dom/client";
import {
  BarElement,
  CategoryScale,
  Chart as ChartJS,
  Filler,
  Legend,
  LineElement,
  LinearScale,
  PointElement,
  RadialLinearScale,
  Tooltip,
} from "chart.js";
import { Bar, Line, Radar } from "react-chartjs-2";
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
  Legend,
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

function makeBrushMainOptions(selection, animate) {
  return {
    responsive: true,
    maintainAspectRatio: false,
    interaction: { mode: "index", intersect: false },
    animation: animate ? { duration: 220, easing: "easeOutQuart" } : false,
    plugins: {
      legend: {
        position: "top",
        align: "start",
        labels: {
          color: "#dbe7ec",
          usePointStyle: true,
          pointStyle: "line",
          boxWidth: 16,
          boxHeight: 6,
          font: { family: "Inter", size: 12 },
          padding: 12,
        },
      },
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

  const wrapRef = React.useRef(null);
  const stripChartRef = React.useRef(null);
  const dragRef = React.useRef(null);

  const mainData = React.useMemo(() => ({ datasets: buildLoadSeries(false) }), []);
  const stripData = React.useMemo(() => ({ datasets: buildLoadSeries(true) }), []);
  const mainOptions = React.useMemo(
    () => makeBrushMainOptions(selection, !reduced && !interacting),
    [selection, reduced, interacting],
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

function KMetricsChart() {
  const data = {
    labels: kMetrics.map((row) => `K=${row.k}`),
    datasets: [
      {
        type: "bar",
        label: "Silhouette",
        data: kMetrics.map((row) => row.silhouette),
        backgroundColor: kMetrics.map((row) => (row.selected ? "#48d7c2" : "#31465a")),
        borderRadius: 7,
        yAxisID: "y",
      },
      {
        type: "line",
        label: "Davies-Bouldin",
        data: kMetrics.map((row) => row.daviesBouldin),
        borderColor: "#f0a64b",
        backgroundColor: "#f0a64b",
        pointRadius: 4,
        tension: 0.35,
        yAxisID: "y1",
      },
    ],
  };
  const options = chartDefaults();
  options.scales.y.title = { display: true, text: "Silhouette", color: "#94a8b4" };
  options.scales.y1 = {
    position: "right",
    grid: { drawOnChartArea: false },
    ticks: { color: "#f0c384" },
    title: { display: true, text: "Davies-Bouldin", color: "#f0c384" },
  };
  return <Bar data={data} options={options} />;
}

function PcaChart() {
  const data = {
    labels: pcaComponents.map((row) => `PC${row.component}`),
    datasets: [
      {
        label: "Explained variance",
        data: pcaComponents.map((row) => row.explainedVariance * 100),
        backgroundColor: "#6c8cff",
        borderRadius: 7,
      },
      {
        type: "line",
        label: "Cumulative variance",
        data: pcaComponents.map((row) => row.cumulativeVariance * 100),
        borderColor: "#48d7c2",
        backgroundColor: "#48d7c2",
        pointRadius: 3,
        tension: 0.35,
      },
    ],
  };
  const options = chartDefaults();
  options.scales.y.ticks.callback = (value) => `${value}%`;
  options.scales.y.suggestedMax = 100;
  return <Bar data={data} options={options} />;
}

function ClusterRadar() {
  const labels = ["Morning", "Afternoon", "Evening", "Night", "Base load", "Variation"];
  const data = {
    labels,
    datasets: clusters.map((cluster) => ({
      label: cluster.name,
      data: [
        cluster.morningShare,
        cluster.afternoonShare,
        cluster.eveningShare,
        cluster.nightShare,
        cluster.baseLoadShare,
        cluster.coefficientOfVariation,
      ],
      borderColor: cluster.color,
      backgroundColor: `${cluster.color}24`,
      pointBackgroundColor: cluster.color,
    })),
  };
  return (
    <Radar
      data={data}
      options={{
        responsive: true,
        maintainAspectRatio: false,
        plugins: chartDefaults().plugins,
        scales: {
          r: {
            angleLines: { color: "rgba(141, 163, 176, 0.18)" },
            grid: { color: "rgba(141, 163, 176, 0.18)" },
            pointLabels: { color: "#dbe7ec", font: { size: 12 } },
            ticks: { color: "#94a8b4", backdropColor: "transparent" },
          },
        },
      }}
    />
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
              <div className="chart-container">
                <KMetricsChart />
              </div>
            </article>
            <article className="chart-panel">
              <div className="panel-heading">
                <h3>PCA variance</h3>
                <p>Fourteen components keep just over 95% of the variation.</p>
              </div>
              <div className="chart-container">
                <PcaChart />
              </div>
            </article>
            <article className="chart-panel">
              <div className="panel-heading">
                <h3>Cluster profile comparison</h3>
                <p>Shares describe timing; variation describes how peaked the shape is.</p>
              </div>
              <div className="chart-container">
                <ClusterRadar />
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
