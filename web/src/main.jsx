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
          <a href="https://github.com/shaxntanu/Energy-Consumption-Pattern-Analysis-using-PCA-and-K-Means">GitHub</a>
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
          <LoadShapeChart />
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
              <LoadShapeChart />
            </article>
            <article className="chart-panel">
              <div className="panel-heading">
                <h3>K selection</h3>
                <p>K=3 balances separation with stable, non-tiny clusters.</p>
              </div>
              <KMetricsChart />
            </article>
            <article className="chart-panel">
              <div className="panel-heading">
                <h3>PCA variance</h3>
                <p>Fourteen components keep just over 95% of the variation.</p>
              </div>
              <PcaChart />
            </article>
            <article className="chart-panel">
              <div className="panel-heading">
                <h3>Cluster profile comparison</h3>
                <p>Shares describe timing; variation describes how peaked the shape is.</p>
              </div>
              <ClusterRadar />
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
              <a className="reference-card" href={reference.url} key={reference.title}>
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
      </main>
    </div>
  );
}

createRoot(document.getElementById("root")).render(<App />);
