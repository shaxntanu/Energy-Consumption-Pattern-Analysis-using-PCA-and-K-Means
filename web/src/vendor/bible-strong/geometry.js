// Vendored from @bible-strong/avatar-core geometry.ts (AGPL-3.0). TypeScript
// stripped; runtime behavior unchanged.
import { cursorLayout, surfaceFrontSampleAt, surfacePointAt, surfaceSampleAt } from './surfaces'

export const RADIUS = 120
const FOCAL_LENGTH = 620
const QUARTER_ARC_SAMPLES = 14

export const expressionFields = [
  'headX',
  'headY',
  'headZ',
  'widthLeft',
  'widthRight',
  'heightLeft',
  'heightRight',
  'spacing',
  'positionXLeft',
  'positionXRight',
  'positionYLeft',
  'positionYRight',
  'leftAngle',
  'rightAngle',
  'perspective',
]

export const clamp = (value, min, max) => Math.max(min, Math.min(max, value))

export const radians = (degrees) => (degrees * Math.PI) / 180

export const normalizeQuaternion = ([w, x, y, z]) => {
  const length = Math.hypot(w, x, y, z) || 1
  return [w / length, x / length, y / length, z / length]
}

export const multiplyQuaternions = ([aw, ax, ay, az], [bw, bx, by, bz]) =>
  normalizeQuaternion([
    aw * bw - ax * bx - ay * by - az * bz,
    aw * bx + ax * bw + ay * bz - az * by,
    aw * by - ax * bz + ay * bw + az * bx,
    aw * bz + ax * by - ay * bx + az * bw,
  ])

export const quaternionFromAxisAngle = ([x, y, z], angle) => {
  const halfAngle = angle / 2
  const sine = Math.sin(halfAngle)
  return normalizeQuaternion([Math.cos(halfAngle), x * sine, y * sine, z * sine])
}

export const quaternionFromEuler = (x, y, z) => {
  const xRotation = quaternionFromAxisAngle([1, 0, 0], x)
  const yRotation = quaternionFromAxisAngle([0, 1, 0], y)
  const zRotation = quaternionFromAxisAngle([0, 0, 1], z)
  return multiplyQuaternions(multiplyQuaternions(zRotation, xRotation), yRotation)
}

export const quaternionFromVectors = (from, to) => {
  const dot = from[0] * to[0] + from[1] * to[1] + from[2] * to[2]
  const cross = [
    from[1] * to[2] - from[2] * to[1],
    from[2] * to[0] - from[0] * to[2],
    from[0] * to[1] - from[1] * to[0],
  ]
  return normalizeQuaternion([1 + dot, cross[0], cross[1], cross[2]])
}

export const quaternionToEuler = ([w, x, y, z]) => {
  const matrix00 = 1 - 2 * (y * y + z * z)
  const matrix01 = 2 * (x * y - z * w)
  const matrix10 = 2 * (x * y + z * w)
  const matrix11 = 1 - 2 * (x * x + z * z)
  const matrix20 = 2 * (x * z - y * w)
  const matrix21 = 2 * (y * z + x * w)
  const matrix22 = 1 - 2 * (x * x + y * y)
  const headX = Math.asin(clamp(matrix21, -1, 1))
  if (Math.abs(Math.cos(headX)) < 0.00001) return [headX, 0, Math.atan2(matrix10, matrix00)]
  return [headX, Math.atan2(-matrix20, matrix22), Math.atan2(-matrix01, matrix11)]
}

const nearestEquivalentAngle = (angle, current) => {
  let result = angle
  while (result - current > 180) result -= 360
  while (result - current < -180) result += 360
  return clamp(result, -365, 365)
}

export const expressionWithOrientation = (expression, orientation) => {
  const [radiansX, radiansY, radiansZ] = quaternionToEuler(orientation)
  const x = (radiansX * 180) / Math.PI
  const y = (radiansY * 180) / Math.PI
  const z = (radiansZ * 180) / Math.PI
  return {
    ...expression,
    headX: nearestEquivalentAngle(x, expression.headX),
    headY: nearestEquivalentAngle(y, expression.headY),
    headZ: nearestEquivalentAngle(z, expression.headZ),
  }
}

export const slerpQuaternion = (start, end, progress) => {
  let target = end
  let dot = start.reduce((total, value, index) => total + value * target[index], 0)
  if (dot < 0) {
    target = target.map(value => -value)
    dot = -dot
  }
  if (dot > 0.9995) {
    return normalizeQuaternion(
      start.map((value, index) => value + (target[index] - value) * progress)
    )
  }
  const angle = Math.acos(clamp(dot, -1, 1))
  const sine = Math.sin(angle)
  const startWeight = Math.sin((1 - progress) * angle) / sine
  const targetWeight = Math.sin(progress * angle) / sine
  return normalizeQuaternion(
    start.map((value, index) => value * startWeight + target[index] * targetWeight)
  )
}

export const rotateWithQuaternion = ([w, x, y, z], [px, py, pz]) => {
  const tx = 2 * (y * pz - z * py)
  const ty = 2 * (z * px - x * pz)
  const tz = 2 * (x * py - y * px)
  return [
    px + w * tx + (y * tz - z * ty),
    py + w * ty + (z * tx - x * tz),
    pz + w * tz + (x * ty - y * tx),
  ]
}

