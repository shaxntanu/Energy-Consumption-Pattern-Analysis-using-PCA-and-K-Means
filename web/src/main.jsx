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
import { Bar, Line } from "react-chartjs-2";
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
import VantaNetBackground from "./VantaNetBackground";
import ParticleText from "./components/ParticleText";
import GlowCursor from "./components/GlowCursor";
import LogoLoop from "./components/LogoLoop";
import DriftWall from "./components/DriftWall";
import MorphSlider from "./components/MorphSlider";
import "./styles.css";
import {
  clusters,
  clusterShapes,
  explainabilityStats,
  kMetrics,
  longitudinalStats,
  pcaComponents,
  populationShape,
  realWorldStats,
  references,
  seasonalStats,
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

// Every slide waits this long before its animation begins, so the reader has a
// beat to absorb the caption before the chart starts building.
const LEAD_IN_MS = 1500;

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

// ---------------------------------------------------------------------------
// "Raw Data Field" slide — Slide 1 of the load-shape carousel, ported from the
// test animation's first scene (ml_pipeline_animation/src/stages/rawDataField.js).
// A field of 12 sample consumer profiles emerges, then one line highlights as
// the representative. Profiles are derived from the same real archetype shapes
// the load-shape chart uses, adding only the same synthetic "consumer" noise the
// animation applies — so it stays a faithful port without inventing new committed
// data. It renders inside the same .chart-container area as the other slides and
// keeps the defined footprint (responsive, no overflow/clip).
// ---------------------------------------------------------------------------
const sampleProfiles = (() => {
  const bases = clusters.map((cluster) => clusterShapes[cluster.id]);
  const profiles = [];
  for (let i = 0; i < 12; i++) {
    const base = bases[i % bases.length];
    const noiseAmp = 0.15 + Math.random() * 0.1;
    const profile = base.map((v) => Math.max(0, v + (Math.random() - 0.5) * noiseAmp * v));
    const max = Math.max(...profile);
    profiles.push(profile.map((v) => v / max));
  }
  return profiles;
})();

const rawFieldColors = clusters.map((cluster) => cluster.color);

function RawDataFieldSlide({ onRepActive }) {
  const reduced = usePrefersReducedMotion();
  const [state, setState] = React.useState(() => ({
    // Representative line is full strength; the rest emerge over time.
    alpha: sampleProfiles.map((_, i) => (reduced ? (i === 0 ? 1 : 0.08) : 0)),
    highlighted: reduced,
  }));

  React.useEffect(() => {
    if (reduced) return undefined;
    let cancel = false;
    const timers = [];
    // Reveal each consumer line in sequence.
    sampleProfiles.forEach((_, i) => {
      timers.push(
        setTimeout(() => {
          if (cancel) return;
          setState((prev) => {
            const alpha = [...prev.alpha];
            alpha[i] = 0.35;
            return { ...prev, alpha };
          });
        }, LEAD_IN_MS + 260 * i),
      );
    });
    // Then highlight the representative line and fade the field behind it.
    timers.push(
      setTimeout(() => {
        if (cancel) return;
        setState({
          alpha: sampleProfiles.map((_, i) => (i === 0 ? 1 : 0.06)),
          highlighted: true,
        });
      }, LEAD_IN_MS + 260 * sampleProfiles.length + 700),
    );
    return () => {
      cancel = true;
      timers.forEach(clearTimeout);
    };
  }, [reduced]);

  // Tell the enclosing carousel when the representative (amber) line is shown,
  // so it can update the caption to say what that line represents.
  React.useEffect(() => {
    onRepActive?.(state.highlighted);
  }, [state.highlighted, onRepActive]);

  const options = React.useMemo(() => {
    const base = chartDefaults();
    // 12 transient lines would clutter the legend; hide just this slide's.
    return { ...base, plugins: { ...base.plugins, legend: { display: false } } };
  }, []);

  const data = {
    labels: hours,
    datasets: sampleProfiles.map((profile, i) => ({
      label: `Consumer ${String(i + 1).padStart(3, "0")}`,
      data: profile,
      borderColor: hexToRgba(rawFieldColors[i % rawFieldColors.length], state.alpha[i]),
      backgroundColor: "transparent",
      pointRadius: 0,
      tension: 0.42,
      fill: false,
      borderWidth: i === 0 && state.highlighted ? 2.4 : 1,
    })),
  };

  return <Line data={data} options={options} />;
}

// ---------------------------------------------------------------------------
// "Raw Data: Annotated Profile" slide - Slide 2 of the load-shape carousel,
// ported from the test animation's second scene
// (ml_pipeline_animation/src/stages/rawDataProfile.js). It zooms into the same
// representative day the field highlights (sampleProfiles[0]) and draws it as a
// single clean 24-hour rhythm with green day-phase brackets (NIGHT / MORNING /
// AFTERNOON / EVENING), preserving the scene's palette and timing. It only
// appends to the existing .chart-container footprint (no overflow/clip) and
// honors prefers-reduced-motion.
// ---------------------------------------------------------------------------
const DAY_PHASES = [
  { name: "NIGHT", start: 0, end: 6 },
  { name: "MORNING", start: 6, end: 12 },
  { name: "AFTERNOON", start: 12, end: 18 },
  { name: "EVENING", start: 18, end: 24 },
];

// Chart-axis value (higher = lower on screen) just above the peak consumption
// of each phase in the representative profile, so each bracket hangs over its
// own curve segment instead of the field's tallest line.
function phaseBracketValue(start, end) {
  const segment = sampleProfiles[0].slice(start, end + 1);
  const peak = Math.max(...segment);
  return Math.max(0.04, Math.min(1, 1 - peak + 0.07));
}

function buildPhaseBracketDataset(phase) {
  const value = phaseBracketValue(phase.start, phase.end);
  return {
    label: `${phase.name} phase`,
    data: hours.map((_, hour) => (hour >= phase.start && hour <= phase.end ? value : null)),
    borderColor: "#4ade80",
    backgroundColor: "transparent",
    borderWidth: 1.4,
    borderDash: [5, 4],
    pointRadius: 0,
    tension: 0,
    fill: false,
    spanGaps: false,
  };
}

function RawDataAnnotatedSlide({ onRepActive }) {
  const reduced = usePrefersReducedMotion();
  const profile = sampleProfiles[0];
  const [state, setState] = React.useState(() => ({
    // Start with nothing drawn so no partial line ("tail") shows during the
    // lead-in before the draw animation begins. Reduced motion still shows the
    // full profile immediately.
    drawn: reduced ? profile.length : 0,
    phaseShown: reduced ? DAY_PHASES.length : 0,
  }));

  React.useEffect(() => {
    if (reduced) return undefined;
    let cancel = false;
    const timers = [];

    // Draw the clean representative profile from left to right.
    const total = profile.length;
    for (let n = 2; n <= total; n++) {
      timers.push(
        setTimeout(() => {
          if (cancel) return;
          setState((prev) => ({ ...prev, drawn: Math.max(prev.drawn, n) }));
        }, LEAD_IN_MS + 50 * n),
      );
    }

    // Then reveal each day-phase bracket in sequence.
    const drawMs = LEAD_IN_MS + 50 * total;
    DAY_PHASES.forEach((_, i) => {
      timers.push(
        setTimeout(() => {
          if (cancel) return;
          setState((prev) => ({ ...prev, phaseShown: Math.max(prev.phaseShown, i + 1) }));
        }, drawMs + 340 * i),
      );
    });

    return () => {
      cancel = true;
      timers.forEach(clearTimeout);
    };
  }, [reduced]);

  // The representative profile is present throughout this slide, so report it
  // active to the carousel immediately to use the annotated caption.
  React.useEffect(() => {
    onRepActive?.(true);
  }, [onRepActive]);

  const options = React.useMemo(() => {
    const base = chartDefaults();
    return {
      ...base,
      plugins: { ...base.plugins, legend: { display: false } },
      scales: {
        ...base.scales,
        y: {
          ...base.scales.y,
          suggestedMin: 0,
          suggestedMax: 1,
          ticks: { ...base.scales?.y?.ticks, maxTicksLimit: 5 },
        },
      },
    };
  }, []);

  const data = {
    labels: hours,
    datasets: [
      {
        label: "Representative profile",
        data: profile.slice(0, state.drawn),
        borderColor: "#22d3ee",
        backgroundColor: "transparent",
        pointRadius: 0,
        tension: 0.42,
        fill: false,
        borderWidth: 2.4,
      },
      ...DAY_PHASES.filter((_, i) => i < state.phaseShown).map((phase) =>
        buildPhaseBracketDataset(phase),
      ),
    ],
  };

  return (
    <div
      className="annotated-slide"
      style={{ display: "flex", flexDirection: "column", height: "100%", minWidth: 0 }}
    >
      <div
        className="annotated-phases"
        style={{ display: "flex", justifyContent: "space-between", padding: "2px 8px 4px" }}
      >
        {DAY_PHASES.map((phase, i) => (
          <span
            key={phase.name}
            style={{
              color: "#4ade80",
              fontSize: "0.7rem",
              fontWeight: 600,
              letterSpacing: "0.14em",
              opacity: i < state.phaseShown ? 1 : 0,
              transition: "opacity 0.3s ease",
            }}
          >
            {phase.name}
          </span>
        ))}
      </div>
      <div style={{ position: "relative", flex: 1, minHeight: 0, minWidth: 0 }}>
        <Line data={data} options={options} />
      </div>
    </div>
  );
}

// ---------------------------------------------------------------------------
// "Behavioral Features" slide - Slide 3, ported from Scene 3 (features.js).
// The six timing/behavioural descriptors are revealed as bars for the
// representative (midday-peaking) cluster, then the 51-feature total appears.
// Palette and reveal order follow the scene; values are the committed cluster
// shares and base-load / variation fractions, so nothing is invented.
// ---------------------------------------------------------------------------
const representativeCluster = clusters[0];

// Scene-3 marker palette: each feature keeps the scene's own colour identity.
const FEATURE_ROWS = [
  { key: "Morning share", color: "#22d3ee" },
  { key: "Afternoon share", color: "#4ade80" },
  { key: "Evening share", color: "#fbbf24" },
  { key: "Night share", color: "#a78bfa" },
  { key: "Base load", color: "#f87171" },
  { key: "Variation (CV)", color: "#22d3ee" },
];
const FEATURE_VALUES = [
  representativeCluster.morningShare,
  representativeCluster.afternoonShare,
  representativeCluster.eveningShare,
  representativeCluster.nightShare,
  representativeCluster.baseLoadShare,
  representativeCluster.coefficientOfVariation,
];

// Compact y-axis labels for the six descriptors; the full names go in the
// legend beside the bars. Short, similar-width labels are all present from
// frame one, so the axis gutter never changes width and the plot area cannot
// shift sideways as bars reveal.
const SHORT_FEATURE_LABELS = ["Morn", "Aft", "Eve", "Night", "Base", "CV"];

function BehavioralFeaturesSlide({ onRepActive }) {
  const reduced = usePrefersReducedMotion();
  const [state, setState] = React.useState(() => ({
    shown: reduced ? FEATURE_ROWS.length : 0,
    countShown: reduced,
  }));

  React.useEffect(() => {
    onRepActive?.(reduced);
  }, [onRepActive, reduced]);

  React.useEffect(() => {
    if (reduced) return undefined;
    let cancel = false;
    const timers = [];
    FEATURE_ROWS.forEach((_, i) => {
      timers.push(
        setTimeout(() => {
          if (cancel) return;
          setState((prev) => ({ ...prev, shown: Math.max(prev.shown, i + 1) }));
        }, LEAD_IN_MS + 220 * i),
      );
    });
    timers.push(
      setTimeout(() => {
        if (cancel) return;
        setState((prev) => ({ ...prev, countShown: true }));
        onRepActive?.(true);
      }, LEAD_IN_MS + 220 * FEATURE_ROWS.length + 320),
    );
    return () => {
      cancel = true;
      timers.forEach(clearTimeout);
    };
  }, [reduced, onRepActive]);

  // Stable six-category layout: every reveal keeps the same band positions, so
  // each feature's label and bar pop in together instead of the axis reflowing
  // and the already-visible bars shuffling out of step with the reveal order.
  // Every short label is rendered from frame one (in a dimmer grey until its
  // own reveal), so the y-axis gutter width never changes and the plot area
  // cannot shift right as text appears.
  const options = React.useMemo(() => {
    const base = chartDefaults();
    const muted = "rgba(148, 168, 180, 0.35)";
    return {
      ...base,
      indexAxis: "y",
      // Short per-reveal pop so a bar settles right around when its label lands
      // (220ms reveal cadence); reduced motion draws the final frame instantly.
      animation: reduced ? false : { duration: 240 },
      plugins: { ...base.plugins, legend: { display: false } },
      scales: {
        x: { ...base.scales.x, beginAtZero: true, suggestedMax: 1 },
        y: {
          ...base.scales.y,
          grid: { display: false },
          ticks: {
            ...base.scales.y.ticks,
            // Chart.js hands a category scale the row INDEX here, not the label
            // — read the short name straight from SHORT_FEATURE_LABELS so the
            // axis never shows counting.
            callback(value, index) {
              return SHORT_FEATURE_LABELS[index] ?? "";
            },
            color(ctx) {
              return ctx.index < state.shown ? base.scales.y.ticks.color : muted;
            },
          },
        },
      },
    };
  }, [reduced, state.shown]);

  const data = {
    labels: FEATURE_ROWS.map((row) => row.key),
    datasets: [
      {
        label: `Share for ${representativeCluster.name}`,
        data: FEATURE_VALUES.map((value, i) => (i < state.shown ? value : 0)),
        // Hidden rows stay fully transparent and minBarLength is off, so no
        // coloured sliver peeks out of the axis during the lead-in or between
        // reveals — the pause stays clean until each bar's own turn.
        backgroundColor: FEATURE_ROWS.map((row, i) =>
          i < state.shown ? row.color : "rgba(0,0,0,0)",
        ),
        borderColor: "rgba(255,255,255,0)",
        borderWidth: 0,
        minBarLength: 0,
        borderRadius: 3,
        barThickness: 8,
      },
    ],
  };

  return (
    <div className="features-slide" style={{ display: "flex", flexDirection: "column", height: "100%", minWidth: 0 }}>
      <div className="features-main">
        <div style={{ position: "relative", flex: "1 1 auto", minHeight: 0, minWidth: 0 }}>
          <Bar data={data} options={options} />
        </div>
        {/* Legend to the right of the bars: short axis label, full form, and
            the row's colour, fading in in step with the matching bar. */}
        <div className="features-legend" aria-label="Feature legend: full forms of the axis abbreviations">
          {FEATURE_ROWS.map((row, i) => (
            <div
              className="features-legend-item"
              key={row.key}
              style={{
                opacity: i < state.shown ? 1 : 0,
                transform: i < state.shown ? "translateY(0)" : "translateY(3px)",
              }}
            >
              <span className="features-swatch" style={{ background: row.color }} aria-hidden="true" />
              <span className="features-short" style={{ color: row.color }}>
                {SHORT_FEATURE_LABELS[i]}
              </span>
              <span className="features-full">{row.key}</span>
            </div>
          ))}
        </div>
      </div>
      <div
        className={`features-count${state.countShown ? " features-count-in" : ""}`}
        style={{ opacity: state.countShown ? 1 : 0 }}
      >
        <span
          style={{
            color: "#a78bfa",
            fontFamily: '"IBM Plex Mono", ui-monospace, monospace',
            fontSize: "0.7rem",
            fontWeight: 700,
            letterSpacing: "0.14em",
          }}
        >
          {summaryStats.features} FEATURES
        </span>
      </div>
    </div>
  );
}

// ---------------------------------------------------------------------------
// "K-Means clustering" slide - Slide 4, ported from Scene 4 (kmeans.js).
// A 2D scatter of consumer points is drawn, four centroids spawn, and then
// the algorithm iterates: every point is recoloured to its nearest centroid
// ("captured"), and each centroid moves to the mean of its claimed points.
// This is a live port of the scene's centroid-capture animation, using the
// scene's palette (cyan / green / amber / rose). The point cloud is a
// schematic at the visualization boundary (the dashboard stores no raw 2D
// coordinates); the assignment and update steps run the real K-means
// algorithm so the motion is faithful. The concluding silhouette (0.328) is
// the committed figure.
// ---------------------------------------------------------------------------
const KM_COLORS = ["#22d3ee", "#4ade80", "#fbbf24", "#fb7185"];
const KM_ITERS = 5;

// Scatter-chart scaffolding for the K-Means slide: stay in normalized [0,1]
// space (matching the points), shared by both the faint grid/frame lines and
// the 0.0–1.0 tick labels.
const KM_GRID_STEPS = [0, 0.2, 0.4, 0.6, 0.8, 1];

// Seeded PRNG so the schematic cloud is stable across renders and slide
// switches (same approach as the source's SeededRandom).
function mulberry32(seed) {
  return function () {
    seed |= 0;
    seed = (seed + 0x6d2b79f5) | 0;
    let t = Math.imul(seed ^ (seed >>> 15), 1 | seed);
    t = (t + Math.imul(t ^ (t >>> 7), 61 | t)) ^ t;
    return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
  };
}

// Four well-separated blobs (one per real consumer archetype), normalized
// coordinates in [0,1] x [0,1].
const KM_BLOBS = [
  { cx: 0.14, cy: 0.74, count: 20 },
  { cx: 0.46, cy: 0.28, count: 19 },
  { cx: 0.86, cy: 0.62, count: 18 },
  { cx: 0.24, cy: 0.18, count: 17 },
];
const clamp01 = (v) => Math.max(0, Math.min(1, v));
const kmPointsData = (() => {
  const rand = mulberry32(7);
  const pts = [];
  KM_BLOBS.forEach((blob, bi) => {
    for (let c = 0; c < blob.count; c++) {
      const rx = (rand() * 2 - 1) * 0.15;
      const ry = (rand() * 2 - 1) * 0.15;
      pts.push({
        x: clamp01(blob.cx + rx),
        y: clamp01(blob.cy + ry),
        trueCluster: bi,
      });
    }
  });
  return pts;
})();

// Deliberately offset from the blob centres so the centroids visibly migrate
// while claiming points.
const KM_INIT_CENTROIDS = [
  { x: 0.05, y: 0.9 },
  { x: 0.4, y: 0.06 },
  { x: 0.94, y: 0.86 },
  { x: 0.16, y: 0.3 },
];

function kmNearestAssign(points, cents) {
  return points.map((p) => {
    let best = 0;
    let bestDist = Infinity;
    for (let k = 0; k < cents.length; k++) {
      const dx = p.x - cents[k].x;
      const dy = p.y - cents[k].y;
      const d = dx * dx + dy * dy;
      if (d < bestDist) {
        bestDist = d;
        best = k;
      }
    }
    return best;
  });
}

function kmStepCentroids(points, assign) {
  const sums = cents => cents.map(() => ({ x: 0, y: 0, c: 0 }));
  const acc = sums(KM_INIT_CENTROIDS);
  points.forEach((p, i) => {
    acc[assign[i]].x += p.x;
    acc[assign[i]].y += p.y;
    acc[assign[i]].c += 1;
  });
  return acc.map((a) => (a.c ? { x: a.x / a.c, y: a.y / a.c } : { x: 0.5, y: 0.5 }));
}

// Precomputed converged state (used by reduced-motion and as the final frame).
const KM_FINAL = (() => {
  let cents = KM_INIT_CENTROIDS.map((c) => ({ x: c.x, y: c.y }));
  let assign = [];
  for (let it = 0; it < KM_ITERS; it++) {
    assign = kmNearestAssign(kmPointsData, cents);
    cents = kmStepCentroids(kmPointsData, assign);
  }
  return { assign, cents };
})();

// Points glide toward their centroid on assignment (the "shoot"). KM_PULL is
// how far a claimed point advances toward its centroid each iteration and
// KM_GLIDE_MS is the CSS transition duration for that slide. The simulation is
// precomputed deterministically at load so the animated and reduced-motion
// paths show the same converged clusters.
const KM_PULL = 0.62;
const KM_GLIDE_MS = 380;
const kmLerp = (a, b, t) => ({ x: a.x + (b.x - a.x) * t, y: a.y + (b.y - a.y) * t });
const KM_SIM = (() => {
  let cents = KM_INIT_CENTROIDS.map((c) => ({ x: c.x, y: c.y }));
  let pts = kmPointsData.map((p) => ({ x: p.x, y: p.y }));
  const frames = [];
  for (let it = 0; it < KM_ITERS; it++) {
    const assign = kmNearestAssign(pts, cents);
    const pulled = pts.map((p, i) => kmLerp(p, cents[assign[i]], KM_PULL));
    const move = kmStepCentroids(pulled, assign);
    frames.push({ assign, pts: pulled, cents: cents.map((c) => ({ x: c.x, y: c.y })), move });
    pts = pulled;
    cents = move;
  }
  return { frames, finalCents: cents };
})();

function useElementSize() {
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
    const ro = new ResizeObserver(update);
    ro.observe(el);
    return () => ro.disconnect();
  }, []);
  return [ref, size];
}

