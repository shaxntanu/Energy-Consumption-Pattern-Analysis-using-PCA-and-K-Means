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
// no pointer/gaze tracking, so gaze-following is a continuous pose field: a
// rAF loop eases the cursor position and writes a blended pose into the
// 'gaze-live' expression slot, which the 'gaze-follow' hold loop keeps on
// screen - any cursor angle, blended from the nearest lab glances).
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
  const busyUntilRef = useRef(0)
  const navHoldUntilRef = useRef(0)
  const lastFactRef = useRef(null)
  const lastNavRef = useRef(null)
  const lastNavAtRef = useRef(0)
  const lastActivityRef = useRef(Date.now())
  const emotionRef = useRef(0) // 0 idle/engaged, 1 bored, 2 impatient, 3 angry
  const reactingRef = useRef(false)
  const cycleMessageShownRef = useRef(false)
  const gazeRef = useRef(null)

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

  // ---- Cursor gaze (continuous, approximated: lab has no tracking API) ----
  // While the cursor is near, a rAF loop eases the cursor's normalized
  // position toward its latest target and writes a blended pose into the
  // 'gaze-live' slot of the definition. The vendored runtime samples that
  // object live every frame and the 'gaze-follow' loop animation keeps its
  // paint loop running, so any cursor angle becomes a continuous blend of the
  // two nearest real lab glance expressions, scaled by distance toward
  // neutral - theoretically infinite degrees of freedom, no discrete steps.
  useEffect(() => {
    if (prefersReducedMotion || !gazeConfig.enabled) return undefined
    const DIRS = { up: [0, -1], down: [0, 1], left: [-1, 0], right: [1, 0] }
    const slot = sunee.expressions['gaze-live']
    const neutral = sunee.expressions.neutral
    const guides = Object.entries(gazeConfig.guides).map(([key, exprKey]) => ({
      key,
      dir: DIRS[key],
      pose: sunee.expressions[exprKey],
    }))
    const blink = gazeConfig.blink
    const lerp = (a, b, t) => a + (b - a) * t
    const clamp = (value, min, max) => Math.min(max, Math.max(min, value))
    const state = {
      on: false,
      armed: false,
      raf: 0,
      lastEval: 0,
      lastMoveAt: 0,
      target: { x: 0, y: 0 },
      u: 0,
      v: 0,
      t: 0,
      nextBlinkAt: 0,
      blinkUntil: 0,
    }
    gazeRef.current = state
    const start = () => {
      if (!state.on) {
        state.on = true
        state.raf = requestAnimationFrame(tick)
      }
    }
    const stop = () => {
      if (state.on) {
        state.on = false
        cancelAnimationFrame(state.raf)
      }
    }
    const tick = () => {
      state.raf = requestAnimationFrame(tick)
      const now = performance.now()
      const suppressed = Boolean(
        messageRef.current || emotionRef.current > 0 || reactingRef.current
      )
      const active =
        !suppressed && state.armed && now - state.lastMoveAt <= gazeConfig.steadyMs
      const wantT = active
        ? clamp(Math.hypot(state.target.x, state.target.y) / gazeConfig.rangePx, 0, 1)
        : 0
      const wantU = active ? clamp(state.target.x / gazeConfig.rangePx, -1, 1) : 0
      const wantV = active ? clamp(state.target.y / gazeConfig.rangePx, -1, 1) : 0
      state.t += (wantT - state.t) * gazeConfig.easeFactor
      state.u += (wantU - state.u) * gazeConfig.easeFactor
      state.v += (wantV - state.v) * gazeConfig.easeFactor

      // Autonomous micro-blink (the gaze hold disables the animation blink).
      if (now >= state.nextBlinkAt) {
        state.nextBlinkAt = now + randBetween(blink.minMs, blink.maxMs)
        state.blinkUntil = now + blink.durationMs
      }
      const blinking = now < state.blinkUntil

      // Converged on neutral: the avatar may resume its idle loop.
      if (state.t < 0.015 && Math.abs(state.u) < 0.02 && Math.abs(state.v) < 0.02) {
        writePose(0, null, blinking)
        if (
          !active &&
          !suppressed &&
          !messageRef.current &&
          emotionRef.current === 0
        ) {
          stop()
          state.armed = false
          avatarRef.current?.play('idle')
        }
        return
      }

      // Angular kernels over the four guide glances (weight by how closely
      // the eased cursor direction matches each guide's axis).
      const weights = {}
      let weightTotal = 0
      for (const guide of guides) {
        const w = clamp(state.u * guide.dir[0] + state.v * guide.dir[1], 0, 1)
        weights[guide.key] = w
        weightTotal += w
      }
      const mixes = weightTotal > 1e-6 ? weights : null
      writePose(state.t, mixes, blinking)
    }
    // Blend the current cursor pose into the definition slot. mixes carries
    // the per-guide angular weights (already eased); t scales the whole gaze
    // by cursor distance (0 = pure neutral). While blinking, eye heights dip.
    const writePose = (t, mixes, blinking) => {
      const nEyes = neutral.eyes
      const nL = nEyes.left
      const nR = nEyes.right
      const blend = { hx: 0, hy: 0, hz: 0, wL: 0, hL: 0, xL: 0, yL: 0, aL: 0, wR: 0, hR: 0, xR: 0, yR: 0, aR: 0, sp: 0 }
      let total = 0
      if (mixes) {
        for (const guide of guides) {
          const weight = mixes[guide.key]
          if (weight <= 0) continue
          total += weight
          const pose = guide.pose
          const l = pose.eyes.left
          const r = pose.eyes.right
          blend.hx += weight * pose.head.x
          blend.hy += weight * pose.head.y
          blend.hz += weight * pose.head.z
          blend.wL += weight * l.width
          blend.hL += weight * l.height
          blend.xL += weight * l.x
          blend.yL += weight * l.y
          blend.aL += weight * l.angle
          blend.wR += weight * r.width
          blend.hR += weight * r.height
          blend.xR += weight * r.x
          blend.yR += weight * r.y
          blend.aR += weight * r.angle
          blend.sp += weight * pose.eyes.spacing
        }
        if (total > 0) {
          const inv = 1 / total
          for (const key of Object.keys(blend)) blend[key] *= inv
        }
      }
      const hasBlend = total > 0
      slot.head.x = lerp(neutral.head.x, blend.hx, t)
      slot.head.y = lerp(neutral.head.y, blend.hy, t)
      slot.head.z = lerp(neutral.head.z, blend.hz, t)
      slot.eyes.left.width = lerp(nL.width, blend.wL, t * Number(hasBlend))
      slot.eyes.left.height = lerp(nL.height, blend.hL, t * Number(hasBlend))
      slot.eyes.left.x = lerp(nL.x, blend.xL, t * Number(hasBlend))
      slot.eyes.left.y = lerp(nL.y, blend.yL, t * Number(hasBlend))
      slot.eyes.left.angle = lerp(nL.angle, blend.aL, t * Number(hasBlend))
      slot.eyes.right.width = lerp(nR.width, blend.wR, t * Number(hasBlend))
      slot.eyes.right.height = lerp(nR.height, blend.hR, t * Number(hasBlend))
      slot.eyes.right.x = lerp(nR.x, blend.xR, t * Number(hasBlend))
      slot.eyes.right.y = lerp(nR.y, blend.yR, t * Number(hasBlend))
      slot.eyes.right.angle = lerp(nR.angle, blend.aR, t * Number(hasBlend))
      slot.eyes.spacing = lerp(nEyes.spacing, blend.sp, t * Number(hasBlend))
      if (blinking) {
        const progress =
          (performance.now() - (state.blinkUntil - blink.durationMs)) / blink.durationMs
        const dip = Math.sin(Math.PI * clamp(progress, 0, 1))
        slot.eyes.left.height = lerp(slot.eyes.left.height, 14, dip)
        slot.eyes.right.height = lerp(slot.eyes.right.height, 14, dip)
      }
    }
    const onMove = (event) => {
      const now = performance.now()
      if (now - state.lastEval < gazeConfig.throttleMs) return
      state.lastEval = now
      if (messageRef.current || emotionRef.current > 0 || reactingRef.current) return
      const host = hostRef.current
      if (!host) return
      const rect = host.getBoundingClientRect()
      state.target.x = event.clientX - (rect.left + rect.width / 2)
      state.target.y = event.clientY - (rect.top + rect.height / 2)
      state.lastMoveAt = now
      if (Math.hypot(state.target.x, state.target.y) > gazeConfig.rangePx) {
        state.armed = false
        return
      }
      if (!state.armed) {
        state.armed = true
        avatarRef.current?.play('gaze-follow')
        start()
      }
    }
    window.addEventListener('mousemove', onMove)
    return () => {
      window.removeEventListener('mousemove', onMove)
      stop()
    }
  }, [prefersReducedMotion])

  // ---- Full cleanup -------------------------------------------------------
  useEffect(
    () => () => {
      const timers = [
        hideTimerRef.current,
        introTimerRef.current,
        factTimerRef.current,
        ladderTimerRef.current,
        reactionTimerRef.current,
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