const roundedRectangle = (width, height) => {
  const halfWidth = width / 2
  const halfHeight = height / 2
  const cornerRadius = Math.min(halfHeight, halfWidth)
  const points = []
  const addLine = (start, end) => {
    const samples = Math.max(2, Math.ceil(Math.hypot(end[0] - start[0], end[1] - start[1]) / 1.5))
    for (let index = 0; index < samples; index += 1) {
      const progress = index / samples
      points.push([
        start[0] + (end[0] - start[0]) * progress,
        start[1] + (end[1] - start[1]) * progress,
      ])
    }
  }
  const addArc = (centerX, centerY, startAngle) => {
    for (let index = 0; index < QUARTER_ARC_SAMPLES; index += 1) {
      const angle = startAngle + (index / QUARTER_ARC_SAMPLES) * (Math.PI / 2)
      points.push([
        centerX + Math.cos(angle) * cornerRadius,
        centerY + Math.sin(angle) * cornerRadius,
      ])
    }
  }
  addLine([-halfWidth + cornerRadius, -halfHeight], [halfWidth - cornerRadius, -halfHeight])
  addArc(halfWidth - cornerRadius, -halfHeight + cornerRadius, -Math.PI / 2)
  addLine([halfWidth, -halfHeight + cornerRadius], [halfWidth, halfHeight - cornerRadius])
  addArc(halfWidth - cornerRadius, halfHeight - cornerRadius, 0)
  addLine([halfWidth - cornerRadius, halfHeight], [-halfWidth + cornerRadius, halfHeight])
  addArc(-halfWidth + cornerRadius, halfHeight - cornerRadius, Math.PI / 2)
  addLine([-halfWidth, halfHeight - cornerRadius], [-halfWidth, -halfHeight + cornerRadius])
  addArc(-halfWidth + cornerRadius, -halfHeight + cornerRadius, Math.PI)
  return points
}

const project = (point, perspective) => {
  const denominator = FOCAL_LENGTH - point[2] * perspective
  const scale = Math.abs(denominator) < 0.0001 ? FOCAL_LENGTH / 0.0001 : FOCAL_LENGTH / denominator
  return [point[0] * scale, point[1] * scale, point[2]]
}

export const axisVector = axis =>
  axis === 'x' ? [1, 0, 0] : axis === 'y' ? [0, 1, 0] : [0, 0, 1]

export const rotateExpressionAroundAxis = (expression, axis, deltaDegrees) => {
  const startOrientation = poseFromExpression(expression).orientation
  const worldAxis = rotateWithQuaternion(startOrientation, axisVector(axis))
  const orientation = multiplyQuaternions(
    quaternionFromAxisAngle(worldAxis, radians(deltaDegrees)),
    startOrientation
  )
  return expressionWithOrientation(expression, orientation)
}

export const rotateExpressionAroundCamera = (expression, deltaRadians) => {
  const startOrientation = poseFromExpression(expression).orientation
  return expressionWithOrientation(
    expression,
    multiplyQuaternions(quaternionFromAxisAngle([0, 0, 1], deltaRadians), startOrientation)
  )
}

const arcballVector = ([xValue, yValue]) => {
  const x = xValue / RADIUS
  const y = yValue / RADIUS
  const squaredLength = x * x + y * y
  if (squaredLength <= 1) return [x, y, Math.sqrt(1 - squaredLength)]
  const length = Math.sqrt(squaredLength)
  return [x / length, y / length, 0]
}

export const rotateExpressionWithArcball = (expression, startPoint, currentPoint) => {
  const startOrientation = poseFromExpression(expression).orientation
  const delta = quaternionFromVectors(arcballVector(startPoint), arcballVector(currentPoint))
  return expressionWithOrientation(expression, multiplyQuaternions(delta, startOrientation))
}

export const rotationRing = (pose, axis, radius = 30) =>
  Array.from({ length: 97 }, (_, index) => {
    const angle = (index / 96) * Math.PI * 2
    const cosine = Math.cos(angle)
    const sine = Math.sin(angle)
    const point = axis === 'x' ? [0, cosine, sine] : axis === 'y' ? [cosine, 0, sine] : [cosine, sine, 0]
    const rotated = rotateWithQuaternion(pose.orientation, point)
    return [rotated[0] * radius, rotated[1] * radius, rotated[2]]
  })

export const renderBodyNodeEditor = (pose, node, axisLength = 34, ringRadius = 26) => {
  const projectInHeadSpace = point =>
    project(rotateWithQuaternion(pose.orientation, point), pose.expression.perspective)
  const center = projectInHeadSpace(node.position)
  const localOrientation = quaternionFromEuler(
    radians(node.rotation[0]),
    radians(node.rotation[1]),
    radians(node.rotation[2])
  )
  const axes = Object.fromEntries(
    ['x', 'y', 'z'].map(axis => {
      const vector = rotateWithQuaternion(localOrientation, axisVector(axis))
      return [
        axis,
        projectInHeadSpace([
          node.position[0] + vector[0] * axisLength,
          node.position[1] + vector[1] * axisLength,
          node.position[2] + vector[2] * axisLength,
        ]),
      ]
    })
  )
  ;['x', 'y', 'z'].forEach(axis => {
    const endpoint = axes[axis]
    if (Math.hypot(endpoint[0] - center[0], endpoint[1] - center[1]) >= 12) return
    const fallback =
      axis === 'x'
        ? [center[0] + 18, center[1], endpoint[2]]
        : axis === 'y'
          ? [center[0], center[1] + 18, endpoint[2]]
          : [center[0] + 14, center[1] + 14, endpoint[2]]
    axes[axis] = fallback
  })
  const rings = Object.fromEntries(
    ['x', 'y', 'z'].map(axis => [
      axis,
      Array.from({ length: 65 }, (_, index) => {
        const angle = (index / 64) * Math.PI * 2
        const cosine = Math.cos(angle) * ringRadius
        const sine = Math.sin(angle) * ringRadius
        const localPoint =
          axis === 'x' ? [0, cosine, sine] : axis === 'y' ? [cosine, 0, sine] : [cosine, sine, 0]
        const rotated = rotateWithQuaternion(localOrientation, localPoint)
        return projectInHeadSpace([
          node.position[0] + rotated[0],
          node.position[1] + rotated[1],
          node.position[2] + rotated[2],
        ])
      }),
    ])
  )
  return { center, axes, rings }
}

