import test from 'node:test'
import assert from 'node:assert/strict'
import { canReplaceMessage, nextFactIndex, canOfferAutomaticFact } from './companionBehavior.js'

const nav = (text) => ({ kind: 'navigation', priority: 100, text })

test('latest navigation replaces stale navigation without admitting lower priority facts', () => {
  assert.equal(canReplaceMessage(nav('About'), nav('Charts')), true)
  assert.equal(canReplaceMessage(nav('Charts'), nav('Charts')), false)
  assert.equal(canReplaceMessage(nav('Charts'), { kind: 'fact', priority: 50 }), false)
  assert.equal(canReplaceMessage({ kind: 'fact', priority: 50 }, nav('Charts')), true)
  assert.equal(canReplaceMessage(null, nav('Charts')), true)
})

test('equal priority facts do not interrupt one another', () => {
  assert.equal(canReplaceMessage({ kind: 'fact', priority: 50 }, { kind: 'fact', priority: 50 }), false)
})

test('deterministic rotation visits every fact before repeating', () => {
  let index = -1
  const seen = []
  for (let i = 0; i < 8; i += 1) {
    index = nextFactIndex(index, 4)
    seen.push(index)
  }
  assert.deepEqual(seen, [0, 1, 2, 3, 0, 1, 2, 3])
  assert.equal(nextFactIndex(-1, 0), -1)
  assert.equal(nextFactIndex(0, 1), 0)
})

test('automatic facts respect input, visibility and inactivity boundaries', () => {
  const base = { hidden: false, idleMs: 2500, focusedInteractive: false, boredAfterMs: 30000 }
  assert.equal(canOfferAutomaticFact(base), true)
  for (const change of [
    { hidden: true }, { focusedInteractive: true }, { idleMs: 2499 }, { idleMs: 30000 },
  ]) assert.equal(canOfferAutomaticFact({ ...base, ...change }), false)
  assert.equal(canOfferAutomaticFact({ ...base, boredAfterMs: 2000 }), false)
})
