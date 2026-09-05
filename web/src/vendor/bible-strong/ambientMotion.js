// Vendored from @bible-strong/avatar-core ambientMotion.ts (AGPL-3.0).
// TypeScript stripped; runtime behavior unchanged.
export const eyeMotionModes = ['none', 'microSaccades', 'shake']
export const bodyMotionModes = ['none', 'slowDrift', 'shake']
const eyeMotionSet = new Set(eyeMotionModes)
const bodyMotionSet = new Set(bodyMotionModes)
export const isEyeMotion = value => typeof value === 'string' && eyeMotionSet.has(value)
export const isBodyMotion = value => typeof value === 'string' && bodyMotionSet.has(value)

const smoothstep = value => value * value * (3 - 2 * value)
const hash = value => {
  const raw = Math.sin(value * 127.1 + 311.7) * 43758.5453
  return (raw - Math.floor(raw)) * 2 - 1
}

const expressionSeed = expression =>
  expression.headX * 0.71 + expression.headY * 1.13 + expression.headZ * 1.37
const EYE_MOTION_SEED = 17.29

const smoothNoise = (elapsedMs, axis, seed, interval) => {
  const progress = elapsedMs / interval
  const step = Math.floor(progress)
  const blend = smoothstep(progress - step)
  const previous = hash(step * 3 + axis + seed)
  const next = hash((step + 1) * 3 + axis + seed)
  return previous + (next - previous) * blend
}

const saccade = (elapsedMs, axis, seed) => {
  const interval = 1100
  const duration = 140
  if (elapsedMs <= 0) return 0
  const step = Math.floor(elapsedMs / interval)
  const progress = (elapsedMs - step * interval) / duration
  const blend = smoothstep(Math.min(progress, 1))
  const previous = step === 0 ? 0 : hash((step - 1) * 2 + axis + seed)
  const next = hash(step * 2 + axis + seed)
  return previous + (next - previous) * blend
}

export const hasAmbientMotion = expression =>
  expression.eyeMotion !== 'none' || expression.bodyMotion !== 'none'

export const ambientBodyOffset = (expression, elapsedMs, strength = 1) => {
  const seed = expressionSeed(expression)
  if (expression.bodyMotion === 'slowDrift') {
    return {
      x: smoothNoise(elapsedMs, 3, seed, 2900) * 1.45 * strength,
      y: smoothNoise(elapsedMs, 4, seed, 3700) * 1.1 * strength,
    }
  }
  if (expression.bodyMotion === 'shake') {
    const time = elapsedMs / 1000
    return {
      x: (Math.sin(time * 31) + Math.sin(time * 53) * 0.45) * 1.35 * strength,
      y: (Math.sin(time * 37) + Math.sin(time * 61) * 0.4) * 1.1 * strength,
    }
  }
  return { x: 0, y: 0 }
}

export const ambientEyeOffset = (expression, elapsedMs, strength = 1) => {
  if (expression.eyeMotion === 'microSaccades') {
    return {
      x: saccade(elapsedMs, 0, EYE_MOTION_SEED) * 1.5 * strength,
      y: saccade(elapsedMs, 1, EYE_MOTION_SEED) * 0.9 * strength,
    }
  }
  if (expression.eyeMotion === 'shake') {
    const time = elapsedMs / 1000
    return {
      x: (Math.sin(time * 47) + Math.sin(time * 71) * 0.45) * 1.2 * strength,
      y: (Math.sin(time * 59) + Math.sin(time * 83) * 0.4) * 0.8 * strength,
    }
  }
  return { x: 0, y: 0 }
}

export const applyAmbientBodyMotion = (expression, elapsedMs, strength = 1) => {
  const next = { ...expression }
  const seed = expressionSeed(expression)

  if (expression.bodyMotion === 'slowDrift') {
    next.headX += smoothNoise(elapsedMs, 0, seed, 2600) * 0.8 * strength
    next.headY += smoothNoise(elapsedMs, 1, seed, 3300) * 1.15 * strength
    next.headZ += smoothNoise(elapsedMs, 2, seed, 4100) * 0.45 * strength
  } else if (expression.bodyMotion === 'shake') {
    const time = elapsedMs / 1000
    next.headX += (Math.sin(time * 31) + Math.sin(time * 53) * 0.45) * 1.15 * strength
    next.headY += (Math.sin(time * 37) + Math.sin(time * 61) * 0.4) * 1.35 * strength
    next.headZ += Math.sin(time * 43) * 0.7 * strength
  }

  return next
}

export const applyAmbientMotion = (expression, elapsedMs, strength = 1) => {
  const next = applyAmbientBodyMotion(expression, elapsedMs, strength)
  const eyeOffset = ambientEyeOffset(expression, elapsedMs, strength)
  next.positionXLeft += eyeOffset.x
  next.positionXRight += eyeOffset.x
  next.positionYLeft += eyeOffset.y
  next.positionYRight += eyeOffset.y
  return next
}