export const translateBodyNodeAlongLocalAxis = (node, axis, distance) => {
  const orientation = quaternionFromEuler(
    radians(node.rotation[0]),
    radians(node.rotation[1]),
    radians(node.rotation[2])
  )
  const direction = rotateWithQuaternion(orientation, axisVector(axis))
  return {
    ...node,
    position: [
      node.position[0] + direction[0] * distance,
      node.position[1] + direction[1] * distance,
      node.position[2] + direction[2] * distance,
    ],
  }
}

export const translateBodyNodeInCameraPlane = (node, pose, screenDeltaX, screenDeltaY) => {
  const cameraPosition = rotateWithQuaternion(pose.orientation, node.position)
  const denominator = FOCAL_LENGTH - cameraPosition[2] * pose.expression.perspective
  const perspectiveScale =
    Math.abs(denominator) < 0.0001 ? FOCAL_LENGTH / 0.0001 : FOCAL_LENGTH / denominator
  const [w, x, y, z] = pose.orientation
  const headDelta = rotateWithQuaternion(
    [w, -x, -y, -z],
    [screenDeltaX / perspectiveScale, screenDeltaY / perspectiveScale, 0]
  )
  return {
    ...node,
    position: [
      node.position[0] + headDelta[0],
      node.position[1] + headDelta[1],
      node.position[2] + headDelta[2],
    ],
  }
}

export const rotateBodyNodeAroundLocalAxis = (node, axis, deltaDegrees) => {
  const orientation = quaternionFromEuler(
    radians(node.rotation[0]),
    radians(node.rotation[1]),
    radians(node.rotation[2])
  )
  const rotated = multiplyQuaternions(
    orientation,
    quaternionFromAxisAngle(axisVector(axis), radians(deltaDegrees))
  )
  const next = quaternionToEuler(rotated).map(value => (value * 180) / Math.PI)
  return {
    ...node,
    rotation: next.map((value, index) => nearestEquivalentAngle(value, node.rotation[index])),
  }
}

const path = (points, close = true) => {
  if (!points.length) return ''
  return `M${points[0][0].toFixed(2)} ${points[0][1].toFixed(2)}${points
    .slice(1)
    .map(point => `L${point[0].toFixed(2)} ${point[1].toFixed(2)}`)
    .join('')}${close ? 'Z' : ''}`
}

export const poseFromExpression = expression => ({
  expression,
  orientation: quaternionFromEuler(
    radians(expression.headX),
    radians(expression.headY),
    radians(expression.headZ)
  ),
})

export const interpolatePose = (from, to, progress) => {
  const expression = { ...from.expression }
  expressionFields.forEach(field => {
    let target = to.expression[field]
    if (
      field === 'headX' ||
      field === 'headY' ||
      field === 'headZ' ||
      field === 'leftAngle' ||
      field === 'rightAngle'
    ) {
      target = nearestEquivalentAngle(target, from.expression[field])
    }
    expression[field] = from.expression[field] + (target - from.expression[field]) * progress
  })
  return {
    expression,
    orientation: poseFromExpression(expression).orientation,
  }
}

const MAX_SURFACE_CACHE_ENTRIES = 24
const HEAD_LATITUDE_SAMPLES = 25
const HEAD_LONGITUDE_SAMPLES = 73
const PRIMITIVE_RING_SAMPLES = 144
const ROUNDED_PRIMITIVE_LATITUDE_SAMPLES = 33
const ROUNDED_PRIMITIVE_LONGITUDE_SAMPLES = 73
const headSamplesCache = new Map()
const accessorySamplesCache = new Map()
const wireSamplesCache = new Map()

const surfaceCacheKey = surface =>
  JSON.stringify([
    surface.type,
    surface.width,
    surface.height,
    surface.depth,
    surface.roundness,
    surface.morphRoundness,
    surface.tipRoundness,
    surface.baseRoundness,
  ])

const cacheSurfaceValue = (cache, key, value) => {
  if (cache.size >= MAX_SURFACE_CACHE_ENTRIES) cache.delete(cache.keys().next().value)
  cache.set(key, value)
  return value
}

const localSurfacePoint = (surface, longitude, latitude) =>
  surfaceSampleAt(surface, longitude, latitude)

const projectLocalSurfacePoint = (pose, sample) => ({
  point: project(rotateWithQuaternion(pose.orientation, sample.point), pose.expression.perspective),
  normal: rotateWithQuaternion(pose.orientation, sample.normal),
})

const canonicalFaceCoordinates = (x, y) => {
  const longitude = x / RADIUS
  const latitude = y / RADIUS
  return [RADIUS * Math.cos(latitude) * Math.sin(longitude), RADIUS * Math.sin(latitude)]
}

const projectFacePoint = (pose, surface, x, y) => {
  const [faceX, faceY] = canonicalFaceCoordinates(x, y)
  return projectLocalSurfacePoint(pose, surfaceFrontSampleAt(surface, faceX, faceY))
}

const eyePoints = (pose, surface, side, blink, offset = { x: 0, y: 0 }) => {
  const expression = pose.expression
  const suffix = side < 0 ? 'Left' : 'Right'
  const width = expression[`width${suffix}`]
  const restingHeight = expression[`height${suffix}`]
  const height = 5 + (restingHeight - 5) * blink
  const centerX = (side * expression.spacing) / 2 + expression[`positionX${suffix}`] + offset.x
  const centerY = expression[`positionY${suffix}`] + offset.y
  const angle = radians(side < 0 ? expression.leftAngle : expression.rightAngle)
  return roundedRectangle(width, height).map(([localX, localY]) => {
    const rotatedX = localX * Math.cos(angle) - localY * Math.sin(angle)
    const rotatedY = localX * Math.sin(angle) + localY * Math.cos(angle)
    return projectFacePoint(pose, surface, centerX + rotatedX, centerY + rotatedY)
  })
}