function KMeansSlide({ onRepActive }) {
  const reduced = usePrefersReducedMotion();
  const [wrapRef, size] = useElementSize();
  const [state, setState] = React.useState(() => {
    if (reduced) {
      // Reduced motion: show the converged scatter immediately.
      return {
        revealed: kmPointsData.length,
        spawned: true,
        assign: KM_SIM.frames[KM_SIM.frames.length - 1].assign,
        pts: KM_SIM.frames[KM_SIM.frames.length - 1].pts,
        cents: KM_SIM.frames[KM_SIM.frames.length - 1].move,
        done: true,
        rays: false,
      };
    }
    return {
      revealed: 0,
      spawned: false,
      assign: new Array(kmPointsData.length).fill(-1),
      pts: kmPointsData.map((p) => ({ x: p.x, y: p.y })),
      cents: KM_INIT_CENTROIDS.map((c) => ({ x: c.x, y: c.y })),
      done: false,
      rays: false,
    };
  });

  React.useEffect(() => {
    onRepActive?.(reduced);
  }, [onRepActive, reduced]);

  React.useEffect(() => {
    if (reduced) return undefined;
    let cancel = false;
    const timers = [];

    // 1. Reveal the consumer points (grey) with the usual lead-in.
    kmPointsData.forEach((_, i) => {
      timers.push(
        setTimeout(() => {
          if (cancel) return;
          setState((prev) => ({ ...prev, revealed: Math.max(prev.revealed, i + 1) }));
        }, LEAD_IN_MS + 24 * i),
      );
    });

    // 2. Spawn the three centroids.
    const spawnAt = LEAD_IN_MS + 24 * kmPointsData.length + 300;
    timers.push(
      setTimeout(() => {
        if (cancel) return;
        setState((prev) => ({ ...prev, spawned: true }));
      }, spawnAt),
    );

    // 3. Iterate: glide each claimed point toward its centroid (the shoot),
    //    then move each centroid to the mean of its claimed points.
    let t = spawnAt + 520;
    for (let it = 0; it < KM_ITERS; it++) {
      const frame = KM_SIM.frames[it];
      timers.push(
        setTimeout(() => {
          if (cancel) return;
          setState((prev) => ({ ...prev, assign: frame.assign, pts: frame.pts, cents: frame.cents, rays: true }));
        }, t),
      );
      timers.push(
        setTimeout(() => {
          if (cancel) return;
          setState((prev) => ({ ...prev, cents: frame.move, rays: false }));
        }, t + KM_GLIDE_MS + 60),
      );
      t += KM_GLIDE_MS + 470;
    }

    // 4. Done: reveal the conclusion and caption.
    timers.push(
      setTimeout(() => {
        if (cancel) return;
        setState((prev) => ({ ...prev, done: true }));
        onRepActive?.(true);
      }, t + 200),
    );

    return () => {
      cancel = true;
      timers.forEach(clearTimeout);
    };
  }, [reduced, onRepActive]);

  // Asymmetric plot inset: extra room on the left/bottom holds the added axis
  // tick labels outside the frame instead of clipping them at the SVG edge.
  const padL = 38;
  const padR = 16;
  const padT = 18;
  const padB = 30;
  const width = size.width;
  const height = size.height;
  const px = (x) => padL + x * Math.max(0, width - padL - padR);
  const py = (y) => padT + y * Math.max(0, height - padT - padB);
  // React needs real style objects (a string here throws TypeError and unmounts
  // the app). cx/cy and fill are CSS-animatable geometry/style properties, so a
  // transition object gives the same smooth motion the scene gets from gsap.
  const pointTransition = reduced
    ? undefined
    : {
        transition: `cx ${KM_GLIDE_MS}ms cubic-bezier(0.33, 0.9, 0.25, 1), cy ${KM_GLIDE_MS}ms cubic-bezier(0.33, 0.9, 0.25, 1), fill 0.18s ease`,
      };
  const centroidTransition = reduced ? undefined : { transition: "cx 0.42s ease, cy 0.42s ease" };

  return (
    <div className="kmeans-slide" style={{ display: "flex", flexDirection: "column", height: "100%", minWidth: 0 }}>
      <div ref={wrapRef} style={{ position: "relative", flex: 1, minHeight: 0, minWidth: 0 }}>
        {width > 0 &&
          height > 0 && (
            <svg
              width={width}
              height={height}
              viewBox={`0 0 ${width} ${height}`}
              role="img"
              aria-label="K-Means clustering scatter: four centroids claim the consumer points"
            >
              <title>K-Means clustering scatter</title>
              {/* Graph-like scaffolding behind the points: a faint Cartesian
                  grid with a framed axis and compact 0.0–1.0 ticks, so the
                  cluster claims read against a real scatter chart — not a
                  blank panel. */}
              {KM_GRID_STEPS.map((f) => (
                <line
                  key={`grid-v-${f}`}
                  x1={px(f)}
                  y1={py(0)}
                  x2={px(f)}
                  y2={py(1)}
                  stroke={
                    f === 0 || f === 1
                      ? "rgba(148, 168, 180, 0.30)"
                      : "rgba(141, 163, 176, 0.10)"
                  }
                  strokeWidth={1}
                />
              ))}
              {KM_GRID_STEPS.map((f) => (
                <line
                  key={`grid-h-${f}`}
                  x1={px(0)}
                  y1={py(f)}
                  x2={px(1)}
                  y2={py(f)}
                  stroke={
                    f === 0 || f === 1
                      ? "rgba(148, 168, 180, 0.30)"
                      : "rgba(141, 163, 176, 0.10)"
                  }
                  strokeWidth={1}
                />
              ))}
              {KM_GRID_STEPS.map((f) => (
                <g key={`tick-${f}`}>
                  <text
                    x={px(f)}
                    y={py(1) + 15}
                    textAnchor="middle"
                    fill="rgba(148, 168, 180, 0.55)"
                    fontSize="9"
                  >
                    {f.toFixed(1)}
                  </text>
                  <text
                    x={px(0) - 8}
                    y={py(f) + 3}
                    textAnchor="end"
                    fill="rgba(148, 168, 180, 0.55)"
                    fontSize="9"
                  >
                    {f.toFixed(1)}
                  </text>
                </g>
              ))}
              {kmPointsData.map((point, i) => (
                <circle
                  key={i}
                  cx={px(state.pts[i].x)}
                  cy={py(state.pts[i].y)}
                  r={3}
                  fill={state.assign[i] >= 0 ? KM_COLORS[state.assign[i]] : "#9aa9b5"}
                  fillOpacity={i < state.revealed ? (state.assign[i] >= 0 ? 0.92 : 0.5) : 0}
                  stroke="none"
                  style={pointTransition}
                />
              ))}
              {state.rays &&
                state.spawned &&
                kmPointsData.map((point, i) => {
                  const c = state.assign[i];
                  if (i >= state.revealed || c < 0) return null;
                  return (
                    <line
                      key={`ray-${i}`}
                      x1={px(state.pts[i].x)}
                      y1={py(state.pts[i].y)}
                      x2={px(state.cents[c].x)}
                      y2={py(state.cents[c].y)}
                      stroke={KM_COLORS[c]}
                      strokeWidth={1}
                      strokeDasharray="2,3"
                      strokeOpacity={0.7}
                      pointerEvents="none"
                    />
                  );
                })}
              {state.spawned &&
                KM_INIT_CENTROIDS.map((_, k) => (
                  <g key={k}>
                    <circle
                      cx={px(state.cents[k].x)}
                      cy={py(state.cents[k].y)}
                      r={11}
                      fill="none"
                      stroke={KM_COLORS[k]}
                      strokeWidth={2.5}
                      style={centroidTransition}
                    />
                    <circle
                      cx={px(state.cents[k].x)}
                      cy={py(state.cents[k].y)}
                      r={4}
                      fill={KM_COLORS[k]}
                      style={centroidTransition}
                    />
                    <text
                      x={px(state.cents[k].x)}
                      y={py(state.cents[k].y) - 17}
                      textAnchor="middle"
                      fill={KM_COLORS[k]}
                      fontSize="11"
                      fontWeight="600"
                    >
                      C{k + 1}
                    </text>
                  </g>
                ))}
            </svg>
          )}
      </div>
      <div
        className="kmeans-tag"
        style={{
          display: "flex",
          justifyContent: "center",
          gap: "0.5rem",
          color: "#4ade80",
          fontFamily: '"IBM Plex Mono", ui-monospace, monospace',
          fontSize: "0.7rem",
          fontWeight: 700,
          letterSpacing: "0.12em",
          paddingTop: 4,
          opacity: state.done ? 1 : 0,
          transition: "opacity 0.3s ease",
          flexWrap: "wrap",
        }}
      >
        <span>4 DISTINCT CLUSTERS</span>
        <span style={{ color: "#fbbf24" }}>
          SILHOUETTE {Number(kMetrics.find((row) => row.selected)?.silhouette ?? 0.328).toFixed(3)}
        </span>
      </div>
    </div>
  );
}

