import test from 'node:test'
import assert from 'node:assert/strict'
import { buildFacts } from './projectFacts.js'

const text = (data) => buildFacts(data).map((fact) => fact.text).join('\n')

test('peak hours are zero-based, including midnight and the last hour', () => {
  for (const peak of [0, 19, 23]) {
    const shape = Array(24).fill(1)
    shape[peak] = 2
    assert.match(text({ populationShape: shape }), new RegExp(`peaks at ${String(peak).padStart(2, '0')}:00`))
  }
})

test('ties are reported and flat or missing profiles do not invent a peak', () => {
  const shape = Array(24).fill(1)
  shape[8] = shape[20] = 2
  assert.match(text({ populationShape: shape }), /peaks at 08:00, 20:00/)
  assert.deepEqual(buildFacts({ populationShape: Array(24).fill(1) }), [])
  assert.deepEqual(buildFacts({}), [])
})

test('missing and non-finite optional metrics are not narrated', () => {
  const facts = text({
    summaryStats: { stabilityRaw: NaN },
    seasonalStats: { available: true, amplitude: null, phaseR: Infinity },
    explainabilityStats: { available: true, cvBalancedAccuracy: null },
    realWorldStats: { available: false, meters: 24, selectedK: 2, silhouette: 0.7 },
  })
  assert.equal(facts, '')
})

test('demo provenance and ARI interpretation stay explicit', () => {
  const facts = text({
    summaryStats: { stabilityRaw: 0.8 },
    realWorldStats: { available: true, meters: 12, selectedK: 3, silhouette: 0.4 },
  })
  assert.match(facts, /mean ARI 0.800/)
  assert.doesNotMatch(facts, /80.0%/)
  assert.match(facts, /12 synthetic demo meters/)
  assert.match(facts, /not performance on a real dataset/)
})

test('leading feature and recovered group count come from data', () => {
  const facts = text({
    clusters: [{ name: 'A', size: 2 }, { name: 'B', size: 3 }],
    explainabilityStats: {
      available: true, cvBalancedAccuracy: 0.9,
      globalImportance: [{ feature: 'small', value: 0.1 }, { feature: 'large', value: 0.5 }],
    },
  })
  assert.match(facts, /2 recovered clusters/)
  assert.match(facts, /highest for large/)
  assert.doesNotMatch(facts, /weekend_ratio/)
  assert.match(facts, /surrogate fidelity, not clustering accuracy/)
})

test('phase explanation uses seasonal energy, and committed facts stay deterministic', () => {
  const facts = text({ seasonalStats: {
    available: true, phaseR: 0.6, phaseAgreement: 0.8, nTruthConsumers: 10,
  } })
  assert.match(facts, /highest mean daily energy by season/)
  assert.deepEqual(buildFacts(), buildFacts())
  assert.ok(buildFacts().length > 0)
  assert.doesNotMatch(text(), /undefined|NaN|Infinity/)
})