const visiblePath = points => {
  const segments = []
  let segment = []
  points.forEach(({ point, normal }) => {
    if (normal[2] > 0) segment.push(point)
    else if (segment.length) {
      segments.push(segment)
      segment = []
    }
  })
  if (segment.length) segments.push(segment)
  return segments
    .filter(item => item.length > 1)
    .map(item => path(item, false))
    .join('')
}

const wirePaths = (pose, surface) => {
  const key = surfaceCacheKey(surface)
  let samples = wireSamplesCache.get(key)
  if (!samples) {
    const parallels = [-60, -30, 0, 30, 60].map(latitude =>
      Array.from({ length: 73 }, (_, index) =>
        localSurfacePoint(surface, radians(-180 + index * 5), radians(latitude))
      )
    )
    const meridians = Array.from(
      { length: 12 },
      (_, longitudeIndex) => -150 + longitudeIndex * 30
    ).map(longitude =>
      Array.from({ length: 37 }, (_, index) =>
        localSurfacePoint(surface, radians(longitude), radians(-90 + index * 5))
      )
    )
    samples = cacheSurfaceValue(wireSamplesCache, key, [...parallels, ...meridians])
  }
  return samples.map(curve =>
    visiblePath(curve.map(sample => projectLocalSurfacePoint(pose, sample)))
  )
}

const projectEyePoint = (pose, surface, side, localX, localY) => {
  const expression = pose.expression
  const suffix = side < 0 ? 'Left' : 'Right'
  const angle = radians(side < 0 ? expression.leftAngle : expression.rightAngle)
  const rotatedX = localX * Math.cos(angle) - localY * Math.sin(angle)
  const rotatedY = localX * Math.sin(angle) + localY * Math.cos(angle)
  return projectFacePoint(
    pose,
    surface,
    (side * expression.spacing) / 2 + expression[`positionX${suffix}`] + rotatedX,
    expression[`positionY${suffix}`] + rotatedY
  ).point
}

export const renderEyeEditor = (pose, surface, side) => {
  const expression = pose.expression
  const suffix = side < 0 ? 'Left' : 'Right'
  const width = expression[`width${suffix}`]
  const height = expression[`height${suffix}`]
  const selectedSamples = eyePoints(pose, surface, side, 1)
  const selectedPoints = selectedSamples.map(sample => sample.point)
  const center = projectEyePoint(pose, surface, side, 0, 0)
  const widthHandle = projectEyePoint(pose, surface, side, width / 2 + 9, 0)
  const heightHandle = projectEyePoint(pose, surface, side, 0, -height / 2 - 9)
  const rotateHandle = projectEyePoint(pose, surface, side, 0, -height / 2 - 30)
  const sizeHandle = projectEyePoint(pose, surface, side, width / 2 + 11, height / 2 + 11)
  const leftCenter = projectEyePoint(pose, surface, -1, 0, 0)
  const rightCenter = projectEyePoint(pose, surface, 1, 0, 0)
  const spacingCenterX = (expression.positionXLeft + expression.positionXRight) / 2
  const spacingCenterY = (expression.positionYLeft + expression.positionYRight) / 2
  const spacingHandle = projectFacePoint(
    pose,
    surface,
    spacingCenterX,
    spacingCenterY + height / 2 + 34
  ).point
  const spacingMiddle = [
    (leftCenter[0] + rightCenter[0]) / 2,
    (leftCenter[1] + rightCenter[1]) / 2,
    (leftCenter[2] + rightCenter[2]) / 2,
  ]
  const line = (from, to) => path([from, to], false)
  return {
    visible: selectedSamples.reduce((total, sample) => total + sample.normal[2], 0) > 0,
    selectionPath: path(selectedPoints),
    widthGuide: line(center, widthHandle),
    heightGuide: line(center, heightHandle),
    rotationGuide: line(heightHandle, rotateHandle),
    spacingGuide: `${line(leftCenter, rightCenter)}${line(spacingMiddle, spacingHandle)}`,
    center,
    widthHandle,
    heightHandle,
    rotateHandle,
    sizeHandle,
    spacingHandle,
  }
}

const convexHull = points => {
  const sorted = [...points].sort((left, right) => left[0] - right[0] || left[1] - right[1])
  const cross = (origin, first, second) =>
    (first[0] - origin[0]) * (second[1] - origin[1]) -
    (first[1] - origin[1]) * (second[0] - origin[0])
  const half = source => {
    const result = []
    source.forEach(point => {
      while (
        result.length >= 2 &&
        cross(result[result.length - 2], result[result.length - 1], point) <= 0
      )
        result.pop()
      result.push(point)
    })
    return result
  }
  return [...half(sorted).slice(0, -1), ...half(sorted.reverse()).slice(0, -1)]
}

const smoothClosedPath = points => {
  if (points.length < 3) return path(points)
  const pointAt = index => points[(index + points.length) % points.length]
  return `M${points[0][0].toFixed(2)} ${points[0][1].toFixed(2)}${points
    .map((point, index) => {
      const previous = pointAt(index - 1)
      const next = pointAt(index + 1)
      const afterNext = pointAt(index + 2)
      const firstControl = [
        point[0] + (next[0] - previous[0]) / 6,
        point[1] + (next[1] - previous[1]) / 6,
        point[2],
      ]
      const secondControl = [
        next[0] - (afterNext[0] - point[0]) / 6,
        next[1] - (afterNext[1] - point[1]) / 6,
        next[2],
      ]
      return `C${firstControl[0].toFixed(2)} ${firstControl[1].toFixed(2)} ${secondControl[0].toFixed(2)} ${secondControl[1].toFixed(2)} ${next[0].toFixed(2)} ${next[1].toFixed(2)}`
    })
    .join('')}Z`
}

