// Dependency-free replacement for avatarDefinition.ts's ajv-based validation.
// Mirrors the original's inspectMaterializedValue + semanticErrors checks so a
// vendored avatar definition gets the same safety guarantees without pulling
// in ajv and the JSON schema.
import { bodyPrimitiveTypes } from './body'
import { surfacePresets } from './surfaces'

export const AVATAR_DEFINITION_MAX_DEPTH = 32
export const SEMANTIC_KEY_PATTERN = /^[a-z][a-z0-9]*(?:-[a-z0-9]+)*$/
const HEX_COLOR = /^#[0-9a-f]{3}(?:[0-9a-f]{3})?$/i
const PLAYBACK_MODES = new Set(['loop', 'once', 'pingPong'])
const TRANSITIONS = new Set(['spring', 'smooth', 'snappy'])
const EYE_MOTIONS = new Set(['none', 'microSaccades', 'shake'])
const BODY_MOTIONS = new Set(['none', 'slowDrift', 'shake'])

export const getSemanticKeyIssue = (semanticKey, kind) => {
  if (!semanticKey) return 'missing_semantic_key'
  if (!SEMANTIC_KEY_PATTERN.test(semanticKey) || semanticKey.length > 64) {
    return 'invalid_semantic_key'
  }
  if (kind === 'expression' && semanticKey === 'neutral') return 'reserved_semantic_key'
  return undefined
}

const escapePointer = (value) => value.replaceAll('~', '~0').replaceAll('/', '~1')
const childPointer = (path, segment) => `${path}/${escapePointer(String(segment))}`

const error = (path, code, message) => ({ path, code, message })

const inspectMaterializedValue = (value) => {
  const errors = []
  const ancestors = new WeakSet()

  const visit = (current, path) => {
    if (typeof current === 'number' && !Number.isFinite(current)) {
      errors.push(error(path, 'non_finite_number', 'Number must be finite'))
      return
    }
    if (current === null || typeof current !== 'object') return
    if (ancestors.has(current)) {
      errors.push(error(path, 'cyclic_value', 'Avatar definition must not be cyclic'))
      return
    }
    ancestors.add(current)
    if (!Array.isArray(current)) {
      const prototype = Object.getPrototypeOf(current)
      if (prototype !== Object.prototype && prototype !== null) {
        errors.push(error(path, 'non_plain_object', 'Expected a plain object'))
        ancestors.delete(current)
        return
      }
    }
    Object.entries(current).forEach(([key, child]) => visit(child, childPointer(path, key)))
    ancestors.delete(current)
  }

  visit(value, '')
  return errors
}

const isFiniteNumber = (value) => typeof value === 'number' && Number.isFinite(value)
const isHexColor = (value) => typeof value === 'string' && HEX_COLOR.test(value)
// The JSON schema's semanticKey rule is pattern-only; 'neutral' is a valid
// (required) expression key, so the reserved-key check is not applied here.
const isValidSemanticKey = (key) =>
  typeof key === 'string' && SEMANTIC_KEY_PATTERN.test(key) && key.length <= 64

const checkSurface = (surface, path, allowedTypes) => {
  const errors = []
  if (!surface || typeof surface !== 'object') {
    errors.push(error(path, 'surface_required', 'Surface config is required'))
    return errors
  }
  if (!allowedTypes.includes(surface.type)) {
    errors.push(error(path, 'type_required', `Surface type must be one of: ${allowedTypes.join(', ')}`))
  }
  for (const field of ['width', 'height', 'depth', 'roundness']) {
    if (!isFiniteNumber(surface[field])) {
      errors.push(error(childPointer(path, field), 'type', 'must be number'))
    }
  }
  for (const field of ['morphRoundness', 'tipRoundness', 'baseRoundness']) {
    if (surface[field] !== undefined && !isFiniteNumber(surface[field])) {
      errors.push(error(childPointer(path, field), 'type', 'must be number'))
    }
  }
  return errors
}

const checkBody = (body, path) => {
  const errors = []
  if (!body || typeof body !== 'object') {
    errors.push(error(path, 'body_required', `must have required property 'body'`))
    return errors
  }
  errors.push(...checkSurface(body.primary, childPointer(path, 'primary'), Object.keys(surfacePresets)))
  if (!Array.isArray(body.nodes)) {
    errors.push(error(childPointer(path, 'nodes'), 'type', 'must be array'))
    return errors
  }
  body.nodes.forEach((node, index) => {
    const nodePath = childPointer(childPointer(path, 'nodes'), index)
    if (!node || typeof node !== 'object') {
      errors.push(error(nodePath, 'type', 'must be object'))
      return
    }
    errors.push(...checkSurface(node.surface, childPointer(nodePath, 'surface'), bodyPrimitiveTypes))
    for (const field of ['position', 'rotation']) {
      const vector = node[field]
      if (!Array.isArray(vector) || vector.length !== 3 || !vector.every(isFiniteNumber)) {
        errors.push(error(childPointer(nodePath, field), 'type', 'must be array of 3 finite numbers'))
      }
    }
  })
  return errors
}

