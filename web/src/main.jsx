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

  // Tell the enclosing carousel when the representative (orange) line is shown,
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
    drawn: reduced ? profile.length : 2,
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

  const options = React.useMemo(() => {
    const base = chartDefaults();
    return {
      ...base,
      indexAxis: "y",
      plugins: { ...base.plugins, legend: { display: false } },
      scales: {
        x: { ...base.scales.x, beginAtZero: true, suggestedMax: 1 },
        y: { ...base.scales.y, grid: { display: false } },
      },
    };
  }, []);

  const data = {
    labels: FEATURE_ROWS.slice(0, state.shown).map((row) => row.key),
    datasets: [
      {
        label: `Share for ${representativeCluster.name}`,
        data: FEATURE_VALUES.slice(0, state.shown),
        backgroundColor: FEATURE_ROWS.slice(0, state.shown).map((row) => row.color),
        borderColor: "rgba(255,255,255,0)",
        borderWidth: 0,
        borderRadius: 3,
        barThickness: 8,
      },
    ],
  };

  return (
    <div className="features-slide" style={{ display: "flex", flexDirection: "column", height: "100%", minWidth: 0 }}>
      <div style={{ position: "relative", flex: 1, minHeight: 0, minWidth: 0 }}>
        <Bar data={data} options={options} />
      </div>
      <div
        className="features-count"
        style={{
          display: "flex",
          justifyContent: "center",
          paddingTop: 4,
          opacity: state.countShown ? 1 : 0,
          transition: "opacity 0.3s ease",
        }}
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
// A 2D scatter of consumer points is drawn, three centroids spawn, and then
// the algorithm iterates: every point is recoloured to its nearest centroid
// ("captured"), and each centroid moves to the mean of its claimed points.
// This is a live port of the scene's centroid-capture animation, using the
// scene's palette (cyan / green / amber). The point cloud is a schematic at
// the visualization boundary (the dashboard stores no raw 2D coordinates);
// the assignment and update steps run the real K-means algorithm so the
// motion is faithful. The concluding silhouette (0.312) is the committed
// figure.
// ---------------------------------------------------------------------------
const KM_COLORS = ["#22d3ee", "#4ade80", "#fbbf24"];
const KM_ITERS = 5;

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

// Three well-separated blobs (one per real consumer archetype), normalized
// coordinates in [0,1] x [0,1].
const KM_BLOBS = [
  { cx: 0.14, cy: 0.74, count: 20 },
  { cx: 0.46, cy: 0.28, count: 19 },
  { cx: 0.86, cy: 0.62, count: 18 },
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
      return { revealed: kmPointsData.length, spawned: true, assign: KM_FINAL.assign, cents: KM_FINAL.cents, done: true };
    }
    return {
      revealed: 0,
      spawned: false,
      assign: new Array(kmPointsData.length).fill(-1),
      cents: KM_INIT_CENTROIDS.map((c) => ({ x: c.x, y: c.y })),
      done: false,
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

    // 3. Iterate: assign points to the nearest centroid (capture), then move
    //    each centroid to the mean of its claimed points.
    let cents = KM_INIT_CENTROIDS.map((c) => ({ x: c.x, y: c.y }));
    let t = spawnAt + 520;
    for (let it = 0; it < KM_ITERS; it++) {
      const assign = kmNearestAssign(kmPointsData, cents);
      const next = kmStepCentroids(kmPointsData, assign);
      timers.push(
        setTimeout(() => {
          if (cancel) return;
          setState((prev) => ({ ...prev, assign }));
        }, t),
      );
      timers.push(
        setTimeout(() => {
          if (cancel) return;
          setState((prev) => ({ ...prev, cents: next }));
        }, t + 430),
      );
      cents = next;
      t += 860;
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

  const pad = 14;
  const width = size.width;
  const height = size.height;
  const px = (x) => pad + x * Math.max(0, width - 2 * pad);
  const py = (y) => pad + y * Math.max(0, height - 2 * pad);
  // React needs real style objects (a string here throws TypeError and unmounts
  // the app). cx/cy and fill are CSS-animatable geometry/style properties, so a
  // transition object gives the same smooth motion the scene gets from gsap.
  const pointTransition = reduced ? undefined : { transition: "fill 0.18s ease" };
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
              aria-label="K-Means clustering scatter: three centroids claim the consumer points"
            >
              <title>K-Means clustering scatter</title>
              {kmPointsData.map((point, i) => (
                <circle
                  key={i}
                  cx={px(point.x)}
                  cy={py(point.y)}
                  r={3}
                  fill={state.assign[i] >= 0 ? KM_COLORS[state.assign[i]] : "#9aa9b5"}
                  fillOpacity={i < state.revealed ? (state.assign[i] >= 0 ? 0.92 : 0.5) : 0}
                  stroke="none"
                  style={pointTransition}
                />
              ))}
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
        <span>3 DISTINCT CLUSTERS</span>
        <span style={{ color: "#fbbf24" }}>
          SILHOUETTE {Number(kMetrics.find((row) => row.selected)?.silhouette ?? 0.312).toFixed(3)}
        </span>
      </div>
    </div>
  );
}

// ---------------------------------------------------------------------------
// "PCA" slide - Slide 5, ported from Scene 5 (pca.js).
// The 14 retained components reveal as explained-variance bars (#6c8cff), the
// cumulative line (#48d7c2) then draws across them, and the retained-variance
// total appears once the cumulative line settles on the committed 95.3%.
// ---------------------------------------------------------------------------
const PCA_COMPONENTS = pcaComponents; // PC1..PC14, real committed values
const PCA_LABELS = pcaComponents.map((row) => `PC${row.component}`);
const PCA_RETAINED = pcaComponents[pcaComponents.length - 1].cumulativeVariance; // 0.9526

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
// (behavioralArchetypes.js). The three cluster profiles reveal one at a time
// as 24-hour curves, each tagged with its consumer count, preserving the
// scene's card-sequential rhythm and archetype colour identity.
// ---------------------------------------------------------------------------
const ARCHETYPE_COLORS = {
  "Midday-Peaking": "#fbbf24",
  "Flat All-Day": "#22d3ee",
  "Evening-Peaking": "#a78bfa",
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
// K=3 silhouette and Davies-Bouldin from kMetrics, the cluster count, and the
// dataset scale from summaryStats. Cards reveal in sequence (silhouette first,
// scene-coloured), then the validation caption appears.
// ---------------------------------------------------------------------------
function ValidationRobustnessSlide({ onRepActive }) {
  const reduced = usePrefersReducedMotion();
  const selected = kMetrics.find((row) => row.selected);
  const cards = [
    { label: "Silhouette", value: Number(selected?.silhouette).toFixed(3), color: "#a78bfa", note: "within vs between separation" },
    { label: "Davies-Bouldin", value: Number(selected?.daviesBouldin).toFixed(3), color: "#4ade80", note: "lower is better" },
    { label: "Clusters", value: String(selected?.k ?? 3), color: "#22d3ee", note: "selected K" },
  ];
  const [state, setState] = React.useState(() => ({
    shown: reduced ? cards.length : 0,
    done: reduced,
  }));

  React.useEffect(() => {
    onRepActive?.(reduced);
  }, [onRepActive, reduced]);

  React.useEffect(() => {
    if (reduced) return undefined;
    let cancel = false;
    const timers = [];
    cards.forEach((_, i) => {
      timers.push(
        setTimeout(() => {
          if (cancel) return;
          setState((prev) => ({ ...prev, shown: Math.max(prev.shown, i + 1) }));
        }, LEAD_IN_MS + 260 * i),
      );
    });
    timers.push(
      setTimeout(() => {
        if (cancel) return;
        setState((prev) => ({ ...prev, done: true }));
        onRepActive?.(true);
      }, LEAD_IN_MS + 260 * cards.length + 320),
    );
    return () => {
      cancel = true;
      timers.forEach(clearTimeout);
    };
  }, [reduced, cards, onRepActive]);

  return (
    <div
      className="validation-slide"
      style={{ display: "flex", flexDirection: "column", height: "100%", minWidth: 0 }}
    >
      <div style={{ flex: 1, minHeight: 0, display: "flex", alignItems: "center", justifyContent: "center" }}>
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
          {cards.map((card, i) => (
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
          {summaryStats.records} READING · {summaryStats.consumers} CONSUMERS
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
        title: "The orange line is the representative day",
        subtitle: "It is the midday-peaking rhythm, peaking around 1 pm.",
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
        subtitle: "Three centroids claim the consumer points, then move to their cluster means.",
      },
      rep: {
        title: "K=3 is the selected model",
        subtitle: "It scores a silhouette of 0.312, a modest but useful separation.",
      },
    },
  },
  {
    component: PcaSlide,
    captions: {
      idle: {
        title: "Principal component analysis",
        subtitle: "Fourteen principal components capture the shape variation.",
      },
      rep: {
        title: "Fourteen components retain 95.3% of the variance",
        subtitle: "The cumulative line settles just past 95 percent.",
      },
    },
  },
  {
    component: BehavioralArchetypesSlide,
    captions: {
      idle: {
        title: "Behavioral archetypes",
        subtitle: "The three clusters re-emerge as distinct household rhythm archetypes.",
      },
      rep: {
        title: "Three household rhythms",
        subtitle: "Midday peak, flat all-day, and evening peak, by consumer count.",
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
        title: "K=3 holds its shape across 144,000 readings",
        subtitle: "Silhouette 0.312 with 200 consumers and 3 clusters.",
      },
    },
  },
];

function LoadShapeCarousel({ tall = false }) {
  const [slide, setSlide] = React.useState(0);
  const [repActive, setRepActive] = React.useState(false);
  const count = loadShapeSlides.length;
  // Linear navigation: clamp instead of wrapping, so the prev arrow is disabled
  // on the first slide and the next arrow is disabled on the last.
  const goTo = (index) => setSlide(Math.max(0, Math.min(count - 1, index)));

  const { component: Slide, captions } = loadShapeSlides[slide];
  const caption = repActive ? captions.rep : captions.idle;

  return (
    <div className="carousel" role="group" aria-roledescription="carousel" aria-label="Daily load-shape data field">
      <div className="carousel-meta">
        <h3 className="carousel-title">{caption.title}</h3>
        <p className="carousel-subtitle">{caption.subtitle}</p>
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
          <div className={`chart-container${tall ? " tall" : ""}`}>
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
