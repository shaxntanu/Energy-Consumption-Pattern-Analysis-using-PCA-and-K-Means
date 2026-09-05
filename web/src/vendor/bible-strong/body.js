// Vendored from @bible-strong/avatar-core body.ts (AGPL-3.0). TypeScript
// stripped; runtime behavior unchanged.
import { surfaceLabels, surfacePresets } from './surfaces'

export const bodyPrimitiveTypes = [
  'sphere',
  'cube',
  'capsule',
  'cylinder',
  'cone',
  'diamond',
]

export const MAX_BODY_NODES = 16

const allSurfaceTypes = Object.keys(surfacePresets)
const finite = value => typeof value === 'number' && Number.isFinite(value)
const vector = value => Array.isArray(value) && value.length === 3 && value.every(finite)

export const parseSurfaceConfig = (value, fallback) => {
  if (!value || typeof value !== 'object') return { ...fallback }
  const candidate = value
  const type =
    candidate.type && allSurfaceTypes.includes(candidate.type) ? candidate.type : fallback.type
  const preset = surfacePresets[type]
  const numericFields = ['width', 'height', 'depth', 'roundness']
  if (numericFields.some(field => !finite(candidate[field]))) return { ...fallback }
  if (candidate.morphRoundness !== undefined && !finite(candidate.morphRoundness))
    return { ...fallback }
  if (candidate.tipRoundness !== undefined && !finite(candidate.tipRoundness))
    return { ...fallback }
  if (candidate.baseRoundness !== undefined && !finite(candidate.baseRoundness))
    return { ...fallback }
  return { ...preset, ...candidate, type }
}

export const parseAvatarBody = (value, fallbackPrimary) => {
  if (!value || typeof value !== 'object') return { primary: fallbackPrimary, nodes: [] }
  const candidate = value
  const primary = parseSurfaceConfig(candidate.primary, fallbackPrimary)
  const seenIds = new Set()
  const nodes = Array.isArray(candidate.nodes)
    ? candidate.nodes
        .filter(node => {
          if (!node || typeof node !== 'object') return false
          const surface = node.surface
          const id = node.id
          if (id === 'primary' || seenIds.has(id)) return false
          const valid = Boolean(
            typeof node.id === 'string' &&
              id &&
              typeof node.name === 'string' &&
              surface &&
              bodyPrimitiveTypes.includes(surface.type) &&
              finite(surface.width) &&
              finite(surface.height) &&
              finite(surface.depth) &&
              finite(surface.roundness) &&
              vector(node.position) &&
              vector(node.rotation)
          )
          if (valid) seenIds.add(id)
          return valid
        })
        .slice(0, MAX_BODY_NODES)
        .map(node => ({
          ...node,
          surface: parseSurfaceConfig(node.surface, surfacePresets[node.surface.type]),
        }))
    : []
  return { primary, nodes }
}

export const createBodyNode = (type, index) => {
  const preset = surfacePresets[type]
  const scale = 0.34
  const side = index % 2 === 0 ? -1 : 1
  return {
    id: `shape-${crypto.randomUUID()}`,
    name: `${surfaceLabels[type]} ${index + 1}`,
    surface: {
      ...preset,
      width: preset.width * scale,
      height: preset.height * scale,
      depth: preset.depth * scale,
    },
    position: [side * 82, -72, -18],
    rotation: [0, 0, 0],
  }
}

export const duplicateBodyNode = source => ({
  ...source,
  id: `shape-${crypto.randomUUID()}`,
  name: `${source.name} copie`,
  surface: { ...source.surface },
  position: [source.position[0] + 14, source.position[1] + 14, source.position[2]],
  rotation: [...source.rotation],
})