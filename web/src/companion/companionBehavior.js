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

export function canOfferAutomaticFact({ hidden, idleMs, focusedInteractive }) {
  // Offer facts only after a short pause, never during input or a bored cycle.
  return !hidden && !focusedInteractive && idleMs >= 2500 && idleMs < 30000
}