const densifyClosedPoints = (points, maximumDistance = 7) =>
  points.flatMap((point, index) => {
    const next = points[(index + 1) % points.length]
    const steps = Math.max(
      1,
      Math.ceil(Math.hypot(next[0] - point[0], next[1] - point[1]) / maximumDistance)
    )
    return Array.from({ length: steps }, (_, step) => {
      const progress = step / steps
      return [
        point[0] + (next[0] - point[0]) * progress,
        point[1] + (next[1] - point[1]) * progress,
        point[2] + (next[2] - point[2]) * progress,
      ]
    })
  })

const smoothOpenPath = points => {
  if (!points.length) return ''
  if (points.length === 1) return `${points[0][0].toFixed(2)} ${points[0][1].toFixed(2)}`
  return points
    .slice(0, -1)
    .map((point, index) => {
      const previous = points[Math.max(0, index - 1)]
      const next = points[index + 1]
      const afterNext = points[Math.min(points.length - 1, index + 2)]
      const firstControlX = point[0] + (next[0] - previous[0]) / 6
      const firstControlY = point[1] + (next[1] - previous[1]) / 6
      const secondControlX = next[0] - (afterNext[0] - point[0]) / 6
      const secondControlY = next[1] - (afterNext[1] - point[1]) / 6
      return `C${firstControlX.toFixed(2)} ${firstControlY.toFixed(2)} ${secondControlX.toFixed(2)} ${secondControlY.toFixed(2)} ${next[0].toFixed(2)} ${next[1].toFixed(2)}`
    })
    .join('')
}

const projectLocalPoint = (pose, point) =>
  project(rotateWithQuaternion(pose.orientation, point), pose.expression.perspective)

const ringPoints = (width, depth, y) =>
  Array.from({ length: PRIMITIVE_RING_SAMPLES + 1 }, (_, index) => {
    const angle = (index / PRIMITIVE_RING_SAMPLES) * Math.PI * 2
    return [(width / 2) * Math.sin(angle), y, (depth / 2) * Math.cos(angle)]
  })

const projectedRoundedPrimitivePath = (pose, surface) => {
  const key = surfaceCacheKey(surface)
  let localSamples = headSamplesCache.get(key)
  if (!localSamples) {
    localSamples = Array.from(
      { length: ROUNDED_PRIMITIVE_LATITUDE_SAMPLES },
      (_, latitudeIndex) => {
        const latitude =
          -Math.PI / 2 + (latitudeIndex / (ROUNDED_PRIMITIVE_LATITUDE_SAMPLES - 1)) * Math.PI
        return Array.from({ length: ROUNDED_PRIMITIVE_LONGITUDE_SAMPLES }, (_, longitudeIndex) => {
          const longitude =
            -Math.PI + (longitudeIndex / (ROUNDED_PRIMITIVE_LONGITUDE_SAMPLES - 1)) * Math.PI * 2
          return surfacePointAt(surface, longitude, latitude)
        })
      }
    ).flat()
    cacheSurfaceValue(headSamplesCache, key, localSamples)
  }
  const projected = localSamples.map(point => projectLocalPoint(pose, point))
  return smoothClosedPath(densifyClosedPoints(convexHull(projected)))
}

const projectedCylinderPath = (pose, surface) => {
  if (surface.roundness > 0 || (surface.morphRoundness ?? 0) > 0) {
    return projectedRoundedPrimitivePath(pose, surface)
  }

  const halfHeight = surface.height / 2
  const projected = [
    ...ringPoints(surface.width, surface.depth, -halfHeight),
    ...ringPoints(surface.width, surface.depth, halfHeight),
  ].map(point => projectLocalPoint(pose, point))
  return smoothClosedPath(densifyClosedPoints(convexHull(projected)))
}

const projectedCursorBodyPath = (pose, surface) => {
  const layout = cursorLayout(surface)
  const halfHeight = layout.bodyHeight / 2
  const projected = [
    ...ringPoints(layout.bodyWidth, layout.bodyDepth, layout.bodyCenterY - halfHeight),
    ...ringPoints(layout.bodyWidth, layout.bodyDepth, layout.bodyCenterY + halfHeight),
  ].map(point => projectLocalPoint(pose, point))
  return smoothClosedPath(densifyClosedPoints(convexHull(projected)))
}

const projectedCursorConePath = (pose, surface) => {
  const layout = cursorLayout(surface)
  const apex = projectLocalPoint(pose, [0, layout.coneApexY, 0])
  const base = ringPoints(surface.width, surface.depth, layout.coneBaseY).map(point =>
    projectLocalPoint(pose, point)
  )
  return smoothClosedPath(densifyClosedPoints(convexHull([...base, apex])))
}

const projectedConePath = (pose, surface) => {
  if (
    (surface.morphRoundness ?? 0) > 0 ||
    (surface.tipRoundness ?? 0) > 0 ||
    (surface.baseRoundness ?? 0) > 0
  ) {
    return projectedRoundedPrimitivePath(pose, surface)
  }

  const apex = projectLocalPoint(pose, [0, -surface.height / 2, 0])
  const base = ringPoints(surface.width, surface.depth, surface.height / 2).map(point =>
    projectLocalPoint(pose, point)
  )
  const hull = convexHull([...base, apex])
  const apexIndex = hull.findIndex(
    point => Math.hypot(point[0] - apex[0], point[1] - apex[1]) < 0.01
  )
  if (apexIndex < 0) return smoothClosedPath(hull)

  const ordered = [...hull.slice(apexIndex), ...hull.slice(0, apexIndex)]
  const baseArc = ordered.slice(1)
  if (baseArc.length < 2) return path(hull)
  return `M${apex[0].toFixed(2)} ${apex[1].toFixed(2)}L${baseArc[0][0].toFixed(2)} ${baseArc[0][1].toFixed(2)}${smoothOpenPath(baseArc)}L${apex[0].toFixed(2)} ${apex[1].toFixed(2)}Z`
}