// ---------------------------------------------------------------------------
// "PCA" slide - Slide 5, ported from Scene 5 (pca.js).
// The 10 retained components reveal as explained-variance bars (#6c8cff), the
// cumulative line (#48d7c2) then draws across them, and the retained-variance
// total appears once the cumulative line settles on the committed 95.0%.
// ---------------------------------------------------------------------------
const PCA_COMPONENTS = pcaComponents; // PC1..PC10, real committed values
const PCA_LABELS = pcaComponents.map((row) => `PC${row.component}`);
const PCA_RETAINED = pcaComponents[pcaComponents.length - 1].cumulativeVariance; // 0.9505

function PcaSlide({ onRepActive }) {
  const reduced = usePrefersReducedMotion();
  const total = PCA_COMPONENTS.length;
  const [state, setState] = React.useState(() => ({
    bars: reduced ? total : 0,
    line: reduced ? total : 0,
    done: reduced,
  }));

  React.useEffect(() => {
    onRepActive?.(reduced);
  }, [onRepActive, reduced]);

  React.useEffect(() => {
    if (reduced) return undefined;
    let cancel = false;
    const timers = [];
    // Bars pop in one at a time.
    PCA_COMPONENTS.forEach((_, i) => {
      timers.push(
        setTimeout(() => {
          if (cancel) return;
          setState((prev) => ({ ...prev, bars: Math.max(prev.bars, i + 1) }));
        }, LEAD_IN_MS + 160 * i),
      );
    });
    // Cumulative line draws across after the bars finish.
    const barsDone = LEAD_IN_MS + 160 * total;
    for (let j = 0; j < total; j++) {
      timers.push(
        setTimeout(() => {
          if (cancel) return;
          setState((prev) => ({ ...prev, line: Math.max(prev.line, j + 1) }));
        }, barsDone + 110 * j),
      );
    }
    timers.push(
      setTimeout(() => {
        if (cancel) return;
        setState((prev) => ({ ...prev, done: true }));
        onRepActive?.(true);
      }, barsDone + 110 * total + 320),
    );
    return () => {
      cancel = true;
      timers.forEach(clearTimeout);
    };
  }, [reduced, total, onRepActive]);

  const options = React.useMemo(() => {
    const base = chartDefaults();
    return {
      ...base,
      plugins: { ...base.plugins, legend: { display: false } },
      scales: {
        x: { ...base.scales.x, grid: { display: false } },
        y: {
          ...base.scales.y,
          beginAtZero: true,
          max: 1,
          ticks: {
            ...base.scales?.y?.ticks,
            maxTicksLimit: 5,
            callback: (value) => `${Math.round(value * 100)}%`,
          },
        },
      },
    };
  }, []);

  const data = {
    labels: PCA_LABELS,
    datasets: [
      {
        type: "bar",
        label: "Explained variance",
        data: PCA_COMPONENTS.slice(0, state.bars).map((row) => row.explainedVariance),
        backgroundColor: "#6c8cff",
        borderColor: "rgba(255,255,255,0)",
        borderRadius: 3,
        barThickness: 8,
        maxBarThickness: 18,
      },
      {
        type: "line",
        label: "Cumulative variance",
        data: PCA_COMPONENTS.slice(0, state.line).map((row) => row.cumulativeVariance),
        borderColor: "#48d7c2",
        backgroundColor: "transparent",
        borderWidth: 2.2,
        pointRadius: 0,
        tension: 0.3,
        fill: false,
        spanGaps: false,
      },
    ],
  };

  return (
    <div className="pca-slide" style={{ display: "flex", flexDirection: "column", height: "100%", minWidth: 0 }}>
      <div style={{ position: "relative", flex: 1, minHeight: 0, minWidth: 0 }}>
        <Bar data={data} options={options} />
      </div>
      <div
        className="pca-tag"
        style={{
          display: "flex",
          justifyContent: "center",
          paddingTop: 4,
          opacity: state.done ? 1 : 0,
          transition: "opacity 0.3s ease",
        }}
      >
        <span
          style={{
            color: "#fbbf24",
            fontFamily: '"IBM Plex Mono", ui-monospace, monospace',
            fontSize: "0.7rem",
            fontWeight: 700,
            letterSpacing: "0.14em",
          }}
        >
          {(PCA_RETAINED * 100).toFixed(1)}% VARIANCE RETAINED
        </span>
      </div>
    </div>
  );
}

