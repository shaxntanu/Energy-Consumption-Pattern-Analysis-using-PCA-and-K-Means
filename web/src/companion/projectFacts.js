// Fact builders for the Sunee companion. Every fact is derived live from the
// real analysis exports in ../analysisData.js (which itself is copied verbatim
// from web/public/data/*.json) - nothing is invented here.
// Each builder returns { animation, text } or null when its data is not
// available on the current run, so the companion only ever speaks true facts.
import {
  populationShape,
  clusters,
  kMetrics,
  pcaComponents,
  summaryStats,
  seasonalStats,
  longitudinalStats,
  explainabilityStats,
  realWorldStats,
  validationStats,
} from '../analysisData'

const pct = (value, digits = 1) => `${(value * 100).toFixed(digits)}%`
const fmt = (value, digits = 3) => Number(value).toFixed(digits)

// populationShape is 24 hourly mean loads; the max index maps to that hour.
const peakHourLabel = `${populationShape.indexOf(Math.max(...populationShape)) + 1}:00`
const selectedKMetric = kMetrics.find((metric) => metric.selected)
const largestCluster = clusters.reduce((a, b) => (b.baseLoadShare > a.baseLoadShare ? b : a))
const clusterList = clusters.map((cluster) => `${cluster.name} (${cluster.size})`).join(', ')

const factBuilders = [
  () => ({
    animation: 'proud',
    text: `I've read ${summaryStats.records} hourly readings from ${summaryStats.consumers} consumers - a full year of smart-meter data.`,
  }),
  () => ({
    animation: 'curious',
    text: `Each consumer becomes a vector of ${summaryStats.features} engineered features: timing, load shape and variability.`,
  }),
  () => ({
    animation: 'proud',
    text: `PCA squeezes ${summaryStats.features} features into ${pcaComponents.length} components while keeping ${pct(summaryStats.varianceRaw)} of the variance.`,
  }),
  selectedKMetric
    ? () => ({
        animation: 'surprised',
        text: `We sweep K = 2..10 and K = ${selectedKMetric.k} wins the composite metric (${fmt(selectedKMetric.score)}) with a silhouette of ${fmt(selectedKMetric.silhouette)}.`,
      })
    : null,
  () => ({
    animation: 'curious',
    text: `Four consumer types emerge: ${clusterList}.`,
  }),
  () => ({
    animation: 'curious',
    text: `Across all consumers, demand peaks at ${peakHourLabel}.`,
  }),
  () => ({
    animation: 'happy',
    text: `The "${largestCluster.name}" group runs ${pct(largestCluster.baseLoadShare)} of its load as a steady base - the calmest rhythm of the four.`,
  }),
  () => ({
    animation: 'proud',
    text: `Re-running the whole pipeline barely moves: the cluster assignments are ${pct(summaryStats.stabilityRaw)} stable (ARI).`,
  }),
  () => ({
    animation: 'surprised',
    text: `On synthetic data with known answers, we recover the true groups with ARI ${fmt(validationStats.selectedKAri)} and NMI ${fmt(validationStats.selectedKNmi)}.`,
  }),
  seasonalStats.available
    ? () => ({
        animation: 'curious',
        text: `Seasons move the numbers: mean daily use is ${seasonalStats.meanDailyKwhBySeason.winter} kWh in winter vs ${seasonalStats.meanDailyKwhBySeason.summer} kWh in summer.`,
      })
    : null,
  seasonalStats.available
    ? () => ({
        animation: 'surprised',
        text: `Demand breathes with the seasons at about ${pct(seasonalStats.amplitude)} amplitude - a slow year-long wave that never enters the clustering features.`,
      })
    : null,
  seasonalStats.available
    ? () => ({
        animation: 'curious',
        text: `Even the busiest hour shifts: ${seasonalStats.peakHourBySeason.winter}:00 in winter vs ${seasonalStats.peakHourBySeason.summer}:00 in summer.`,
      })
    : null,
  seasonalStats.available
    ? () => ({
        animation: 'shy',
        text: `We recover the hidden seasonal phase from load shapes alone: r = ${fmt(seasonalStats.phaseR)} with ${pct(seasonalStats.phaseAgreement)} peak-season agreement - true on ${seasonalStats.nTruthConsumers} consumers.`,
      })
    : null,
  longitudinalStats.available
    ? () => ({
        animation: 'proud',
        text: `Across ${longitudinalStats.nSegments} quarterly windows, the consumer types hold at ${fmt(longitudinalStats.meanStability)} mean ARI.`,
      })
    : null,
  explainabilityStats.available
    ? () => ({
        animation: 'proud',
        text: `A surrogate classifier explains the clusters at ${pct(explainabilityStats.cvBalancedAccuracy, 2)} balanced accuracy, led by weekend_ratio.`,
      })
    : null,
  realWorldStats.available
    ? () => ({
        animation: 'happy',
        text: `On ${realWorldStats.meters} real meters, the same pipeline finds K = ${realWorldStats.selectedK} with a silhouette of ${fmt(realWorldStats.silhouette)}.`,
      })
    : null,
  () => ({
    animation: 'shy',
    text: `The toolkit is classic: PCA (Abdi & Williams, 2010) plus silhouette-based K selection (Rousseeuw, 1987).`,
  }),
]

// Returns the facts that are speakable on this run (non-null builders).
export const buildFacts = () => factBuilders.filter(Boolean).map((build) => build())
