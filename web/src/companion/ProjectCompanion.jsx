// Sunee, the project companion: a small fixed bottom-right mascot with a
// layered behavior system. All rules and copy live in companionConfig.js,
// facts in projectFacts.js, the avatar definition in sunee.avatar.json.
//
// Message priority (one bubble at a time): navigation > intro > manual click
// > random fact > inactivity. Higher priority preempts gracefully (the bubble
// swaps and the runtime transitions the avatar smoothly from its current
// pose). Every bubble has a close (x) button that only hides it - future
// messages are never disabled. Emotion tiers use animation only, no text.
//
// Behaviors that are approximated rather than natively supported by the
// Avatar Lab runtime are documented in companionConfig.js (tldr: the lab has
// no pointer/gaze tracking, so gaze-following maps cursor quadrants onto
// discrete lab glance expressions via setExpression()).
import { Component, useCallback, useEffect, useRef, useState } from 'react'
import Avatar from '../vendor/bible-strong/Avatar.jsx'
import sunee from './sunee.avatar.json'
import { buildFacts } from './projectFacts.js'
import {
  BUBBLE_MS,
  INTRO_BUBBLE_MS,
  INTRO_DELAY_MS,
  INTRO_KEY,
  MESSAGE_PRIORITY,
  introMessage,
  gazeConfig,
  inactivityConfig,
  sectionSummaries,
  factConfig,
} from './companionConfig.js'
import './companion.css'

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
  const hostRef = useRef(null)
  const [message, setMessage] = useState(null)
  const [bubbleKey, setBubbleKey] = useState(0)
  const prefersReducedMotion = usePrefersReducedMotion()

  // Refs the outside-of-render callbacks can read (timers, state mirrors).
  const messageRef = useRef(null)
  messageRef.current = message
  const hideTimerRef = useRef(null)
  const introTimerRef = useRef(null)
  const factTimerRef = useRef(null)
  const ladderTimerRef = useRef(null)
  const reactionTimerRef = useRef(null)
  const lingerTimerRef = useRef(null)
  const busyUntilRef = useRef(0)
  const navHoldUntilRef = useRef(0)
  const lastFactRef = useRef(null)
  const lastNavRef = useRef(null)
  const lastNavAtRef = useRef(0)
  const lastActivityRef = useRef(Date.now())
  const emotionRef = useRef(0) // 0 idle/engaged, 1 bored, 2 impatient, 3 angry
  const reactingRef = useRef(false)
  const cycleMessageShownRef = useRef(false)
  const gazeStateRef = useRef({ inRange: false, quadrant: null, lastSwitch: { x: 0, y: 0 } })

  // Re-assert whatever state the avatar should be in right now. Used after a
  // bubble hides or a gaze ends, so the emotion tier (or plain idle) resumes.
  const assertEmotion = useCallback(() => {
    const index = emotionRef.current
    avatarRef.current?.play(
      index === 0 ? 'idle' : inactivityConfig.tiers[index - 1].animation
    )
  }, [])

  const hideMessage = useCallback(() => {
    if (hideTimerRef.current) {
      window.clearTimeout(hideTimerRef.current)
      hideTimerRef.current = null
    }
    setMessage(null)
    assertEmotion()
  }, [assertEmotion])

  const showMessage = useCallback(
    (candidate, durationMs) => {
      const current = messageRef.current
      if (current && candidate.priority <= current.priority) return false
      if (hideTimerRef.current) {
        window.clearTimeout(hideTimerRef.current)
        hideTimerRef.current = null
      }
      setMessage(candidate)
      setBubbleKey((key) => key + 1)
      if (candidate.animation) avatarRef.current?.play(candidate.animation)
      hideTimerRef.current = window.setTimeout(
        hideMessage,
        durationMs ?? BUBBLE_MS
      )
      return true
    },
    [hideMessage]
  )

  const showFact = useCallback(
    (via) => {
      if (document.hidden) return
      if (via === 'manual' && Date.now() < busyUntilRef.current) return
      if (Date.now() < navHoldUntilRef.current) return
      let next = facts[Math.floor(Math.random() * facts.length)]
      if (facts.length > 1) {
        while (next === lastFactRef.current) {
          next = facts[Math.floor(Math.random() * facts.length)]
        }
      }
      lastFactRef.current = next
      busyUntilRef.current = Date.now() + factConfig.clickCooldownMs
      showMessage(
        {
          kind: 'fact',
          priority: MESSAGE_PRIORITY[via],
          animation: next.animation,
          text: next.text,
        },
        BUBBLE_MS
      )
    },
    [showMessage]
  )

  // ---- Initial introduction: ~3s after load, once per session ------------
  useEffect(() => {
    try {
      if (window.sessionStorage.getItem(INTRO_KEY)) return undefined
    } catch {
      return undefined
    }
    introTimerRef.current = window.setTimeout(() => {
      try {
        window.sessionStorage.setItem(INTRO_KEY, '1')
      } catch {
        // storage unavailable: still show it this once
      }
      showMessage({ ...introMessage, kind: 'intro' }, INTRO_BUBBLE_MS)
    }, INTRO_DELAY_MS)
    return () => window.clearTimeout(introTimerRef.current)
  }, [showMessage])

  // ---- Random fact scheduler: every 45-90s of active usage ---------------
  useEffect(() => {
    const schedule = () => {
      const multiplier = prefersReducedMotion
        ? factConfig.reducedMotionIntervalMultiplier
        : 1
      factTimerRef.current = window.setTimeout(() => {
        factTimerRef.current = null
        const current = messageRef.current
        if (!document.hidden && (!current || current.priority < MESSAGE_PRIORITY.fact)) {
          showFact('fact')
        }
        schedule()
      }, randBetween(factConfig.minIntervalMs * multiplier, factConfig.maxIntervalMs * multiplier))
    }
    schedule()
    return () => {
      if (factTimerRef.current) window.clearTimeout(factTimerRef.current)
    }
  }, [prefersReducedMotion, showFact])

  // ---- Page navigation reactions -----------------------------------------
  useEffect(() => {
    const onNav = (key) => {
      const summary = sectionSummaries[key]
      if (!summary) return
      const now = Date.now()
      if (key === lastNavRef.current && now - lastNavAtRef.current < 4_000) return
      lastNavRef.current = key
      lastNavAtRef.current = now
      navHoldUntilRef.current = now + factConfig.holdOffAfterNavMs
      lastActivityRef.current = now // navigating is activity
      showMessage({ kind: 'navigation', ...summary }, BUBBLE_MS)
    }
    const onHashChange = () => {
      const key = (window.location.hash || '').slice(1)
      if (key) onNav(key)
    }
    // The Simulator is an external link (target=_blank), so no hashchange
    // fires - catch the click on its anchor instead.
    const onDocClick = (event) => {
      const anchor = event.target?.closest?.('a[href*="streamlit"]')
      if (anchor) onNav('simulator')
    }
    window.addEventListener('hashchange', onHashChange)
    document.addEventListener('click', onDocClick)
    return () => {
      window.removeEventListener('hashchange', onHashChange)
      document.removeEventListener('click', onDocClick)
    }
  }, [showMessage])

  // ---- Inactivity emotion ladder (animation-only, gradual) ---------------
  useEffect(() => {
    const onActivity = () => {
      const idleMs = Date.now() - lastActivityRef.current
      lastActivityRef.current = Date.now()
      if (emotionRef.current === 0 || reactingRef.current) return
      // The user came back after the ladder had climbed: reset it and react.
      reactingRef.current = true
      emotionRef.current = 0
      cycleMessageShownRef.current = false
      const surprise = idleMs > inactivityConfig.surprisedReactionAfterMs
      if (!messageRef.current) {
        avatarRef.current?.play(surprise ? 'surprised' : 'happy')
        reactionTimerRef.current = window.setTimeout(() => {
          reactingRef.current = false
          if (emotionRef.current === 0 && !messageRef.current) {
            avatarRef.current?.play('idle')
          }
        }, inactivityConfig.reactionPlayMs)
      } else {
        // A bubble is showing; its animation carries the moment. Just yield.
        reactingRef.current = false
      }
    }
    const events = inactivityConfig.activityEvents
    events.forEach((event) =>
      window.addEventListener(event, onActivity, { passive: true })
    )
    return () =>
      events.forEach((event) => window.removeEventListener(event, onActivity))
  }, [])

  useEffect(() => {
    const tick = () => {
      const idleMs = Date.now() - lastActivityRef.current
      let target = 0
      for (let i = 0; i < inactivityConfig.tiers.length; i += 1) {
        if (idleMs >= inactivityConfig.tiers[i].afterMs) target = i + 1
      }
      if (target <= emotionRef.current) return
      // Climb at most one tier per check: gradual, never a jump to angry.
      emotionRef.current = Math.min(emotionRef.current + 1, target)
      const tier = inactivityConfig.tiers[emotionRef.current - 1]
      if (!messageRef.current) {
        avatarRef.current?.play(tier.animation)
      }
      // One low-priority bubble per boredom cycle, only at the final tier.
      if (tier.key === 'angry' && !cycleMessageShownRef.current) {
        cycleMessageShownRef.current = true
        showMessage(
          {
            kind: 'inactivity',
            priority: MESSAGE_PRIORITY.inactivity,
            animation: tier.animation,
            text: inactivityConfig.inactivityMessage.text,
          },
          BUBBLE_MS
        )
      }
    }
    ladderTimerRef.current = window.setInterval(tick, inactivityConfig.checkIntervalMs)
    return () => window.clearInterval(ladderTimerRef.current)
  }, [showMessage])

  // ---- Cursor gaze (approximated: lab has no pointer-tracking API) -------
  useEffect(() => {
    if (prefersReducedMotion || !gazeConfig.enabled) return undefined
    let lastEval = 0
    const evaluate = (event) => {
      const now = Date.now()
      if (now - lastEval < gazeConfig.throttleMs) return
      lastEval = now
      const host = hostRef.current
      if (!host || emotionRef.current > 0 || messageRef.current || reactingRef.current) {
        return
      }
      const rect = host.getBoundingClientRect()
      const cx = rect.left + rect.width / 2
      const cy = rect.top + rect.height / 2
      const dx = event.clientX - cx
      const dy = event.clientY - cy
      const state = gazeStateRef.current
      if (Math.hypot(dx, dy) > gazeConfig.rangePx) {
        if (state.inRange) {
          state.inRange = false
          state.quadrant = null
          assertEmotion()
        }
        return
      }
      const useX = Math.abs(dx) >= Math.abs(dy)
      const quadrant = useX ? (dx > 0 ? 'right' : 'left') : (dy > 0 ? 'down' : 'up')
      const movedEnough =
        Math.hypot(dx - state.lastSwitch.x, dy - state.lastSwitch.y) >=
        gazeConfig.hysteresisPx
      if (!state.inRange || (quadrant !== state.quadrant && movedEnough)) {
        state.inRange = true
        state.quadrant = quadrant
        state.lastSwitch = { x: dx, y: dy }
        avatarRef.current?.setExpression(gazeConfig.quadrantExpressions[quadrant])
      }
      // Look away (back to the idle loop) once the cursor lingers.
      if (lingerTimerRef.current) window.clearTimeout(lingerTimerRef.current)
      lingerTimerRef.current = window.setTimeout(() => {
        if (state.inRange && !messageRef.current && emotionRef.current === 0) {
          assertEmotion()
        }
      }, gazeConfig.lingerMs)
    }
    window.addEventListener('mousemove', evaluate)
    return () => {
      window.removeEventListener('mousemove', evaluate)
      if (lingerTimerRef.current) window.clearTimeout(lingerTimerRef.current)
    }
  }, [prefersReducedMotion, assertEmotion])

  // ---- Full cleanup -------------------------------------------------------
  useEffect(
    () => () => {
      const timers = [
        hideTimerRef.current,
        introTimerRef.current,
        factTimerRef.current,
        ladderTimerRef.current,
        reactionTimerRef.current,
        lingerTimerRef.current,
      ]
      timers.forEach((timer) => timer !== null && window.clearTimeout(timer))
    },
    []
  )

  const handleClick = useCallback(() => {
    if (!document.hidden) showFact('manual')
  }, [showFact])

  return (
    <CompanionErrorBoundary>
      <div className="project-companion">
        {message ? (
          <div
            className="companion-bubble"
            key={bubbleKey}
            role="status"
            aria-live="polite"
          >
            <span className="companion-bubble-text">{message.text}</span>
            <button
              type="button"
              className="companion-bubble-close"
              onClick={hideMessage}
              aria-label="Dismiss message"
              title="Dismiss"
            >
              ×
            </button>
          </div>
        ) : null}
        <div ref={hostRef}>
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
      </div>
    </CompanionErrorBoundary>
  )
}

export default ProjectCompanion