// ---------------------------------------------------------------------------
// "Behavioral Archetypes" slide - Slide 6, ported from Scene 6
// (behavioralArchetypes.js). The four cluster profiles reveal one at a time
// as 24-hour curves, each tagged with its consumer count, preserving the
// scene's card-sequential rhythm and archetype colour identity.
// ---------------------------------------------------------------------------
const ARCHETYPE_COLORS = {
  "Midday-Peaking Weekday-Heavy": "#f2b04b",
  "Flat All-Day": "#48d7c2",
  "Evening-Peaking": "#b78cff",
  "Evening-Peaking Weekend-Heavy": "#fb7185",
};

function BehavioralArchetypesSlide({ onRepActive }) {
  const reduced = usePrefersReducedMotion();
  const [state, setState] = React.useState(() => ({
    shown: reduced ? clusters.length : 0,
    done: reduced,
  }));

  React.useEffect(() => {
    onRepActive?.(reduced);
  }, [onRepActive, reduced]);

  React.useEffect(() => {
    if (reduced) return undefined;
    let cancel = false;
    const timers = [];
    clusters.forEach((_, i) => {
      timers.push(
        setTimeout(() => {
          if (cancel) return;
          setState((prev) => ({ ...prev, shown: Math.max(prev.shown, i + 1) }));
        }, LEAD_IN_MS + 280 * i),
      );
    });
    timers.push(
      setTimeout(() => {
        if (cancel) return;
        setState((prev) => ({ ...prev, done: true }));
        onRepActive?.(true);
      }, LEAD_IN_MS + 280 * clusters.length + 320),
    );
    return () => {
      cancel = true;
      timers.forEach(clearTimeout);
    };
  }, [reduced, onRepActive]);

  const shown = clusters.slice(0, state.shown);

  const options = React.useMemo(() => {
    const base = chartDefaults();
    return {
      ...base,
      plugins: { ...base.plugins, legend: { display: false } },
      scales: {
        x: { ...base.scales.x, grid: { display: false } },
        y: { ...base.scales.y, beginAtZero: true },
      },
    };
  }, []);

  const data = {
    labels: hours,
    datasets: shown.map((cluster) => ({
      label: cluster.name,
      data: clusterShapes[cluster.id],
      borderColor: ARCHETYPE_COLORS[cluster.name] || cluster.color,
      backgroundColor: "transparent",
      pointRadius: 0,
      tension: 0.42,
      fill: false,
      borderWidth: 2.2,
    })),
  };

  return (
    <div
      className="archetypes-slide"
      style={{ display: "flex", flexDirection: "column", height: "100%", minWidth: 0 }}
    >
      <div style={{ position: "relative", flex: 1, minHeight: 0, minWidth: 0 }}>
        <Line data={data} options={options} />
      </div>
      <div
        className="archetype-chips"
        style={{ display: "flex", justifyContent: "center", gap: "1rem", paddingTop: 4, flexWrap: "wrap" }}
      >
        {clusters.map((cluster, i) => (
          <span
            key={cluster.id}
            style={{
              display: "flex",
              alignItems: "center",
              gap: 6,
              color: "#dbe7ec",
              fontFamily: '"IBM Plex Mono", ui-monospace, monospace',
              fontSize: "0.7rem",
              letterSpacing: "0.05em",
              opacity: i < state.shown ? 1 : 0,
              transition: "opacity 0.3s ease",
            }}
          >
            <span
              aria-hidden="true"
              style={{
                width: 9,
                height: 9,
                borderRadius: 2,
                background: ARCHETYPE_COLORS[cluster.name] || cluster.color,
                flex: "none",
              }}
            />
            {cluster.name}
            <span aria-hidden="true" style={{ color: "#71808d" }}>
              {cluster.size}
            </span>
          </span>
        ))}
      </div>
    </div>
  );
}

