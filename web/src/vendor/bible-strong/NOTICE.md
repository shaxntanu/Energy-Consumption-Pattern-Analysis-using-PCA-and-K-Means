# Vendored runtime: @bible-strong/avatar-core + @bible-strong/avatar-react

## Provenance

Source: [bible-strong-avatar-lab](https://github.com/smontlouis/bible-strong-avatar-lab)
(monorepo, packages/avatar-core and packages/avatar-react, version 0.1.0).

These files are a vendored copy adapted for this project's JS-only, Vite-based
web app:

- TypeScript sources were converted to plain JavaScript/JSX (types stripped;
  no runtime behavior changed).
- The AJV-based JSON-schema validation (`validateAvatarDefinition` /
  `parseAvatarDefinition` in avatarDefinition.ts) is replaced by the
  dependency-free structural + semantic shim in `validation.js`. The shim
  mirrors the original's `inspectMaterializedValue` and `semanticErrors`
  logic, minus the ajv schema pass. Avatar definitions still receive the
  same "expressionOrder complete, neutral first, expressions known, blink
  intervals valid, plain object, finite numbers, no cycles" checks.
- Everything else is a line-for-line translation.

## License

AGPL-3.0. The full license text is in `LICENSE`.

The character in `../../companion/sunee.avatar.json` (and any derivative
avatar definitions) is defined by this vendored runtime's avatar-definition
schema, which is part of the AGPL-3.0-covered upstream work.

**Combined-work notice:** while the companion component (which imports this
vendored runtime) is bundled into the application, the combined application
is distributed under AGPL-3.0 (see project README). If the companion module
and this vendor directory are removed from the bundle, the remainder of the
project returns to its pre-existing license.

## Files

| File | Origin |
|------|--------|
| `LICENSE` | upstream LICENSE (AGPL-3.0, verbatim) |
| `validation.js` | MIT-style permission shim (structural + semantic checks) replacing `avatarDefinition.ts` validation |
| `geometry.js` | avatar-core/src/geometry.ts (TS stripped) |
| `surfaces.js` | avatar-core/src/surfaces.ts (TS stripped) |
| `body.js` | avatar-core/src/body.ts (TS stripped) |
| `scene.js` | avatar-core/src/scene.ts (TS stripped) |
| `ambientMotion.js` | avatar-core/src/ambientMotion.ts (TS stripped) |
| `runtime.js` | avatar-core/src/runtime.ts (TS stripped) |
| `index.js` | barrel re-export |
| `Avatar.jsx` | avatar-react/src/Avatar.tsx (TS/JSX converted; default export added) |
| `styles.css` | avatar-react/src/styles.css (verbatim) |

Commit hash of the upstream source this was vendored from is recorded in the
installing session's notes; the upstream revision is 2026-09 (all packages at
0.1.0).

## Updating

To re-sync with upstream, re-apply the same TS-to-JS/JSX conversions listed
above and keep `validation.js` in step with `avatarDefinition.ts` semantics.

## Notices

- Copyright for the vendored sources remains with the upstream project
  authors. See upstream repository for author attribution.
- AGPL-3.0 section 13 (Remote Network Interaction) applies to deployments of
  the combined application while this code is bundled: users interacting
  with the deployment over a network must receive an offer of access to the
  Corresponding Source.