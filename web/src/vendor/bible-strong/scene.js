// Vendored from @bible-strong/avatar-core scene.ts (AGPL-3.0). TypeScript
// stripped; runtime behavior unchanged.
import { poseFromExpression, renderAvatar } from './geometry'

export const expressionFromDefinition = (key, expression) => ({
  id: key,
  semanticKey: key,
  headX: expression.head.x,
  headY: expression.head.y,
  headZ: expression.head.z,
  widthLeft: expression.eyes.left.width,
  widthRight: expression.eyes.right.width,
  heightLeft: expression.eyes.left.height,
  heightRight: expression.eyes.right.height,
  spacing: expression.eyes.spacing,
  positionXLeft: expression.eyes.left.x,
  positionXRight: expression.eyes.right.x,
  positionYLeft: expression.eyes.left.y,
  positionYRight: expression.eyes.right.y,
  leftAngle: expression.eyes.left.angle,
  rightAngle: expression.eyes.right.angle,
  perspective: expression.perspective,
  eyeMotion: expression.motion.eyes,
  bodyMotion: expression.motion.body,
  ...(expression.colors?.body ? { bodyColor: expression.colors.body } : {}),
  ...(expression.colors?.eyes ? { eyeColor: expression.colors.eyes } : {}),
})

export const bodyFromDefinition = body => ({
  primary: { ...body.primary },
  nodes: body.nodes.map((node, index) => ({
    id: `runtime-node-${index}`,
    name: `Runtime node ${index + 1}`,
    surface: { ...node.surface },
    position: [...node.position],
    rotation: [...node.rotation],
  })),
})

export const renderAvatarExpression = (definition, expression, colors = {}, blink = 1) => {
  const body = bodyFromDefinition(definition.body)
  return {
    geometry: renderAvatar(poseFromExpression(expression), body.primary, blink, {
      bodyNodes: body.nodes,
    }),
    colors: {
      body: colors.body ?? expression.bodyColor ?? definition.colors.body,
      eyes: colors.eyes ?? expression.eyeColor ?? definition.colors.eyes,
    },
  }
}

export const renderAvatarDefinition = (definition, expressionKey = 'neutral') => {
  const publicExpression = definition.expressions[expressionKey]
  if (!publicExpression) throw new Error(`Unknown expression '${expressionKey}'`)
  const expression = expressionFromDefinition(expressionKey, publicExpression)
  return renderAvatarExpression(definition, expression, publicExpression.colors)
}