const projectedCubePath = (pose, surface) => {
  if (surface.roundness > 0) return projectedRoundedPrimitivePath(pose, surface)

  const halfWidth = surface.width / 2
  const halfHeight = surface.height / 2
  const halfDepth = surface.depth / 2
  const vertices = [-1, 1].flatMap(x =>
    [-1, 1].flatMap(y => [-1, 1].map(z => [x * halfWidth, y * halfHeight, z * halfDepth]))
  )
  return path(convexHull(vertices.map(point => projectLocalPoint(pose, point))))
}

const projectedDiamondPath = (pose, surface) => {
  if (surface.roundness > 0) return projectedRoundedPrimitivePath(pose, surface)

  const halfWidth = surface.width / 2
  const halfHeight = surface.height / 2
  const halfDepth = surface.depth / 2
  const vertices = [
    [-halfWidth, 0, 0],
    [halfWidth, 0, 0],
    [0, -halfHeight, 0],
    [0, halfHeight, 0],
    [0, 0, -halfDepth],
    [0, 0, halfDepth],
  ]
  return path(convexHull(vertices.map(point => projectLocalPoint(pose, point))))
}

const ellipseProjection = (centerX, centerY, covarianceXX, covarianceXY, covarianceYY) => {
  const trace = covarianceXX + covarianceYY
  const difference = Math.hypot(covarianceXX - covarianceYY, covarianceXY * 2)
  const majorSquared = (trace + difference) / 2
  const minorSquared = (trace - difference) / 2
  if (majorSquared <= 0 || minorSquared <= 0) return null

  return {
    centerX,
    centerY,
    majorRadius: Math.sqrt(majorSquared),
    minorRadius: Math.sqrt(minorSquared),
    rotation: Math.atan2(covarianceXY * 2, covarianceXX - covarianceYY) / 2,
  }
}

const ellipsePath = ({ centerX, centerY, majorRadius, minorRadius, rotation }) => {
  const rotationDegrees = (rotation * 180) / Math.PI
  const offsetX = Math.cos(rotation) * majorRadius
  const offsetY = Math.sin(rotation) * majorRadius
  const startX = centerX + offsetX
  const startY = centerY + offsetY
  const endX = centerX - offsetX
  const endY = centerY - offsetY

  return `M${startX.toFixed(2)} ${startY.toFixed(2)}A${majorRadius.toFixed(2)} ${minorRadius.toFixed(2)} ${rotationDegrees.toFixed(2)} 0 1 ${endX.toFixed(2)} ${endY.toFixed(2)}A${majorRadius.toFixed(2)} ${minorRadius.toFixed(2)} ${rotationDegrees.toFixed(2)} 0 1 ${startX.toFixed(2)} ${startY.toFixed(2)}Z`
}

const projectedEllipsoid = (pose, axes, localCenter = [0, 0, 0]) => {
  const rotatedAxes = [
    rotateWithQuaternion(pose.orientation, [1, 0, 0]),
    rotateWithQuaternion(pose.orientation, [0, 1, 0]),
    rotateWithQuaternion(pose.orientation, [0, 0, 1]),
  ]
  const center = rotateWithQuaternion(pose.orientation, localCenter)

  if (Math.abs(pose.expression.perspective) < 0.0001) {
    const covarianceXX = rotatedAxes.reduce(
      (total, axis, index) => total + axis[0] * axis[0] * axes[index] * axes[index],
      0
    )
    const covarianceXY = rotatedAxes.reduce(
      (total, axis, index) => total + axis[0] * axis[1] * axes[index] * axes[index],
      0
    )
    const covarianceYY = rotatedAxes.reduce(
      (total, axis, index) => total + axis[1] * axis[1] * axes[index] * axes[index],
      0
    )
    return ellipseProjection(center[0], center[1], covarianceXX, covarianceXY, covarianceYY)
  }

  const inverseAxesSquared = axes.map(axis => 1 / (axis * axis))
  const quadratic = Array.from({ length: 3 }, (_, row) =>
    Array.from({ length: 3 }, (_, column) =>
      rotatedAxes.reduce(
        (total, axis, index) => total + axis[row] * inverseAxesSquared[index] * axis[column],
        0
      )
    )
  )
  const focalLength = FOCAL_LENGTH / pose.expression.perspective
  const cameraOffset = [-center[0], -center[1], focalLength - center[2]]
  const cameraNormal = [
    quadratic[0][0] * cameraOffset[0] +
      quadratic[0][1] * cameraOffset[1] +
      quadratic[0][2] * cameraOffset[2],
    quadratic[1][0] * cameraOffset[0] +
      quadratic[1][1] * cameraOffset[1] +
      quadratic[1][2] * cameraOffset[2],
    quadratic[2][0] * cameraOffset[0] +
      quadratic[2][1] * cameraOffset[1] +
      quadratic[2][2] * cameraOffset[2],
  ]
  const cameraTerm =
    cameraOffset[0] * cameraNormal[0] +
    cameraOffset[1] * cameraNormal[1] +
    cameraOffset[2] * cameraNormal[2] -
    1
  const tangentLinear = [cameraNormal[0], cameraNormal[1], -focalLength * cameraNormal[2]]
  const rayQuadratic = [
    [quadratic[0][0], quadratic[0][1], -focalLength * quadratic[0][2]],
    [quadratic[1][0], quadratic[1][1], -focalLength * quadratic[1][2]],
    [
      -focalLength * quadratic[2][0],
      -focalLength * quadratic[2][1],
      focalLength * focalLength * quadratic[2][2],
    ],
  ]
  const conic = Array.from({ length: 3 }, (_, row) =>
    Array.from(
      { length: 3 },
      (_, column) =>
        tangentLinear[row] * tangentLinear[column] - cameraTerm * rayQuadratic[row][column]
    )
  )
  const determinant = conic[0][0] * conic[1][1] - conic[0][1] * conic[0][1]
  if (Math.abs(determinant) < 1e-12) return null

  const centerX = -(conic[1][1] * conic[0][2] - conic[0][1] * conic[1][2]) / determinant
  const centerY = (conic[0][1] * conic[0][2] - conic[0][0] * conic[1][2]) / determinant
  const centeredConstant = conic[2][2] + conic[0][2] * centerX + conic[1][2] * centerY
  const scale = -centeredConstant
  if (Math.abs(scale) < 1e-12) return null

  const shapeXX = conic[0][0] / scale
  const shapeXY = conic[0][1] / scale
  const shapeYY = conic[1][1] / scale
  const shapeDeterminant = shapeXX * shapeYY - shapeXY * shapeXY
  if (shapeDeterminant <= 0) return null

  return ellipseProjection(
    centerX,
    centerY,
    shapeYY / shapeDeterminant,
    -shapeXY / shapeDeterminant,
    shapeXX / shapeDeterminant
  )
}