// ---------------------------------------------------------------------------
// "Validation & Robustness" slide - Slide 7, ported from Scene 7
// (validationRobustness.js). Only committed figures are shown: the selected
// K=4 silhouette and Davies-Bouldin from kMetrics, the cluster count, and the
// dataset scale from summaryStats.
//
// The three cards reveal fast and tight, then a compact K-sweep (silhouette
// bars + Davies-Bouldin line across K=2..10, K=4 highlighted) fades in below
// to fill the panel with the actual evidence that picked K=4.
// ---------------------------------------------------------------------------
// Cards lead the beat so all three land well before the old ~1.3s lag; the
// sweep follows right after the last card, then the caption.
//
// VALIDATION_CARDS must live at module scope: the reveal effect schedules one
// timer per card, and with referentially-stable inputs ([reduced, onRepActive])
// it runs exactly once and every timer survives for its full duration. If the
// card array were built inside the component (as it once was), each render
// would mint a fresh identity, the effect would re-run on every setState,
// clearTimeout all pending timers, and restart the clock — so each card reveal
// cancelled the later cards' timers and only the first card ever appeared.
const VALIDATION_CARDS_AT = 800;
const VALIDATION_CARD_STAGGER = 120;
const VALIDATION_SWEEP_AT = VALIDATION_CARDS_AT + VALIDATION_CARD_STAGGER * 3 + 240;
const VALIDATION_DONE_AT = VALIDATION_SWEEP_AT + 360;

const VALIDATION_SELECTED = kMetrics.find((row) => row.selected);

const VALIDATION_CARDS = [
  { label: "Silhouette", value: Number(VALIDATION_SELECTED?.silhouette).toFixed(3), color: "#a78bfa", note: "within vs between separation" },
  { label: "Davies-Bouldin", value: Number(VALIDATION_SELECTED?.daviesBouldin).toFixed(3), color: "#4ade80", note: "lower is better" },
  { label: "Clusters", value: String(VALIDATION_SELECTED?.k ?? 3), color: "#22d3ee", note: "selected K" },
];

function ValidationRobustnessSlide({ onRepActive }) {
  const reduced = usePrefersReducedMotion();
  const [state, setState] = React.useState(() => ({
    shown: reduced ? VALIDATION_CARDS.length : 0,
    sweepShown: reduced,
    done: reduced,
  }));

  React.useEffect(() => {
    onRepActive?.(reduced);
  }, [onRepActive, reduced]);

  React.useEffect(() => {
    if (reduced) return undefined;
    let cancel = false;
    const timers = [];
    VALIDATION_CARDS.forEach((_, i) => {
      timers.push(
        setTimeout(() => {
          if (cancel) return;
          setState((prev) => ({ ...prev, shown: Math.max(prev.shown, i + 1) }));
        }, VALIDATION_CARDS_AT + VALIDATION_CARD_STAGGER * i),
      );
    });
    timers.push(
      setTimeout(() => {
        if (cancel) return;
        setState((prev) => ({ ...prev, sweepShown: true }));
      }, VALIDATION_SWEEP_AT),
    );
    timers.push(
      setTimeout(() => {
        if (cancel) return;
        setState((prev) => ({ ...prev, done: true }));
        onRepActive?.(true);
      }, VALIDATION_DONE_AT),
    );
    return () => {
      cancel = true;
      timers.forEach(clearTimeout);
    };
  }, [reduced, onRepActive]);

  // Compact K = 2..10 sweep reusing the composed chart family. Same data and
  // series as the full K-selection chart, but sized for the carousel panel.
  const sweepRows = kMetrics.map((row) => ({
    k: `K${row.k}`,
    kNumber: row.k,
    silhouette: row.silhouette,
    daviesBouldin: row.daviesBouldin,
  }));
  const sweepSelected = kMetrics.findIndex((row) => row.selected);

  return (
    <div
      className="validation-slide"
      style={{ display: "flex", flexDirection: "column", height: "100%", minWidth: 0 }}
    >
      <div
        className="validation-cards"
        style={{
          display: "flex",
          gap: "0.75rem",
          justifyContent: "center",
          alignItems: "stretch",
          flexWrap: "wrap",
        }}
      >
        {VALIDATION_CARDS.map((card, i) => (
          <div
            key={card.label}
            className="validation-card"
            style={{
              flex: "1 1 120px",
              maxWidth: 200,
              textAlign: "center",
              padding: "0.7rem 0.9rem",
              border: `1px solid ${card.color}44`,
              borderRadius: 10,
              background: "var(--panel-strong)",
              opacity: i < state.shown ? 1 : 0,
              transform: i < state.shown ? "translateY(0)" : "translateY(6px)",
              transition: "opacity 0.3s ease, transform 0.3s ease",
            }}
          >
            <div
              style={{
                color: card.color,
                fontFamily: '"IBM Plex Mono", ui-monospace, monospace',
                fontSize: "0.7rem",
                fontWeight: 700,
                letterSpacing: "0.12em",
              }}
            >
              {card.label}
            </div>
            <div
              style={{
                color: "#ffffff",
                fontSize: "1.5rem",
                fontWeight: 700,
                lineHeight: 1.1,
                margin: "0.2rem 0 0.1rem",
              }}
            >
              {card.value}
            </div>
            <div style={{ color: "#71808d", fontSize: "0.7rem" }}>{card.note}</div>
          </div>
        ))}
      </div>

      <div className={`validation-sweep${state.sweepShown ? " is-shown" : ""}`}>
        <div className="validation-sweep-top" aria-hidden="true">
          <span className="validation-sweep-key">
            <span className="validation-sweep-dot" style={{ background: "var(--cyan)" }} />
            Silhouette
          </span>
          <span className="validation-sweep-key">
            <span className="validation-sweep-line" style={{ background: "var(--amber)" }} />
            Davies-Bouldin
          </span>
        </div>
        <ComposedChart
          data={sweepRows}
          xDataKey="k"
          selectedIndex={sweepSelected}
          maxBarSize={26}
          ariaLabel="K-sweep validation chart: Silhouette bars and Davies-Bouldin line from K=2 to K=10, with K=4 highlighted"
        >
          <Grid horizontal />
          <YAxis yAxisId="left" orientation="left" label="Silhouette" tickCount={4} />
          <YAxis yAxisId="right" orientation="right" label="DB index" tickCount={4} />
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

      <div
        className="validation-foot"
        style={{
          display: "flex",
          justifyContent: "center",
          paddingTop: 4,
          opacity: state.done ? 1 : 0,
          transition: "opacity 0.3s ease",
        }}
      >
        <span
          style={{
            color: "#48d7c2",
            fontFamily: '"IBM Plex Mono", ui-monospace, monospace',
            fontSize: "0.7rem",
            letterSpacing: "0.12em",
          }}
        >
          {summaryStats.records} READING · {summaryStats.consumers} CONSUMERS · RECOVERY ARI {summaryStats.recovery}
        </span>
      </div>
    </div>
  );
}