const checkExpression = (expression, path) => {
  const errors = []
  for (const field of ['perspective']) {
    if (!isFiniteNumber(expression[field])) {
      errors.push(error(childPointer(path, field), 'type', 'must be number'))
    }
  }
  for (const group of ['head', 'motion']) {
    if (!expression[group] || typeof expression[group] !== 'object') {
      errors.push(error(childPointer(path, group), 'type', 'must be object'))
      continue
    }
    if (group === 'head') {
      for (const axis of ['x', 'y', 'z']) {
        if (!isFiniteNumber(expression.head[axis])) {
          errors.push(error(childPointer(childPointer(path, 'head'), axis), 'type', 'must be number'))
        }
      }
    } else {
      if (!EYE_MOTIONS.has(expression.motion.eyes)) {
        errors.push(error(childPointer(childPointer(path, 'motion'), 'eyes'), 'enum', 'must be one of: none, microSaccades, shake'))
      }
      if (!BODY_MOTIONS.has(expression.motion.body)) {
        errors.push(error(childPointer(childPointer(path, 'motion'), 'body'), 'enum', 'must be one of: none, slowDrift, shake'))
      }
    }
  }
  const eyes = expression.eyes
  if (!eyes || typeof eyes !== 'object') {
    errors.push(error(childPointer(path, 'eyes'), 'type', 'must be object'))
    return errors
  }
  if (!isFiniteNumber(eyes.spacing)) {
    errors.push(error(childPointer(childPointer(path, 'eyes'), 'spacing'), 'type', 'must be number'))
  }
  for (const side of ['left', 'right']) {
    const eye = eyes[side]
    const eyePath = childPointer(childPointer(path, 'eyes'), side)
    if (!eye || typeof eye !== 'object') {
      errors.push(error(eyePath, 'type', 'must be object'))
      continue
    }
    for (const field of ['width', 'height', 'x', 'y', 'angle']) {
      if (!isFiniteNumber(eye[field])) {
        errors.push(error(childPointer(eyePath, field), 'type', 'must be number'))
      }
    }
  }
  if (expression.colors !== undefined) {
    if (expression.colors.body !== undefined && !isHexColor(expression.colors.body)) {
      errors.push(error(childPointer(childPointer(path, 'colors'), 'body'), 'pattern', 'must match pattern "#rrggbb"'))
    }
    if (expression.colors.eyes !== undefined && !isHexColor(expression.colors.eyes)) {
      errors.push(error(childPointer(childPointer(path, 'colors'), 'eyes'), 'pattern', 'must match pattern "#rrggbb"'))
    }
  }
  return errors
}

const checkAnimation = (animation, path) => {
  const errors = []
  if (!PLAYBACK_MODES.has(animation.playbackMode)) {
    errors.push(error(childPointer(path, 'playbackMode'), 'enum', 'must be one of: loop, once, pingPong'))
  }
  if (!Array.isArray(animation.steps) || animation.steps.length === 0) {
    errors.push(error(childPointer(path, 'steps'), 'minItems', 'must NOT have fewer than 1 items'))
    return errors
  }
  animation.steps.forEach((step, index) => {
    const stepPath = childPointer(childPointer(path, 'steps'), index)
    for (const field of ['holdMs', 'transitionMs']) {
      if (!isFiniteNumber(step[field])) {
        errors.push(error(childPointer(stepPath, field), 'type', 'must be number'))
      }
    }
    if (typeof step.expression !== 'string') {
      errors.push(error(childPointer(stepPath, 'expression'), 'type', 'must be string'))
    }
    if (!TRANSITIONS.has(step.transition)) {
      errors.push(error(childPointer(stepPath, 'transition'), 'enum', 'must be one of: spring, smooth, snappy'))
    }
  })
  const blink = animation.blink
  if (!blink || typeof blink !== 'object') {
    errors.push(error(childPointer(path, 'blink'), 'type', 'must be object'))
    return errors
  }
  for (const field of ['enabled']) {
    if (typeof blink[field] !== 'boolean') {
      errors.push(error(childPointer(childPointer(path, 'blink'), field), 'type', 'must be boolean'))
    }
  }
  for (const field of ['initialDelayMs', 'minIntervalMs', 'maxIntervalMs', 'durationMs']) {
    if (!isFiniteNumber(blink[field])) {
      errors.push(error(childPointer(childPointer(path, 'blink'), field), 'type', 'must be number'))
    }
  }
  return errors
}