const projectedEllipsoidPath = (pose, surface) => {
  const ellipse = projectedEllipsoid(pose, [
    surface.width / 2,
    surface.height / 2,
    surface.depth / 2,
  ])
  const isSphere = surface.width === surface.height && surface.height === surface.depth
  if (ellipse && isSphere) {
    const radius = (ellipse.majorRadius + ellipse.minorRadius) / 2
    return ellipsePath({
      centerX: 0,
      centerY: 0,
      majorRadius: radius,
      minorRadius: radius,
      rotation: 0,
    })
  }
  return ellipse ? ellipsePath(ellipse) : null
}

const mickeyEarPaths = (pose, surface) => {
  if (surface.type !== 'mickey') return []

  const radius = Math.min(surface.width, surface.height) * 0.23
  const depthRadius = Math.min(radius, surface.depth * 0.29)
  const centerX = surface.width * 0.37
  const centerY = -surface.height * 0.39
  const centerZ = -surface.depth * 0.12
  const axes = [radius, radius, depthRadius]
  return [-1, 1]
    .map(side => projectedEllipsoid(pose, axes, [side * centerX, centerY, centerZ]))
    .filter(ear => ear !== null)
    .map(ellipsePath)
}

const compositeBackPaths = (pose, surface) => {
  if (surface.type === 'mickey') return mickeyEarPaths(pose, surface)
  if (surface.type === 'cursor') return [projectedCursorConePath(pose, surface)]
  return []
}

const ellipsePoints = ellipse =>
  Array.from({ length: PRIMITIVE_RING_SAMPLES }, (_, index) => {
    const angle = (index / PRIMITIVE_RING_SAMPLES) * Math.PI * 2
    const major = Math.cos(angle) * ellipse.majorRadius
    const minor = Math.sin(angle) * ellipse.minorRadius
    return [
      ellipse.centerX + major * Math.cos(ellipse.rotation) - minor * Math.sin(ellipse.rotation),
      ellipse.centerY + major * Math.sin(ellipse.rotation) + minor * Math.cos(ellipse.rotation),
      0,
    ]
  })

const smoothHullPath = points => {
  if (points.length < 3) return path(points)
  const distances = points.map((point, index) => {
    const next = points[(index + 1) % points.length]
    return Math.hypot(next[0] - point[0], next[1] - point[1])
  })
  const sortedDistances = [...distances].sort((left, right) => left - right)
  const medianDistance = sortedDistances[Math.floor(sortedDistances.length / 2)] || 1
  const straightThreshold = Math.max(8, medianDistance * 3.5)
  const straightEdges = distances.map(distance => distance > straightThreshold)

  return `M${points[0][0].toFixed(2)} ${points[0][1].toFixed(2)}${points
    .map((point, index) => {
      const nextIndex = (index + 1) % points.length
      const next = points[nextIndex]
      if (straightEdges[index]) return `L${next[0].toFixed(2)} ${next[1].toFixed(2)}`
      const previous = straightEdges[(index - 1 + points.length) % points.length]
        ? point
        : points[(index - 1 + points.length) % points.length]
      const afterNext = straightEdges[nextIndex] ? next : points[(index + 2) % points.length]
      const firstControlX = point[0] + (next[0] - previous[0]) / 6
      const firstControlY = point[1] + (next[1] - previous[1]) / 6
      const secondControlX = next[0] - (afterNext[0] - point[0]) / 6
      const secondControlY = next[1] - (afterNext[1] - point[1]) / 6
      return `C${firstControlX.toFixed(2)} ${firstControlY.toFixed(2)} ${secondControlX.toFixed(2)} ${secondControlY.toFixed(2)} ${next[0].toFixed(2)} ${next[1].toFixed(2)}`
    })
    .join('')}Z`
}

const projectedCapsulePath = (pose, surface) => {
  const radiusX = surface.width / 2
  const radiusY = Math.min(radiusX, surface.height / 2)
  const radiusZ = surface.depth / 2
  const straightHalf = Math.max(0, (surface.height - radiusY * 2) / 2)
  const axes = [radiusX, radiusY, radiusZ]
  const top = projectedEllipsoid(pose, axes, [0, straightHalf, 0])
  const bottom = projectedEllipsoid(pose, axes, [0, -straightHalf, 0])
  if (!top || !bottom) return null
  return smoothHullPath(convexHull([...ellipsePoints(top), ...ellipsePoints(bottom)]))
}