// Slides shown in the "Average 24-hour load shape" carousel, each with its own
// caption (shown before and after its representative state). Arrows and dots
// derive from the array length, so adding a slide updates navigation itself.
const loadShapeSlides = [
  {
    component: RawDataFieldSlide,
    captions: {
      idle: {
        title: "Daily load shapes",
        subtitle: "Twelve raw daily profiles resolve into one representative 24-hour rhythm.",
      },
      rep: {
        title: "The highlighted line is the representative day",
        subtitle: "It is the midday-peaking weekday-heavy rhythm, peaking around 1 pm.",
      },
    },
  },
  {
    component: RawDataAnnotatedSlide,
    captions: {
      idle: {
        title: "Annotated representative profile",
        subtitle: "A single clean 24-hour rhythm with day-phase brackets.",
      },
      rep: {
        title: "Annotated representative profile",
        subtitle: "Four phase brackets trace the day: night, morning, afternoon, evening.",
      },
    },
  },
  {
    component: BehavioralFeaturesSlide,
    captions: {
      idle: {
        title: "Behavioral features",
        subtitle: "Six timing and shape descriptors are extracted from every daily profile.",
      },
      rep: {
        title: "Six shape features in the midday-peaking rhythm",
        subtitle: "Morning and afternoon shares lead; base load and variation round out the shape.",
      },
    },
  },
  {
    component: KMeansSlide,
    captions: {
      idle: {
        title: "K-Means clustering",
        subtitle: "Four centroids claim the consumer points, then move to their cluster means.",
      },
      rep: {
        title: "K=4 is the selected model",
        subtitle: "It scores a silhouette of 0.328, a modest but useful separation.",
      },
    },
  },
  {
    component: PcaSlide,
    captions: {
      idle: {
        title: "Principal component analysis",
        subtitle: "Ten principal components capture the shape variation.",
      },
      rep: {
        title: "Ten components retain 95.0% of the variance",
        subtitle: "The cumulative line settles just past 95 percent.",
      },
    },
  },
  {
    component: BehavioralArchetypesSlide,
    captions: {
      idle: {
        title: "Behavioral archetypes",
        subtitle: "The four clusters re-emerge as distinct household rhythm archetypes.",
      },
      rep: {
        title: "Four household rhythms",
        subtitle: "Midday peak, flat all-day, evening peak, and weekend-heavy evening peak, by consumer count.",
      },
    },
  },
  {
    component: ValidationRobustnessSlide,
    captions: {
      idle: {
        title: "Validation and robustness",
        subtitle: "The selected model is checked on real, committed metrics.",
      },
      rep: {
        title: "K=4 holds its shape across 1.75 million readings",
        subtitle: "Silhouette 0.328 with 200 consumers and 4 clusters.",
      },
    },
  },
];

