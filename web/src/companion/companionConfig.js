// Behavior configuration for the Sunee companion: one clean place for every
// rule the advanced interaction system follows. All animation names here must
// exist in sunee.avatar.json (lab sequences copied verbatim from the Avatar
// Lab studio document, plus 'gaze-follow', the project's own hold loop that
// powers the continuous gaze - see the capability notes at the bottom of
// this file). All section summaries are written from the actual text rendered
// in main.jsx bands, not invented.
//
// Message priority (higher wins when a bubble is already showing):
//   navigation 100 > intro 90 > manual click 60 > random fact 50 > inactivity 10

export const MESSAGE_PRIORITY = {
  navigation: 100,
  intro: 90,
  manual: 60,
  fact: 50,
  inactivity: 10,
}

export const BUBBLE_MS = 6_500
export const INTRO_BUBBLE_MS = 9_000

// ---- Initial introduction ------------------------------------------------
// Shows ~3 seconds after first load, once per session (sessionStorage flag).
export const INTRO_DELAY_MS = 3_000
export const INTRO_KEY = 'sunee-intro-shown'
export const introMessage = {
  priority: MESSAGE_PRIORITY.intro,
  animation: 'happy',
  text: "Hi! I'm Sunee 👋 I'll be your little guide through this project. Stick around - I'll show you some interesting things along the way!",
}

// ---- Cursor gaze (continuous) --------------------------------------------
// The Avatar Lab runtime has NO pointer/gaze tracking API (verified by
// grepping avatar-core, avatar-react and the Studio app: pointer events only
// drive the Studio's editor controls and 3D view orbit). So gaze-following is
// APPROXIMATED here, but continuously: while the cursor is close, a rAF loop
// eases the cursor's position within the range circle and writes a blended
// pose into the definition's 'gaze-live' expression slot (which the vendored
// runtime samples live every frame). Any cursor angle maps to a blend of the
// two nearest lab glance expressions, scaled by distance toward neutral - so
// the gaze direction is a continuous field, not a fixed set of directions.
export const gazeConfig = {
  enabled: true,
  // Distance from avatar center before Sunee pays attention.
  rangePx: 320,
  // Throttle between mousemove evaluations (the rAF loop eases between them).
  throttleMs: 200,
  // Per-frame easing toward the target pose (0..1, higher = snappier).
  easeFactor: 0.16,
  // After the cursor has been still this long, Sunee looks away (idle).
  steadyMs: 1_400,
  // Autonomous micro-blinks while gazing (the gaze hold disables blink).
  blink: { minMs: 2_600, maxMs: 6_200, durationMs: 170 },
  // Real lab glance expressions used as the blending anchors.
  guides: {
    up: 'upward-side-glance',
    down: 'downward-gaze',
    left: 'curious-left',
    right: 'far-right-glance',
  },
}

// ---- Inactivity emotion ladder -------------------------------------------
// Tiers climb gradually: each check advances at most ONE tier, so the avatar
// never jumps straight to angry. Emotion is expressed ONLY through animation
// (no speech bubbles for tiers themselves); the one inactivity bubble fires
// once per boredom cycle, only when the final tier is reached, at the lowest
// priority. Any activity resets the timer and (if the ladder had climbed)
// triggers a surprised or happy reaction before settling back to idle.
export const inactivityConfig = {
  checkIntervalMs: 4_000,
  tiers: [
    { key: 'bored', afterMs: 30_000, animation: 'bored' },
    { key: 'impatient', afterMs: 60_000, animation: 'suspicious' },
    { key: 'angry', afterMs: 120_000, animation: 'angry' },
  ],
  // Which events count as "activity" (reset the idle timer).
  activityEvents: ['mousemove', 'pointerdown', 'keydown', 'scroll', 'touchstart'],
  // Longest idle that still resets with a cheerful reaction vs a surprised one.
  surprisedReactionAfterMs: 180_000,
  reactionPlayMs: 2_400,
  // Fired once per boredom cycle when the angry tier is entered.
  inactivityMessage: {
    text: "I'm still here, no rush… you know where to find me. 🌙",
    animation: 'angry',
  },
}

// ---- Page navigation reactions -------------------------------------------
// Section summaries below are derived from the real copy rendered in
// main.jsx bands (About / Charts / Performance / References) and the
// simulator's purpose. '#' keys match the site-nav anchor ids; 'simulator'
// matches the external Streamlit link (target=_blank - no hashchange fires,
// so the companion listens for clicks on that anchor instead).
export const sectionSummaries = {
  about: {
    priority: MESSAGE_PRIORITY.navigation,
    animation: 'excited',
    text: 'About - 1,752,000 hourly readings from 200 synthetic consumers, distilled into 51 shape features and 4 archetypes. A simple way to find daily energy rhythms.',
  },
  charts: {
    priority: MESSAGE_PRIORITY.navigation,
    animation: 'excited',
    text: 'Charts - the matplotlib results rebuilt for the web: load-shape brush, K selection, PCA variance and cluster radar. K = 4 with a 0.328 silhouette.',
  },
  performance: {
    priority: MESSAGE_PRIORITY.navigation,
    animation: 'excited',
    text: 'Performance - the same PCA and K-Means kernels compiled to native C++ (optional engine), with scikit-learn kept as the scientific reference.',
  },
  references: {
    priority: MESSAGE_PRIORITY.navigation,
    animation: 'curious',
    text: 'References - the research behind the method: PCA (Abdi & Williams), silhouette (Rousseeuw), plus MacQueen, Davies-Bouldin and our Zephyr Station data weather API.',
  },
  simulator: {
    priority: MESSAGE_PRIORITY.navigation,
    animation: 'proud',
    text: 'Simulator - the interactive Streamlit app opens in a new tab: generate a synthetic year and run the whole pipeline live.',
  },
}

// ---- Random facts ---------------------------------------------------------
export const factConfig = {
  // Frequency of unsolicited facts during active usage.
  minIntervalMs: 45_000,
  maxIntervalMs: 90_000,
  // Don't offer a fact within this window after a navigation summary.
  holdOffAfterNavMs: 20_000,
  // Clicking the avatar shows a fact, but not more often than this.
  clickCooldownMs: 10_000,
  // People who ask for reduced motion see facts half as often (and get no
  // cursor gaze at all - see usePrefersReducedMotion in ProjectCompanion).
  reducedMotionIntervalMultiplier: 2,
}

// ---- Capability notes (verified against the lab, 2026-09) -----------------
// The Avatar Lab runs at C:\Users\Shantanu\Desktop\bible-strong-avatar-lab.
//   * Sunee's definition comes from src/features/studio/defaultStudioDocument.json
//     (expressions 00-24 + 23 built-in sequences). This project's
//     sunee.avatar.json mirrors 21 of those expressions and 13 sequences,
//     verbatim (parameter-for-parameter); "talking" IS the lab's "excited",
//     renamed for its fact-bubble role.
//   * The runtime exposes play(key) / setExpression(key) / stop() / pause()
//     and samples definition.expressions[activeExpression] live every frame -
//     that live sampling is what the continuous gaze approximation writes to
//     (the 'gaze-live' slot + the 'gaze-follow' hold loop in sunee.avatar.json).
//   * No cursor/gaze/eye-tracking exists in the lab (packages or Studio app),
//     so that behavior is approximated, not reused. Everything else here maps
//     to real, verified sequences.