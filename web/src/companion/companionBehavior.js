// Pure arbitration rules shared by the component and dependency-free tests.
export function canReplaceMessage(current, candidate) {
  if (!current) return true
  if (candidate.priority > current.priority) return true
  return candidate.kind === 'navigation' && current.kind === 'navigation'
    && candidate.priority === current.priority && candidate.text !== current.text
}

export function nextFactIndex(previous, count) {
  return count > 0 ? (previous + 1) % count : -1
}

export function canOfferAutomaticFact({ hidden, idleMs, focusedInteractive, boredAfterMs }) {
  // Offer facts after a short pause, never during input or a bored cycle.
  // The boredom boundary comes from the existing inactivity configuration.
  const quietMs = 2500
  return !hidden && !focusedInteractive && idleMs >= quietMs && idleMs < boredAfterMs
}