const headPath = (pose, surface) => {
  if (surface.type === 'sphere' || surface.type === 'mickey') {
    const exactPath = projectedEllipsoidPath(pose, surface)
    if (exactPath) return exactPath
  }

  if (surface.type === 'capsule') {
    const exactPath = projectedCapsulePath(pose, surface)
    if (exactPath) return exactPath
  }

  if (surface.type === 'cylinder') return projectedCylinderPath(pose, surface)
  if (surface.type === 'cursor') return projectedCursorBodyPath(pose, surface)
  if (surface.type === 'cone') return projectedConePath(pose, surface)
  if (surface.type === 'cube') return projectedCubePath(pose, surface)
  if (surface.type === 'diamond') return projectedDiamondPath(pose, surface)

  const key = surfaceCacheKey(surface)
  let localSamples = headSamplesCache.get(key)
  if (!localSamples) {
    localSamples = Array.from({ length: HEAD_LATITUDE_SAMPLES }, (_, latitudeIndex) => {
      const latitude = -Math.PI / 2 + (latitudeIndex / (HEAD_LATITUDE_SAMPLES - 1)) * Math.PI
      return Array.from({ length: HEAD_LONGITUDE_SAMPLES }, (_, longitudeIndex) => {
        const longitude = -Math.PI + (longitudeIndex / (HEAD_LONGITUDE_SAMPLES - 1)) * Math.PI * 2
        return surfacePointAt(surface, longitude, latitude)
      })
    }).flat()
    cacheSurfaceValue(headSamplesCache, key, localSamples)
  }
  const projectedSamples = localSamples.map(sample =>
    project(rotateWithQuaternion(pose.orientation, sample), pose.expression.perspective)
  )
  return path(convexHull(projectedSamples))
}

const accessoryPath = (pose, node) => {
  const key = surfaceCacheKey(node.surface)
  let localSamples = accessorySamplesCache.get(key)
  if (!localSamples) {
    localSamples = Array.from({ length: 17 }, (_, latitudeIndex) => {
      const latitude = -Math.PI / 2 + (latitudeIndex / 16) * Math.PI
      return Array.from({ length: 49 }, (_, longitudeIndex) => {
        const longitude = -Math.PI + (longitudeIndex / 48) * Math.PI * 2
        return surfacePointAt(node.surface, longitude, latitude)
      })
    }).flat()
    cacheSurfaceValue(accessorySamplesCache, key, localSamples)
  }

  const localOrientation = quaternionFromEuler(
    radians(node.rotation[0]),
    radians(node.rotation[1]),
    radians(node.rotation[2])
  )
  const projected = localSamples.map(point => {
    const locallyRotated = rotateWithQuaternion(localOrientation, point)
    const positioned = [
      locallyRotated[0] + node.position[0],
      locallyRotated[1] + node.position[1],
      locallyRotated[2] + node.position[2],
    ]
    return project(rotateWithQuaternion(pose.orientation, positioned), pose.expression.perspective)
  })
  const hull = convexHull(projected)
  if (
    (node.surface.type === 'cube' || node.surface.type === 'diamond') &&
    node.surface.roundness <= 0
  ) {
    return path(hull)
  }
  return smoothClosedPath(densifyClosedPoints(hull))
}

const ACCESSORY_FRONT_CROSSING_RATIO = 0.1

const accessoryCameraDepthRadius = (pose, node) => {
  const localOrientation = quaternionFromEuler(
    radians(node.rotation[0]),
    radians(node.rotation[1]),
    radians(node.rotation[2])
  )
  const cameraDepthByAxis = [
    [1, 0, 0],
    [0, 1, 0],
    [0, 0, 1],
  ].map(
    axis => rotateWithQuaternion(pose.orientation, rotateWithQuaternion(localOrientation, axis))[2]
  )
  return Math.hypot(
    cameraDepthByAxis[0] * (node.surface.width / 2),
    cameraDepthByAxis[1] * (node.surface.height / 2),
    cameraDepthByAxis[2] * (node.surface.depth / 2)
  )
}

const accessoryLayers = (pose, nodes) => {
  const layers = nodes
    .map(node => {
      const depth = rotateWithQuaternion(pose.orientation, node.position)[2]
      return {
        id: node.id,
        path: accessoryPath(pose, node),
        depth,
        front: depth > accessoryCameraDepthRadius(pose, node) * ACCESSORY_FRONT_CROSSING_RATIO,
      }
    })
    .sort((left, right) => left.depth - right.depth)
  return {
    backPaths: layers.filter(layer => !layer.front).map(layer => layer.path),
    frontPaths: layers.filter(layer => layer.front).map(layer => layer.path),
    backNodeIds: layers.filter(layer => !layer.front).map(layer => layer.id),
    frontNodeIds: layers.filter(layer => layer.front).map(layer => layer.id),
  }
}

export const renderAvatar = (pose, surface, blink = 1, options = {}) => {
  const leftSamples = eyePoints(pose, surface, -1, blink, options.eyeOffset)
  const rightSamples = eyePoints(pose, surface, 1, blink, options.eyeOffset)
  const left = leftSamples.map(sample => sample.point)
  const right = rightSamples.map(sample => sample.point)
  const accessories = accessoryLayers(pose, options.bodyNodes ?? [])
  const compositePaths = compositeBackPaths(pose, surface)
  return {
    backPaths: [...compositePaths, ...accessories.backPaths],
    frontPaths: accessories.frontPaths,
    backNodeIds: [...compositePaths.map(() => null), ...accessories.backNodeIds],
    frontNodeIds: accessories.frontNodeIds,
    headPath: headPath(pose, surface),
    leftPath: path(left),
    rightPath: path(right),
    leftVisible: leftSamples.reduce((total, sample) => total + sample.normal[2], 0) > 0,
    rightVisible: rightSamples.reduce((total, sample) => total + sample.normal[2], 0) > 0,
    wirePaths: options.includeWire === false ? [] : wirePaths(pose, surface),
  }
}