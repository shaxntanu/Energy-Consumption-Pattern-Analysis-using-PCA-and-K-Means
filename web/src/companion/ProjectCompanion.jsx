// Sunee, the project companion: a small fixed bottom-right mascot that mostly
// idles, occasionally pops a short fact from projectFacts.js, and says one on
// click. Fully isolated so removing this file (plus the mount in main.jsx)
// restores the app exactly as it was. If anything goes wrong the error
// boundary renders null and the rest of the app is untouched.
import { Component, useCallback, useEffect, useRef, useState } from 'react'
import Avatar from '../vendor/bible-strong/Avatar.jsx'
import sunee from './sunee.avatar.json'
import { buildFacts } from './projectFacts.js'
import './companion.css'

const AUTO_MIN_MS = 30_000
const AUTO_MAX_MS = 60_000
const BUBBLE_MS = 6_500
const CLICK_COOLDOWN_MS = 10_000

const facts = buildFacts()

const randBetween = (min, max) => Math.floor(min + Math.random() * (max - min))

class CompanionErrorBoundary extends Component {
  constructor(props) {
    super(props)
    this.state = { failed: false }
  }
  static getDerivedStateFromError() {
    return { failed: true }
  }
  render() {
    return this.state.failed ? null : this.props.children
  }
}

const usePrefersReducedMotion = () => {
  const [reduced, setReduced] = useState(
    () =>
      typeof window.matchMedia === 'function' &&
      window.matchMedia('(prefers-reduced-motion: reduce)').matches
  )
  useEffect(() => {
    if (typeof window.matchMedia !== 'function') return undefined
    const media = window.matchMedia('(prefers-reduced-motion: reduce)')
    const onChange = (event) => setReduced(event.matches)
    media.addEventListener?.('change', onChange)
    return () => media.removeEventListener?.('change', onChange)
  }, [])
  return reduced
}

function ProjectCompanion() {
  if (facts.length === 0) return null

  const avatarRef = useRef(null)
  const busyUntilRef = useRef(0)
  const lastFactRef = useRef(null)
  const timerRef = useRef(null)
  const hideTimerRef = useRef(null)
  const [fact, setFact] = useState(null)
  const [bubbleKey, setBubbleKey] = useState(0)
  const prefersReducedMotion = usePrefersReducedMotion()

  const showFact = useCallback(() => {
    if (document.hidden || Date.now() < busyUntilRef.current) return
    let next = facts[Math.floor(Math.random() * facts.length)]
    if (facts.length > 1) {
      while (next === lastFactRef.current) {
        next = facts[Math.floor(Math.random() * facts.length)]
      }
    }
    lastFactRef.current = next
    busyUntilRef.current = Date.now() + CLICK_COOLDOWN_MS
    if (hideTimerRef.current) window.clearTimeout(hideTimerRef.current)
    setFact(next)
    setBubbleKey((key) => key + 1)
    avatarRef.current?.play(next.animation)
    hideTimerRef.current = window.setTimeout(() => {
      hideTimerRef.current = null
      setFact(null)
      avatarRef.current?.play('idle')
    }, BUBBLE_MS)
  }, [])

  useEffect(() => {
    const schedule = () => {
      // People who ask for reduced motion see facts half as often too.
      const multiplier = prefersReducedMotion ? 2 : 1
      timerRef.current = window.setTimeout(() => {
        timerRef.current = null
        showFact()
        schedule()
      }, randBetween(AUTO_MIN_MS * multiplier, AUTO_MAX_MS * multiplier))
    }
    schedule()
    return () => {
      if (timerRef.current) window.clearTimeout(timerRef.current)
      if (hideTimerRef.current) window.clearTimeout(hideTimerRef.current)
    }
  }, [prefersReducedMotion, showFact])

  const handleClick = useCallback(() => {
    if (!document.hidden) showFact()
  }, [showFact])

  return (
    <CompanionErrorBoundary>
      <div className="project-companion">
        {fact ? (
          <div
            className="companion-bubble"
            key={bubbleKey}
            role="status"
            aria-live="polite"
          >
            {fact.text}
          </div>
        ) : null}
        <button
          type="button"
          className="companion-avatar-button"
          onClick={handleClick}
          aria-label="Ask Sunee for a project fact"
          title="Ask Sunee for a project fact"
        >
          <Avatar
            ref={avatarRef}
            definition={sunee}
            defaultAnimation="idle"
            autoplay
            size={96}
            ariaLabel="Sunee, the project companion"
          />
        </button>
      </div>
    </CompanionErrorBoundary>
  )
}

export default ProjectCompanion
