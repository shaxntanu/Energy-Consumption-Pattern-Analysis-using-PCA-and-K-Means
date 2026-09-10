// Deterministic explanations of the committed display data, not LLM output.
// Missing/non-finite inputs suppress a fact rather than inventing a number.
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
} from '../analysisData.js'

const defaultData = {
  populationShape, clusters, kMetrics, pcaComponents, summaryStats,
  seasonalStats, longitudinalStats, explainabilityStats, realWorldStats, validationStats,
}
const finite = (...values) => values.every(Number.isFinite)
const pct = (value, digits = 1) => `${(value * 100).toFixed(digits)}%`
const fmt = (value, digits = 3) => value.toFixed(digits)
const hour = (value) => `${String(value).padStart(2, '0')}:00`

export function buildFacts(data = defaultData) {
  const {
    populationShape: shape = [], clusters: groups = [], kMetrics: sweep = [],
    pcaComponents: components = [], summaryStats: summary = {},
    seasonalStats: seasons = {}, longitudinalStats: longitudinal = {},
    explainabilityStats: explanation = {}, realWorldStats: demo = {},
    validationStats: validation = {},
  } = data
  const facts = []
  const add = (animation, text) => facts.push({ animation, text })

  if (finite(summary.nRecords, summary.nConsumers)) {
    add('proud', `This synthetic study contains ${summary.nRecords.toLocaleString('en-US')} hourly readings from ${summary.nConsumers} simulated consumers, not measurements of real households.`)
  }
  const featureCount = Number(summary.features)
  if (Number.isInteger(featureCount) && featureCount > 0) {
    add('curious', `Each consumer becomes a vector of ${featureCount} engineered features describing timing, load shape and variability.`)
    if (components.length > 0 && finite(summary.varianceRaw)) {
      add('proud', `PCA compresses ${featureCount} features into ${components.length} components while retaining ${pct(summary.varianceRaw)} of the variance.`)
    }
  }

  const selected = sweep.find((metric) => metric.selected)
  const candidates = sweep.map((metric) => metric.k).filter(Number.isFinite)
  if (selected && candidates.length && finite(selected.k, selected.score, selected.silhouette)) {
    add('surprised', `Among candidate K values ${candidates.join(', ')}, K = ${selected.k} wins the composite rule (score ${fmt(selected.score)}, silhouette ${fmt(selected.silhouette)}). K is selected without consulting the hidden archetypes.`)
  }
  const describedGroups = groups.filter((group) => group.name && finite(group.size))
  if (describedGroups.length) {
    add('curious', `${describedGroups.length} recovered clusters: ${describedGroups.map((group) => `${group.name} (${group.size})`).join(', ')}. These names describe load patterns, not household identities.`)
  }
  if (shape.length === 24 && finite(...shape) && Math.max(...shape) > 0) {
    const peak = Math.max(...shape)
    const peaks = shape.flatMap((value, index) => value === peak ? [hour(index)] : [])
    if (peaks.length < 24) {
      add('curious', `The population mean load shape peaks at ${peaks.join(', ')}. Hour bins run from 00:00 to 23:00.`)
    }
  }
  const baseLoadGroup = groups.filter((group) => group.name && finite(group.baseLoadShare))
    .reduce((best, group) => !best || group.baseLoadShare > best.baseLoadShare ? group : best, null)
  if (baseLoadGroup) {
    add('happy', `The "${baseLoadGroup.name}" cluster has the highest base-load share (${pct(baseLoadGroup.baseLoadShare)}) among the displayed clusters.`)
  }
  if (finite(summary.stabilityRaw)) {
    add('proud', `K-Means restarts on the same PCA scores agree at mean ARI ${fmt(summary.stabilityRaw)}. ARI is chance-adjusted partition agreement, not a percentage of unchanged assignments or a whole-pipeline rerun test.`)
  }
  if (finite(validation.selectedKAri, validation.selectedKNmi)) {
    add('surprised', `Against the synthetic generator's hidden archetypes, recovery is ARI ${fmt(validation.selectedKAri)} and NMI ${fmt(validation.selectedKNmi)}. This is not evidence of accuracy on real households.`)
  }
  if (seasons.available) {
    const energy = seasons.meanDailyKwhBySeason || {}
    if (finite(energy.winter, energy.summer)) {
      add('curious', `In this simulation, mean daily use is ${energy.winter} kWh in winter and ${energy.summer} kWh in summer.`)
    }
    if (finite(seasons.amplitude)) {
      add('surprised', `The estimated seasonal energy swing is ${pct(seasons.amplitude)} of the mean, using (maximum minus minimum seasonal mean) divided by twice the mean.`)
    }
    const peakHours = seasons.peakHourBySeason || {}
    if (finite(peakHours.winter, peakHours.summer)) {
      add('curious', `The population peak hour is ${hour(peakHours.winter)} in winter and ${hour(peakHours.summer)} in summer.`)
    }
    if (finite(seasons.phaseR, seasons.phaseAgreement, seasons.nTruthConsumers)) {
      add('shy', `Seasonal phase is estimated from each consumer's highest mean daily energy by season, not load shape alone. The displayed recovery is r = ${fmt(seasons.phaseR)}, with ${pct(seasons.phaseAgreement)} peak-season agreement and ${seasons.nTruthConsumers} consumers with hidden phase data.`)
    }
  }
  if (longitudinal.available && finite(longitudinal.nSegments, longitudinal.meanStability)) {
    add('proud', `Across ${longitudinal.nSegments} temporal windows, partitions agree with the full-window grouping at mean ARI ${fmt(longitudinal.meanStability)}.`)
  }
  if (explanation.available && finite(explanation.cvBalancedAccuracy)) {
    const leading = (explanation.globalImportance || [])
      .filter((item) => item.feature && finite(item.value))
      .reduce((best, item) => !best || item.value > best.value ? item : best, null)
    add('proud', `A post-hoc classifier predicts the recovered cluster labels at ${pct(explanation.cvBalancedAccuracy, 2)} cross-validated balanced accuracy.${leading ? ` The displayed global importance is highest for ${leading.feature}.` : ''} This measures surrogate fidelity, not clustering accuracy or causation.`)
  }
  if (demo.available && finite(demo.meters, demo.selectedK, demo.silhouette)) {
    add('happy', `The real-world ingestion pathway was exercised with ${demo.meters} synthetic demo meters: K = ${demo.selectedK}, silhouette ${fmt(demo.silhouette)}. This tests the plumbing, not performance on a real dataset.`)
  }
  return facts
}
