// Vendored from @bible-strong/avatar-core runtime.ts (AGPL-3.0). TypeScript
// stripped; runtime behavior unchanged.
import { applyAmbientMotion } from './ambientMotion'
import { interpolatePose, poseFromExpression } from './geometry'
import { expressionFromDefinition, renderAvatarExpression } from './scene'

export const resolveExpression = (definition, key) => {
  const expression = definition.expressions[key]
  return expression
    ? { ok: true, value: expression }
    : {
        ok: false,
        error: { code: 'unknown_expression', key, message: `Unknown expression '${key}'` },
      }
}

export const resolveAnimation = (definition, key) => {
  const explicit = definition.animations[key]
  return explicit
    ? { ok: true, value: explicit }
    : {
        ok: false,
        error: { code: 'unknown_animation', key, message: `Unknown animation '${key}'` },
      }
}

export const createAvatarPlaybackState = () => ({
  activeExpression: 'neutral',
  status: 'stopped',
  stepIndex: 0,
  direction: 1,
  phase: 'transition',
  phaseStartedAt: 0,
  transitionFrom: 'neutral',
})

export const playAvatarAnimation = (definition, key, now, from) => {
  const result = resolveAnimation(definition, key)
  if (!result.ok) return result
  return {
    ok: true,
    value: {
      activeAnimation: key,
      activeExpression: result.value.steps[0]?.expression ?? 'neutral',
      status: 'playing',
      stepIndex: 0,
      direction: 1,
      phase: 'transition',
      phaseStartedAt: now,
      transitionFrom: 'neutral',
      ...(from ? { transitionSnapshot: from } : {}),
      blinkDueAt: now + result.value.blink.initialDelayMs,
    },
  }
}

const nextCursor = (animation, state) => {
  const last = animation.steps.length - 1
  if (state.stepIndex < last && state.direction === 1) {
    return { stepIndex: state.stepIndex + 1, direction: state.direction, complete: false }
  }
  if (state.stepIndex > 0 && state.direction === -1) {
    return { stepIndex: state.stepIndex - 1, direction: state.direction, complete: false }
  }
  if (animation.playbackMode === 'once') {
    return { stepIndex: state.stepIndex, direction: state.direction, complete: true }
  }
  if (animation.playbackMode === 'pingPong' && last > 0) {
    const direction = state.direction === 1 ? -1 : 1
    return { stepIndex: state.stepIndex + direction, direction, complete: false }
  }
  return { stepIndex: 0, direction: 1, complete: false }
}

export const advanceAvatarPlayback = (definition, state, now, environment) => {
  if (state.directTransition) {
    if (now < state.directTransition.startedAt + state.directTransition.durationMs) {
      return { ...state }
    }
    const { directTransition: _directTransition, ...next } = state
    return { ...next, status: 'stopped' }
  }
  if (state.status !== 'playing' || !state.activeAnimation) return { ...state }
  const resolved = resolveAnimation(definition, state.activeAnimation)
  if (!resolved.ok || !resolved.value.steps.length) return { ...createAvatarPlaybackState() }
  const animation = resolved.value
  let next = { ...state }
  if (animation.blink.enabled && next.blinkDueAt !== undefined && now >= next.blinkDueAt) {
    const startedAt = next.blinkDueAt
    const interval =
      animation.blink.minIntervalMs +
      Math.max(0, Math.min(1, environment.random())) *
        (animation.blink.maxIntervalMs - animation.blink.minIntervalMs)
    next.blinkStartedAt = startedAt
    next.blinkDueAt = startedAt + animation.blink.durationMs + interval
  }
  let safety = animation.steps.length * 4 + 4
  while (safety-- > 0) {
    const step = animation.steps[next.stepIndex]
    const duration = next.phase === 'transition' ? step.transitionMs : step.holdMs
    if (now < next.phaseStartedAt + duration) break
    next.phaseStartedAt += duration
    if (next.phase === 'transition') {
      next.phase = 'hold'
      next.activeExpression = step.expression
      continue
    }
    const cursor = nextCursor(animation, next)
    if (cursor.complete) {
      next.status = 'stopped'
      delete next.activeAnimation
      break
    }
    next.stepIndex = cursor.stepIndex
    next.direction = cursor.direction
    next.phase = 'transition'
    next.transitionFrom = next.activeExpression
    delete next.transitionSnapshot
    next.activeExpression = animation.steps[cursor.stepIndex].expression
  }
  return next
}

export const pauseAvatarPlayback = (state, now) =>
  state.status === 'playing' ? { ...state, status: 'paused', pausedAt: now } : { ...state }