function LoadShapeCarousel({ tall = false }) {
  const [slide, setSlide] = React.useState(0);
  const [repActive, setRepActive] = React.useState(false);
  const count = loadShapeSlides.length;
  // Linear navigation: clamp instead of wrapping, so the prev arrow is disabled
  // on the first slide and the next arrow is disabled on the last. A fresh
  // slide always starts in its idle caption state — resetting the flag here
  // stops the previous slide's rep title from flashing for a frame.
  const goTo = (index) => {
    setSlide(Math.max(0, Math.min(count - 1, index)));
    setRepActive(false);
  };

  const { component: Slide, captions } = loadShapeSlides[slide];
  const caption = repActive ? captions.rep : captions.idle;

  // Replay the caption entrance whenever the text itself changes (idle → rep),
  // so the swap is a small eased rise instead of an abrupt text pop. Keying an
  // inner wrapper by this tick remounts just the caption, leaving the slide's
  // own carousel-enter fade (which plays on slide switch) untouched.
  const [captionKey, setCaptionKey] = React.useState(0);
  const prevCaptionRef = React.useRef(caption);
  React.useEffect(() => {
    if (prevCaptionRef.current !== caption) {
      prevCaptionRef.current = caption;
      setCaptionKey((key) => key + 1);
    }
  }, [caption]);

  return (
    <div className="carousel" role="group" aria-roledescription="carousel" aria-label="Daily load-shape data field">
      {/* keyed by slide so the fade (styles.css carousel-enter) replays on
          every switch and the hard remount reads as one eased entry. */}
      <div key={slide} className="carousel-meta">
        <div className="carousel-caption" key={captionKey}>
          <h3 className="carousel-title">{caption.title}</h3>
          <p className="carousel-subtitle">{caption.subtitle}</p>
        </div>
      </div>
      <div className="carousel-body">
        <button
          className="carousel-arrow prev"
          type="button"
          aria-label="Previous visualization"
          disabled={slide === 0}
          onClick={() => goTo(slide - 1)}
        >
          <svg viewBox="0 0 24 24" aria-hidden="true">
            <path d="M15 5l-7 7 7 7" />
          </svg>
        </button>
        <div className="carousel-stage">
          <div key={slide} className={`chart-container${tall ? " tall" : ""}`}>
            <Slide onRepActive={setRepActive} />
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
          disabled={slide === count - 1}
          onClick={() => goTo(slide + 1)}
        >
          <svg viewBox="0 0 24 24" aria-hidden="true">
            <path d="M9 5l7 7-7 7" />
          </svg>
        </button>
      </div>
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

// Five entries for the composable legend, in the same order as the datasets
// (0 = population, then the four archetypes in cluster order) so indices line
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
          ariaLabel="PCA variance: explained variance bars and cumulative variance line from PC1 to PC10"
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
          {/* 10 PCs would crowd as horizontal ticks; vertical labels keep every
              component readable without clashing (see ComposedChart). */}
          <XAxis tickRotation={-90} />
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
  "Midday-Peaking Weekday-Heavy": "var(--amber)",
  "Flat All-Day": "var(--cyan)",
  "Evening-Peaking": "var(--violet)",
  "Evening-Peaking Weekend-Heavy": "var(--rose)",
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
        ariaLabel="Cluster profile comparison: four household archetypes across six load-shape dimensions"
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

// Small labelled bar used by the Science Highlights band. Values are genuine
// contract figures; bars only rescale for presentation (never touch the data).
function MiniBar({ label, value, max, color, format }) {
  const pct = max > 0 ? Math.max(0, Math.min(100, (value / max) * 100)) : 0;
  return (
    <div className="mini-bar-row">
      <span className="mini-label">{label}</span>
      <span className="mini-track">
        <span className="mini-fill" style={{ width: `${pct}%`, background: color }} />
      </span>
      <span className="mini-value">{format(value)}</span>
    </div>
  );
}

// Honest availability chip: available: true on the flagship run; the pipeline
// emits available: false + a reason at short horizons rather than inventing
// numbers (this page shows the flagship run, so all threads are available).
function AvailabilityChip({ available }) {
  return (
    <span className={`availability${available ? " is-true" : " is-false"}`} aria-hidden="true">
      {available ? "available · true" : "available · false"}
    </span>
  );
}

// The four upgraded analysis threads, fed by the committed contract exports in
// analysisData.js (sourced from web/public/data/*.json).
function ScienceHighlights() {
  const seasons = [
    { label: "winter", value: seasonalStats.meanDailyKwhBySeason.winter },
    { label: "spring", value: seasonalStats.meanDailyKwhBySeason.spring },
    { label: "summer", value: seasonalStats.meanDailyKwhBySeason.summer },
    { label: "autumn", value: seasonalStats.meanDailyKwhBySeason.autumn },
  ];
  const maxSeasonKwh = Math.max(...seasons.map((s) => s.value));
  const maxImportance = Math.max(
    ...explainabilityStats.globalImportance.map((f) => f.value),
  );
  return (
    <section className="band" id="highlights">
      <SectionHeader eyebrow="Beyond the base pipeline" title="Seasonal, longitudinal, explainability, and the real-world pathway">
        The upgraded run adds four analysis threads on top of the core K-Means story. All
        figures are the committed flagship outputs (contract_version 1.0.0, config
        99c7a6631340d301). At shorter horizons the pipeline reports available: false with a
        reason instead of inventing numbers.
      </SectionHeader>
      <div className="highlights-grid">
        <article className="highlight-card">
          <div className="highlight-head">
            <h3>Seasonal model</h3>
            <AvailabilityChip available={seasonalStats.available} />
          </div>
          <p>
            Magnitude (annual amplitude of daily totals) is separated from timing (a phase
            shift of the 24-hour profile), so the seasonal swing never changes a daily
            total.
          </p>
          <div className="chip-row">
            <span className="chip">amplitude 0.202</span>
            <span className="chip">phase r 0.678</span>
            <span className="chip">agreement 0.885</span>
          </div>
          <div className="mini-bars">
            {seasons.map((s) => (
              <MiniBar
                key={s.label}
                label={s.label}
                value={s.value}
                max={maxSeasonKwh}
                color="var(--cyan)"
                format={(v) => v.toFixed(1)}
              />
            ))}
          </div>
        </article>

        <article className="highlight-card">
          <div className="highlight-head">
            <h3>Longitudinal stability</h3>
            <AvailabilityChip available={longitudinalStats.available} />
          </div>
          <p>
            Four non-overlapping quarterly windows re-run scaling → PCA → K selection
            independently; agreement with the full-window partition is measured
            permutation-invariantly.
          </p>
          <div className="chip-row">
            <span className="chip">mean ARI 0.882</span>
            <span className="chip">{longitudinalStats.nSegments} segments</span>
          </div>
          <div className="mini-bars">
            {longitudinalStats.segments.map((seg) => (
              <MiniBar
                key={seg.label}
                label={seg.label}
                value={seg.ari}
                max={1}
                color="var(--blue)"
                format={(v) => v.toFixed(3)}
              />
            ))}
          </div>
        </article>

        <article className="highlight-card">
          <div className="highlight-head">
            <h3>Explainability</h3>
            <AvailabilityChip available={explainabilityStats.available} />
          </div>
          <p>
            A small surrogate random forest learns the recovered labels; attribution runs on
            that surrogate (SHAP TreeExplainer, honest permutation fallback otherwise).
          </p>
          <div className="chip-row">
            <span className="chip">method shap</span>
            <span className="chip">cv acc 0.985</span>
          </div>
          <div className="mini-bars">
            {explainabilityStats.globalImportance.map((f) => (
              <MiniBar
                key={f.feature}
                label={f.feature}
                value={f.value}
                max={maxImportance}
                color="var(--amber)"
                format={(v) => v.toFixed(3)}
              />
            ))}
          </div>
        </article>

        <article className="highlight-card">
          <div className="highlight-head">
            <h3>Real-world pathway</h3>
            <AvailabilityChip available={realWorldStats.available} />
          </div>
          <p>
            A documented adapter ingests an external long panel. The real branch reports
            internal quality and stability only — never ARI/NMI against invented labels.
          </p>
          <div className="chip-row">
            <span className="chip">{realWorldStats.meters} meters</span>
            <span className="chip">K = {realWorldStats.selectedK}</span>
            <span className="chip">silhouette 0.719</span>
            <span className="chip">seed stability 1.0</span>
          </div>
          <div className="mini-bars">
            <MiniBar
              label="silhouette"
              value={realWorldStats.silhouette}
              max={1}
              color="var(--violet)"
              format={(v) => v.toFixed(3)}
            />
            <MiniBar
              label="Calinski-Harabasz"
              value={realWorldStats.ch}
              max={realWorldStats.ch}
              color="var(--violet)"
              format={(v) => v.toFixed(1)}
            />
            <MiniBar
              label="Davies-Bouldin"
              value={realWorldStats.db}
              max={realWorldStats.db}
              color="var(--violet)"
              format={(v) => v.toFixed(3)}
            />
          </div>
        </article>
      </div>
    </section>
  );
}

// The optional C++ performance engine (Phase: HPC). The browser never executes
// C++: this section consumes the offline benchmark report committed to
// /data/benchmark.json by `py src/run_cpp_benchmark.py`. When the engine is
// unbuilt the report exists with status "not_executed" and this section shows
// that state honestly instead of inventing speedups.
function PerformanceSection() {
  const [bench, setBench] = React.useState(null);
  const [state, setState] = React.useState("loading"); // loading | error | ready

  React.useEffect(() => {
    let cancelled = false;
    fetch("/data/benchmark.json")
      .then((res) => {
        if (!res.ok) throw new Error(`HTTP ${res.status}`);
        return res.json();
      })
      .then((data) => {
        if (!cancelled) {
          setBench(data);
          setState("ready");
        }
      })
      .catch(() => {
        if (!cancelled) setState("error");
      });
    return () => {
      cancelled = true;
    };
  }, []);

  const engine = bench?.engine || {};
  const info = engine.compile_info || {};
  const executed = state === "ready" && bench.status === "executed";

  // Per-dataset speedup from the flat rows (one entry per engine).
  const rowsByKey = {};
  (bench?.rows || []).forEach((r) => {
    rowsByKey[`${r.dataset}:${r.stage}:${r.engine}`] = r;
  });
  const stages = executed
    ? [...new Set((bench.rows || []).map((r) => `${r.dataset}·${r.stage}`))].map((key) => {
        const [dataset, stage] = key.split("·");
        const py = rowsByKey[`${dataset}:${stage}:python`];
        const cpp = rowsByKey[`${dataset}:${stage}:cpp`];
        return { dataset, stage, py, cpp };
      })
    : [];

  return (
    <section className="band" id="performance">
      <SectionHeader
        eyebrow="High-performance computing engine"
        title="The same two kernels, compiled to native code"
      >
        PCA and K-Means also ship as an optional C++ engine (energy_cpp). The
        Python/scikit-learn implementation remains the scientific reference for every
        result on this page; C++ is a performance-oriented alternative, validated
        against that reference and compared offline. The frontend only renders the
        committed benchmark report — it never executes C++ in the browser.
      </SectionHeader>

      {state === "loading" && (
        <div className="highlight-card">
          <p>Reading the committed benchmark report…</p>
        </div>
      )}

      {state === "error" && (
        <div className="highlight-card">
          <div className="highlight-head">
            <h3>Benchmark report unavailable</h3>
            <span className="availability is-false">not found</span>
          </div>
          <p>
            No <code>/data/benchmark.json</code> is committed. Run{" "}
            <code>py src/run_cpp_benchmark.py</code> after building the engine to
            generate it. No timing or agreement numbers are shown in the meantime.
          </p>
        </div>
      )}

      {state === "ready" && (
        <>
          <div className="highlights-grid">
            <article className="highlight-card">
              <div className="highlight-head">
                <h3>Engine state</h3>
                <span className={`availability${engine.available ? " is-true" : " is-false"}`}>
                  {engine.available ? "built" : "not built"}
                </span>
              </div>
              <p>
                Whether <code>energy_cpp</code> was importable when the offline
                benchmark ran. The Python pipeline works either way — the module is
                strictly optional.
              </p>
              <div className="chip-row">
                <span className="chip">compiler {info.compiler || "-"}</span>
                <span className="chip">OpenMP {String(info.openmp ?? "-")}</span>
                <span className="chip">C++{info.cxx_standard || "-"}</span>
              </div>
              {!engine.available && (
                <p>
                  <code>{engine.build_command || "py -m pip install ./cpp_engine"}</code>
                </p>
              )}
            </article>

            <article className="highlight-card">
              <div className="highlight-head">
                <h3>Kernel agreement</h3>
                <span className={`availability${executed ? " is-true" : " is-false"}`}>
                  {executed ? "benchmarked" : "not executed"}
                </span>
              </div>
              <p>
                The two engines are compared on identical matrices. PCA components are
                sign-aligned (sklearn svd_flip); K-Means labels are compared
                permutation-invariantly with ARI/AMI.
              </p>
              {!executed ? (
                <p>
                  The committed report says status <code>not_executed</code>
                  {bench.reason ? ` — ${bench.reason}` : ""}. No speedups or agreement
                  numbers are fabricated here.
                </p>
              ) : (
                <BenchmarkAgreement bench={bench} />
              )}
            </article>
          </div>

          {executed && (
            <>
              <div className="bench-table-wrap">
                <table className="bench-table">
                  <thead>
                    <tr>
                      <th>dataset</th>
                      <th>stage</th>
                      <th>samples</th>
                      <th>features</th>
                      <th>python (ms)</th>
                      <th>c++ (ms)</th>
                      <th>speedup</th>
                    </tr>
                  </thead>
                  <tbody>
                    {stages.map((s) => {
                      const speedup =
                        s.py && s.cpp && s.cpp.time_ms > 0
                          ? (s.py.time_ms / s.cpp.time_ms).toFixed(2)
                          : "-";
                      return (
                        <tr key={`${s.dataset}:${s.stage}`}>
                          <td>{s.dataset}</td>
                          <td>{s.stage}</td>
                          <td>{s.py ? s.py.n_samples : "-"}</td>
                          <td>{s.py ? s.py.n_features : "-"}</td>
                          <td>{s.py ? s.py.time_ms.toFixed(2) : "-"}</td>
                          <td>{s.cpp ? s.cpp.time_ms.toFixed(2) : "-"}</td>
                          <td className={speedup !== "-" && Number(speedup) > 1 ? "bench-fast" : ""}>
                            {speedup}
                          </td>
                        </tr>
                      );
                    })}
                  </tbody>
                </table>
              </div>
              <p className="bench-note">
                Best-of-3 wall times after one warmup, on the identical matrix for both
                engines; K-Means runs on the same PCA scores. Dataset provenance is
                recorded in the report — medium/large are bootstrap resamples of the
                flagship matrix, wide is a synthetic feature-scaling probe.
              </p>
            </>
          )}
        </>
      )}
    </section>
  );
}

// The agreement chips for an executed benchmark report.
function BenchmarkAgreement({ bench }) {
  const pca = bench.agreement?.pca_small;
  const km = bench.agreement?.kmeans_small;
  const e2e = bench.end_to_end;
  return (
    <div className="mini-bars">
      {pca && (
        <MiniBar
          label="component diff"
          value={pca.max_abs_component_diff}
          max={1e-6}
          color="var(--cyan)"
          format={(v) => v.toExponential(1)}
        />
      )}
      {km && (
        <>
          <MiniBar
            label="k-means ARI"
            value={km.ari}
            max={1}
            color="var(--blue)"
            format={(v) => v.toFixed(4)}
          />
          <MiniBar
            label="k-means AMI"
            value={km.ami}
            max={1}
            color="var(--blue)"
            format={(v) => v.toFixed(4)}
          />
          <MiniBar
            label="inertia rel. diff"
            value={km.inertia_relative_diff}
            max={1e-3}
            color="var(--amber)"
            format={(v) => v.toExponential(1)}
          />
        </>
      )}
      {e2e && (
        <MiniBar
          label="e2e speedup"
          value={e2e.speedup_x}
          max={Math.max(1, e2e.speedup_x)}
          color="var(--violet)"
          format={(v) => `${v.toFixed(2)}x`}
        />
      )}
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
          <a href="#performance">Performance</a>
          <a href="#references">References</a>
          <a href="https://energy-consumption-pattern-vqrh.streamlit.app/" target="_blank" rel="noopener noreferrer">Simulator</a>
        </div>
      </nav>

      <header className="hero" id="top">
        <div className="hero-copy">
          <VantaNetBackground />
          <span className="eyebrow">PCA plus K-Means energy clustering</span>
          <GlowCursor
            color="#48d7c2"
            secondaryColor="#b78cff"
            trailLength={40}
            trailWidth={8}
            trailTaper={0.8}
            followSpeed={0.16}
            glowIntensity={1.9}
            glowSpread={1.2}
            hotspot={0.65}
            brightness={1.25}
            opacity={1}
            pulseSpeed={1.1}
            noiseStrength={0.035}
            idleFade
            idleTimeout={700}
            fadeDuration={900}
            blendMode="screen"
          >
            <div style={{ display: "flex", gap: "2rem", alignItems: "flex-start" }}>
              <div style={{ flex: 1, minWidth: 0 }}>
                <ParticleText
                  text="Energy use is a pattern, not just a number."
                  particleSize={2.2}
                  density={4}
                  color="#48d7c2"
                  highlight="#b78cff"
                  scatter={190}
                  gatherDuration={1600}
                  stagger={420}
                  pointerRepel={42}
                  repelRadius={120}
                  idleDrift={0.8}
                  trigger="mount"
                  fontSize="clamp(2.5rem, 8vw, 6rem)"
                  fontWeight={800}
                />
              </div>
              <aside style={{ width: "100%", maxWidth: 400, flexShrink: 0 }}>
                <MorphSlider
                  items={[
                    { image: "/results/load_shapes.png", caption: "Load Shapes" },
                    { image: "/results/pca_variance.png", caption: "PCA Variance" },
                    { image: "/results/k_selection.png", caption: "K-Selection" },
                    { image: "/results/cluster_radar.png", caption: "Cluster Radar" },
                    { image: "/results/validation_sweep.png", caption: "Validation" },
                  ]}
                  transition="melt"
                  intensity={0.55}
                  aberration={0.35}
                  drift={0.4}
                  autoplay={false}
                  overlayColor="#05060a"
                  duration={1.1}
                  ease="power2.inOut"
                  scale={2.4}
                  autoplayDelay={4}
                  loop
                  radius={16}
                  showCaptions
                  showControls
                  showIndicators
                />
              </aside>
            </div>
            <p>
              This project simulates a full year of household electricity readings, turns
              each day into a load shape, compresses the features with PCA, and uses K-Means
              to find daily rhythms that are easier to explain — then checks how the clusters
              hold up across seasons, over time, and on a real-world demo panel.
            </p>
            <div className="hero-actions">
              <a className="button primary" href="#charts">Explore the charts</a>
              <a className="button secondary" href="#about">What is this project about?</a>
            </div>
          </GlowCursor>
        </div>
        <div className="hero-panel chart-panel tall">
          <LoadShapeCarousel tall />
        </div>
      </header>

      <main>
        <section className="band" id="about">
          <SectionHeader eyebrow="What is this project about" title="A simple way to find daily energy rhythms">
            The analysis asks whether consumers can be grouped by when they use power. It
            uses a controlled synthetic year (200 households × 365 days, config
            99c7a6631340d301) so the result is a reproducible demonstration of the method,
            not a claim about real households. A separate adapter pathway ingests
            real-world panels with honest, internal-only validation.
          </SectionHeader>
          <div className="stats-grid">
            <StatCard label="Records" value={summaryStats.records} note="hourly synthetic readings · one year" />
            <StatCard label="Consumers" value={summaryStats.consumers} />
            <StatCard label="Features" value={summaryStats.features} note="behavioural shape descriptors" />
            <StatCard label="PCA components" value={summaryStats.pcaComponents} note={`${summaryStats.variance} variance retained`} />
            <StatCard label="Selected clusters" value={summaryStats.clusters} />
            <StatCard label="Silhouette" value={summaryStats.silhouette} note="modest but useful separation" />
            <StatCard label="Archetype recovery" value={summaryStats.recovery} note="ARI vs hidden archetypes at K=4" />
            <StatCard label="Temporal stability" value={summaryStats.temporalStability} note="mean ARI across 4 quarterly windows" />
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
                <p>K=4 wins the composite rule — silhouette 0.328, stability ARI 0.995.</p>
              </div>
              <KSelectionChart />
            </article>
            <article className="chart-panel">
              <div className="panel-heading">
                <h3>PCA Variance</h3>
                <p>Ten components keep just over 95% of the variation.</p>
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
          <SectionHeader eyebrow="Cluster stories" title="Four readable patterns">
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

        <ScienceHighlights />

        <PerformanceSection />

        {/* DriftWall — Matplotlib gallery presentation */}
        <section className="band" id="gallery">
          <SectionHeader eyebrow="Results gallery" title="Matplotlib analysis outputs">
            The following images are generated by the Python pipeline and committed to
            <code>/web/public/results/</code>. They show the full analytical picture:
            load shapes, PCA variance, K-selection, cluster profiles, validation sweeps,
            seasonal stability, longitudinal agreement, explainability, real-world demo,
            and C++ benchmarks.
          </SectionHeader>
          <div style={{ height: 560 }}>
            <DriftWall
              items={[
                { image: '/results/load_shapes.png', title: 'Average Load Shapes', href: '#charts' },
                { image: '/results/pca_variance.png', title: 'PCA Explained Variance', href: '#charts' },
                { image: '/results/k_selection.png', title: 'K-Selection Metrics', href: '#charts' },
                { image: '/results/cluster_radar.png', title: 'Cluster Profiles Radar', href: '#charts' },
                { image: '/results/cluster_0_profile.png', title: 'Cluster 0: Night Owls', href: '#charts' },
                { image: '/results/cluster_1_profile.png', title: 'Cluster 1: Early Birds', href: '#charts' },
                { image: '/results/cluster_2_profile.png', title: 'Cluster 2: Day Workers', href: '#charts' },
                { image: '/results/cluster_3_profile.png', title: 'Cluster 3: Evening Peak', href: '#charts' },
                { image: '/results/seasonal_stability.png', title: 'Seasonal Stability', href: '#charts' },
                { image: '/results/longitudinal_ari.png', title: 'Longitudinal ARI', href: '#charts' },
                { image: '/results/validation_sweep.png', title: 'Validation Sweep', href: '#charts' },
                { image: '/results/explainability.png', title: 'Feature Importance', href: '#charts' },
                { image: '/results/real_world.png', title: 'Real-World Demo', href: '#charts' },
                { image: '/results/benchmark.png', title: 'C++ Benchmark', href: '#performance' },
                { image: '/results/pipeline.png', title: 'Pipeline Flow', href: '#about' },
              ]}
              columns={5}
              tileWidth={200}
              tileHeight={132}
              gap={18}
              tilt={16}
              turn={-14}
              perspective={1200}
              depth={120}
              speed={42}
              direction="up"
              variance={0.45}
              parallax={0.6}
              lift={64}
              fade={0.6}
              dim={0.55}
              overlayColor="#060010"
              radius={14}
              roll={0}
              pauseOnHover={false}
              grayscale={false}
            />
          </div>
        </section>

        {/* LogoLoop — Tech stack scroller */}
        <section className="band" style={{ paddingTop: 0, paddingBottom: 2 }}>
          <div style={{ height: 140, position: 'relative', overflow: 'hidden' }}>
            <LogoLoop
              speed={100}
              direction="left"
              logoHeight={60}
              gap={60}
              hoverSpeed={0}
              scaleOnHover
              fadeOut
              fadeOutColor="#070b10"
              ariaLabel="Technology stack"
            />
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

// A small root error boundary. A single WebGL shader, chart or animation throwing
// during render or an effect would otherwise make React unmount the whole tree and
// leave the page blank. This catches it, logs the exact message, and renders a
// readable fallback instead — so the load never ends in an empty white screen.
class RootBoundary extends React.Component {
  constructor(props) {
    super(props);
    this.state = { error: null };
  }
  static getDerivedStateFromError(error) {
    return { error };
  }
  componentDidCatch(error, info) {
    console.error("UI crashed:", error, info?.componentStack ?? "");
  }
  render() {
    if (this.state.error) {
      return (
        <div style={{ maxWidth: "720px", margin: "6rem auto", padding: "0 1.25rem", color: "#dbe7ec", fontFamily: "Inter, system-ui, sans-serif" }}>
          <p style={{ fontFamily: "'IBM Plex Mono', ui-monospace, monospace", fontSize: "0.75rem", letterSpacing: "0.16em", textTransform: "uppercase", color: "#48d7c2" }}>
            Energy Load-Shape Clustering
          </p>
          <h1 style={{ fontSize: "1.6rem", fontWeight: 600, margin: "0.5rem 0 0.75rem" }}>Something on this page failed to render.</h1>
          <p style={{ color: "#94a8b4", lineHeight: 1.6 }}>
            A component crashed during render. The page keeps its shell rather than going blank.
            The error message is logged to the browser console; reload to retry.
          </p>
          <pre style={{ marginTop: "1rem", padding: "0.9rem 1rem", background: "#101722", border: "1px solid #2d3c4d", borderRadius: 8, overflowX: "auto", fontSize: "0.78rem", fontFamily: "'IBM Plex Mono', ui-monospace, monospace", whiteSpace: "pre-wrap" }}>
            {String(this.state.error && this.state.error.message)}
          </pre>
        </div>
      );
    }
    return this.props.children;
  }
}

createRoot(document.getElementById("root")).render(
  <RootBoundary>
    <App />
  </RootBoundary>
);