const semanticErrors = (definition) => {
  const errors = []
  const expressionKeys = Object.keys(definition.expressions)
  const animationKeys = Object.keys(definition.animations)

  const checkCompleteOrder = (order, keys, path) => {
    const ordered = new Set(order)
    const knownKeys = new Set(keys)
    keys.forEach(key => {
      if (!ordered.has(key)) errors.push(error(path, 'incomplete_order', `Order is missing key '${key}'`))
    })
    order.forEach((key, index) => {
      if (!knownKeys.has(key)) {
        errors.push(error(childPointer(path, index), 'unknown_order_key', `Unknown key '${key}'`))
      }
    })
  }

  checkCompleteOrder(definition.expressionOrder, expressionKeys, '/expressionOrder')
  checkCompleteOrder(definition.animationOrder, animationKeys, '/animationOrder')
  if (definition.expressionOrder[0] !== 'neutral') {
    errors.push(error('/expressionOrder/0', 'neutral_not_first', "'neutral' must be the first expression-order entry"))
  }
  Object.entries(definition.animations).forEach(([animationKey, animation]) => {
    if (animation.blink.minIntervalMs > animation.blink.maxIntervalMs) {
      errors.push(
        error(
          `/animations/${escapePointer(animationKey)}/blink/minIntervalMs`,
          'invalid_interval_range',
          'minIntervalMs must be less than or equal to maxIntervalMs'
        )
      )
    }
    animation.steps.forEach((step, index) => {
      if (!(step.expression in definition.expressions)) {
        errors.push(
          error(
            `/animations/${escapePointer(animationKey)}/steps/${index}/expression`,
            'unknown_expression',
            `Unknown expression '${step.expression}'`
          )
        )
      }
    })
  })
  return errors
}

const inspectSchemaShape = (value) => {
  const errors = []
  if (!value || typeof value !== 'object') {
    return [error('', 'type', 'Avatar definition must be an object')]
  }
  if (typeof value.schema !== 'string' || value.schema !== 'bible-strong/avatar-definition') {
    errors.push(error('/schema', 'const', 'must be equal to the constant "bible-strong/avatar-definition"'))
  }
  if (value.schemaVersion !== 1) {
    errors.push(error('/schemaVersion', 'const', 'must be equal to the constant 1'))
  }
  if (value.name !== undefined && typeof value.name !== 'string') {
    errors.push(error('/name', 'type', 'must be string'))
  }
  if (!value.colors || typeof value.colors !== 'object') {
    errors.push(error('/colors', 'required', `must have required property 'colors'`))
  } else {
    if (!isHexColor(value.colors.body)) {
      errors.push(error('/colors/body', 'pattern', 'must match pattern "#rrggbb"'))
    }
    if (!isHexColor(value.colors.eyes)) {
      errors.push(error('/colors/eyes', 'pattern', 'must match pattern "#rrggbb"'))
    }
  }
  errors.push(...checkBody(value.body, '/body'))
  if (!value.expressions || typeof value.expressions !== 'object') {
    errors.push(error('/expressions', 'required', `must have required property 'expressions'`))
  } else {
    if (!('neutral' in value.expressions)) {
      errors.push(error('/expressions', 'required', `must have required property 'neutral'`))
    }
    Object.entries(value.expressions).forEach(([key, expression]) => {
      if (!isValidSemanticKey(key)) {
        errors.push(error(childPointer('/expressions', key), 'propertyNames', 'must match semantic key pattern'))
      }
      errors.push(...checkExpression(expression, childPointer('/expressions', key)))
    })
  }
  if (!Array.isArray(value.expressionOrder)) {
    errors.push(error('/expressionOrder', 'type', 'must be array'))
  }
  if (!value.animations || typeof value.animations !== 'object') {
    errors.push(error('/animations', 'required', `must have required property 'animations'`))
  } else {
    Object.entries(value.animations).forEach(([key, animation]) => {
      if (!isValidSemanticKey(key)) {
        errors.push(error(childPointer('/animations', key), 'propertyNames', 'must match semantic key pattern'))
      }
      errors.push(...checkAnimation(animation, childPointer('/animations', key)))
    })
  }
  if (!Array.isArray(value.animationOrder)) {
    errors.push(error('/animationOrder', 'type', 'must be array'))
  }
  return errors
}

const cloneAndFreeze = (value) => {
  if (value === null || typeof value !== 'object') return value
  const clone = Array.isArray(value)
    ? value.map(item => cloneAndFreeze(item))
    : Object.fromEntries(Object.entries(value).map(([key, item]) => [key, cloneAndFreeze(item)]))
  return Object.freeze(clone)
}

export const validateAvatarDefinition = (value) => {
  const structuralErrors = inspectMaterializedValue(value)
  if (structuralErrors.length) return { ok: false, errors: structuralErrors }
  const shapeErrors = inspectSchemaShape(value)
  if (shapeErrors.length) return { ok: false, errors: shapeErrors }
  const errors = semanticErrors(value)
  return errors.length ? { ok: false, errors } : { ok: true, value: cloneAndFreeze(value) }
}