export const resumeAvatarPlayback = (state, now) => {
  if (state.status !== 'paused' || state.pausedAt === undefined) return { ...state }
  const pauseDuration = now - state.pausedAt
  return {
    ...state,
    status: 'playing',
    phaseStartedAt: state.phaseStartedAt + pauseDuration,
    ...(state.directTransition
      ? {
          directTransition: {
            ...state.directTransition,
            startedAt: state.directTransition.startedAt + pauseDuration,
          },
        }
      : {}),
    ...(state.blinkDueAt === undefined ? {} : { blinkDueAt: state.blinkDueAt + pauseDuration }),
    ...(state.blinkStartedAt === undefined
      ? {}
      : { blinkStartedAt: state.blinkStartedAt + pauseDuration }),
    pausedAt: undefined,
  }
}

const easing = (transition, value) => {
  const progress = Math.max(0, Math.min(1, value))
  if (transition === 'smooth') return progress * progress * (3 - 2 * progress)
  if (transition === 'snappy') return 1 - (1 - progress) ** 3
  const end = 1 - Math.exp(-6) * Math.cos(8)
  return Math.max(0, Math.min(1, (1 - Math.exp(-6 * progress) * Math.cos(8 * progress)) / end))
}

const expressionColors = (definition, expression) => ({
  body: expression.colors?.body ?? definition.colors.body,
  eyes: expression.colors?.eyes ?? definition.colors.eyes,
})

const interpolateHexColor = (from, to, progress) => {
  const parse = color => {
    const value = color.slice(1)
    const expanded = value.length === 3 ? [...value].map(part => `${part}${part}`).join('') : value
    return [0, 2, 4].map(index => Number.parseInt(expanded.slice(index, index + 2), 16))
  }
  const source = parse(from)
  const target = parse(to)
  if (source.some(Number.isNaN) || target.some(Number.isNaN)) return progress < 1 ? from : to
  return `#${source
    .map((value, index) => Math.round(value + (target[index] - value) * progress))
    .map(value => value.toString(16).padStart(2, '0'))
    .join('')}`
}

const interpolateColors = (from, to, progress) => ({
  body: interpolateHexColor(from.body, to.body, progress),
  eyes: interpolateHexColor(from.eyes, to.eyes, progress),
})

export const blinkOpacityAt = (animation, state, now) => {
  if (!animation.blink.enabled || state.blinkStartedAt === undefined) return 1
  const progress = (now - state.blinkStartedAt) / animation.blink.durationMs
  if (progress < 0 || progress >= 1) return 1
  return Math.abs(progress * 2 - 1)
}

export const sampleAvatarFrame = (definition, state, now, environment) => {
  const sampledAt = state.status === 'paused' && state.pausedAt !== undefined ? state.pausedAt : now
  const targetDefinition = definition.expressions[state.activeExpression]
  if (!targetDefinition) {
    const neutral = definition.expressions.neutral
    return {
      expression: expressionFromDefinition('neutral', neutral),
      colors: expressionColors(definition, neutral),
      blink: 1,
      sampledAt,
    }
  }
  let expression = expressionFromDefinition(state.activeExpression, targetDefinition)
  let colors = expressionColors(definition, targetDefinition)
  let blink = 1
  if (state.directTransition && !environment.reduceMotion) {
    const progress = easing(
      state.directTransition.transition,
      (sampledAt - state.directTransition.startedAt) /
        Math.max(state.directTransition.durationMs, 1)
    )
    expression = interpolatePose(
      poseFromExpression(state.directTransition.from.expression),
      poseFromExpression(expression),
      progress
    ).expression
    colors = interpolateColors(state.directTransition.from.colors, colors, progress)
  } else if (state.activeAnimation) {
    const resolved = resolveAnimation(definition, state.activeAnimation)
    if (resolved.ok) {
      const step = resolved.value.steps[state.stepIndex]
      if (state.phase === 'transition' && step && !environment.reduceMotion) {
        const fromDefinition = definition.expressions[state.transitionFrom]
        const from =
          state.transitionSnapshot?.expression ??
          (fromDefinition
            ? expressionFromDefinition(state.transitionFrom, fromDefinition)
            : undefined)
        const fromColors =
          state.transitionSnapshot?.colors ??
          (fromDefinition ? expressionColors(definition, fromDefinition) : undefined)
        if (from && fromColors) {
          const duration = Math.max(step.transitionMs, 1)
          const progress = easing(step.transition, (sampledAt - state.phaseStartedAt) / duration)
          expression = interpolatePose(
            poseFromExpression(from),
            poseFromExpression(expression),
            progress
          ).expression
          colors = interpolateColors(fromColors, colors, progress)
        }
      }
      blink = blinkOpacityAt(resolved.value, state, sampledAt)
    }
  }
  return { expression, colors, blink, sampledAt }
}

export const renderAvatarFrame = (definition, state, now, environment) => {
  const frame = sampleAvatarFrame(definition, state, now, environment)
  const expression = environment.reduceMotion
    ? frame.expression
    : applyAmbientMotion(frame.expression, frame.sampledAt)
  return renderAvatarExpression(definition, expression, frame.colors, frame.blink)
}