"""The zoom hint: a small overlay that appears when a chart is zoomed in.

Plotly's reset gesture is a double-click, which is not discoverable. Every
figure in this project is zoomable, so a reader who drags a box on a chart can
end up stuck in a corner of it with no visible way back.

This puts a short-lived marker in the chart's top-right corner the moment a plot
stops showing its full range, and takes it away again when the view is reset.
Three rules shape it:

- It must not obstruct the chart. It is pointer-transparent, it sits in the
  corner rather than over the plotting area, and it fades itself out after a
  couple of seconds. Zoom again and it comes back.
- It must not look like a Streamlit alert. It uses the project's own graphite
  panel, cyan accent and mono face, with a gooey blob that rises and merges into
  the label - the SVG filter approach borrowed from the brief's component, with
  its colours moved onto the cyan/green accents used everywhere else here.
- It must not lie about the state. "Zoomed" is decided by measuring how much of
  each axis is on screen before a gesture and again after it: a view that got
  narrower is a zoom, a view that got wider is a reset, and a view that only
  moved is a pan. Asking whether an axis is on autorange would be wrong, because
  several figures here pin an explicit hour range and so start with it off; and
  comparing against the range the figure was built with would also be wrong,
  because an autoranged axis recomputes its padding whenever the container is
  resized, which no reader did.

Implementation note: Streamlit has no hook for page-level JavaScript, so the
script is delivered through a zero-height ``components.html`` frame and reaches
the app through ``window.parent``. That frame is same-origin, so this is a
supported access, but it means the listeners belong to a frame that is replaced
on every rerun. The teardown handle is therefore parked on the parent document
and called by the next frame before it installs its own, so listeners cannot
accumulate.
"""
from __future__ import annotations

import streamlit as st
import streamlit.components.v1 as components

from dashboard_ui import CYAN, GREEN, INK, MIDNIGHT, MIST

# How long the marker stays before fading, in milliseconds. Long enough to read
# two short lines, short enough that it is gone before it becomes furniture.
HOLD_MS = 2800

ZOOMED_LABEL = "ZOOMED_DATA"
RESET_LABEL = "DOUBLE-CLICK TO RESET"

_CSS = f"""
[data-testid="stPlotlyChart"] {{ position: relative; }}

.zoomhint {{
  position: absolute; top: 10px; right: 14px; z-index: 6;
  display: flex; flex-direction: column; align-items: flex-end;
  pointer-events: none; user-select: none; -webkit-user-select: none;
  opacity: 0; transition: opacity 0.3s ease;
  filter: url("#zoomhint-goo");
}}
.zoomhint.on {{ opacity: 1; }}

/* The blob. It starts below the label and small, then rises into it; the goo
   filter on the wrapper makes the two read as one piece of matter. */
.zoomhint .singularity {{
  position: absolute; top: 4px; right: 12px;
  width: 40px; height: 40px; border-radius: 50%;
  background: {MIDNIGHT}; opacity: 0;
  transform: translateY(26px) scale(0.12);
  transition: transform 0.6s cubic-bezier(0.34, 1.56, 0.64, 1), opacity 0.4s ease;
}}
.zoomhint.on .singularity {{ opacity: 1; transform: translateY(0) scale(1); }}
.zoomhint .singularity::before {{
  content: ""; position: absolute; inset: -4px; border-radius: 50%;
  background: conic-gradient(from 0deg, {CYAN}, {GREEN}, {CYAN});
  z-index: -1; filter: blur(9px); opacity: 0;
  animation: zoomhint-rotate 2.4s linear infinite;
  transition: opacity 0.4s ease;
}}
.zoomhint.on .singularity::before {{ opacity: 0.7; }}

.zoomhint .horizon {{
  position: relative; z-index: 2; text-align: right;
  background: {MIDNIGHT}; border-radius: 10px; padding: 9px 14px 10px 14px;
}}
.zoomhint .z-title {{
  font-family: "IBM Plex Mono", monospace; font-weight: 700;
  font-size: 0.62rem; letter-spacing: 0.24em; color: {CYAN};
  text-shadow: 0 0 10px rgba(59, 201, 222, 0.55);
}}
.zoomhint .z-sub {{
  font-family: "IBM Plex Mono", monospace; font-size: 0.56rem;
  letter-spacing: 0.16em; color: {INK}; opacity: 0.8; margin-top: 3px;
}}

@keyframes zoomhint-rotate {{ from {{ transform: rotate(0deg); }} to {{ transform: rotate(360deg); }} }}

/* Reduced motion keeps the marker and loses the choreography. */
@media (prefers-reduced-motion: reduce) {{
  .zoomhint .singularity,
  .zoomhint.on .singularity {{ transform: none; transition: opacity 0.2s ease; }}
  .zoomhint .singularity::before {{ animation: none; }}
}}

@media (max-width: 640px) {{
  .zoomhint {{ top: 6px; right: 8px; }}
  .zoomhint .z-sub {{ color: {MIST}; }}
}}
"""

# The gooey merge: blur, push the alpha through a steep ramp so the blurred
# shapes gain hard edges where they overlap, then lay the crisp source back on
# top so the text stays readable.
_SVG = """
<svg id="zoomhint-defs" aria-hidden="true"
     style="position:absolute;width:0;height:0;overflow:hidden">
  <defs>
    <filter id="zoomhint-goo">
      <feGaussianBlur in="SourceGraphic" stdDeviation="9" result="blur"></feGaussianBlur>
      <feColorMatrix in="blur" values="1 0 0 0 0  0 1 0 0 0  0 0 1 0 0  0 0 0 18 -7"
                     result="goo"></feColorMatrix>
      <feComposite in="SourceGraphic" in2="goo" operator="atop"></feComposite>
    </filter>
  </defs>
</svg>
"""

_JS = """
(function () {
  var doc;
  try { doc = window.parent.document; } catch (err) { return; }
  if (!doc || !doc.body) { return; }

  var HOLD = __HOLD__;

  // A previous frame's listeners still hold this document. Their closures are
  // gone, so hand the teardown back before installing new ones.
  if (typeof doc.__zoomhintTeardown === "function") {
    try { doc.__zoomhintTeardown(); } catch (err) {}
  }

  if (!doc.getElementById("zoomhint-css")) {
    var style = doc.createElement("style");
    style.id = "zoomhint-css";
    style.textContent = __CSS__;
    doc.head.appendChild(style);
  }
  if (!doc.getElementById("zoomhint-defs")) {
    var holder = doc.createElement("div");
    holder.innerHTML = __SVG__;
    doc.body.appendChild(holder.firstElementChild);
  }

  function marker(gd) {
    var host = gd.closest('[data-testid="stPlotlyChart"]') || gd.parentElement;
    if (!host) { return null; }
    var hint = host.querySelector(".zoomhint");
    if (!hint) {
      hint = doc.createElement("div");
      hint.className = "zoomhint";
      // Decorative. It restates a mouse gesture and is only ever triggered by
      // that same gesture, so it can tell a screen-reader user nothing they
      // could act on, while interrupting them on every drag.
      hint.setAttribute("aria-hidden", "true");
      hint.innerHTML =
        '<div class="singularity"></div>' +
        '<div class="horizon">' +
        '<div class="z-title">__ZOOMED__</div>' +
        '<div class="z-sub">__RESET__</div></div>';
      host.appendChild(hint);
    }
    return hint;
  }

  // How much of each axis is on screen. Spans, not endpoints: the question is
  // whether the reader is looking at less of the chart than they were.
  function spans(gd) {
    var full = gd._fullLayout;
    if (!full) { return null; }
    var out = {};
    Object.keys(full).forEach(function (key) {
      if (!/^[xy]axis\\d*$/.test(key)) { return; }
      var axis = full[key];
      if (!axis || !axis.range) { return; }
      var lo = axis.range[0], hi = axis.range[1];
      if (typeof lo !== "number") { lo = Date.parse(lo); hi = Date.parse(hi); }
      if (!isFinite(lo) || !isFinite(hi)) { return; }
      out[key] = Math.abs(hi - lo);
    });
    return out;
  }

  // 1 zoomed in, -1 zoomed out or reset, 0 no meaningful change. The threshold
  // absorbs the sub-pixel drift an autoranged axis picks up when its container
  // is resized, which is not something the reader did.
  function verdict(before, after) {
    if (!before || !after) { return 0; }
    var narrower = 0, wider = 0;
    Object.keys(after).forEach(function (key) {
      var was = before[key], now = after[key];
      if (was == null || !isFinite(was) || was === 0) { return; }
      var change = (now - was) / was;
      if (change < -0.005) { narrower += 1; }
      else if (change > 0.005) { wider += 1; }
    });
    if (!narrower && !wider) { return 0; }
    return narrower >= wider ? 1 : -1;
  }

  function show(hint) {
    if (!hint) { return; }
    hint.classList.add("on");
    window.clearTimeout(hint.__timer);
    hint.__timer = window.setTimeout(function () {
      hint.classList.remove("on");
    }, HOLD);
  }

  function hide(hint) {
    if (!hint) { return; }
    window.clearTimeout(hint.__timer);
    hint.classList.remove("on");
  }

  function plotUnder(node) {
    if (!node || typeof node.closest !== "function") { return null; }
    return node.closest(".js-plotly-plot");
  }

  // The figure the gesture in progress belongs to. A box zoom that ends with the
  // pointer off the chart - over the sidebar, or outside the window - still
  // applies, but its mouseup lands somewhere else, so the figure has to be
  // remembered rather than looked up again at the end.
  var active = null;

  // Before the gesture: what was on screen. Recorded per gesture rather than
  // once at load, because an autoranged axis recomputes its padding whenever the
  // container changes width, and that drift would otherwise read as a zoom.
  function onStart(event) {
    var gd = plotUnder(event.target);
    if (!gd) { return; }
    active = gd;
    gd.__zhPre = spans(gd);
  }

  // After it: the change in span decides, so a reset cannot be mistaken for a
  // zoom and a pan - which moves the view without narrowing it - says nothing.
  function onEnd(event) {
    var gd = plotUnder(event.target) || active;
    if (!gd) { return; }
    window.setTimeout(function () {
      var moved = verdict(gd.__zhPre, spans(gd));
      if (moved > 0) { show(marker(gd)); }
      else if (moved < 0) { hide(marker(gd)); }
    }, 70);
  }

  doc.addEventListener("mousedown", onStart, true);
  doc.addEventListener("wheel", onStart, true);
  doc.addEventListener("mouseup", onEnd, true);
  doc.addEventListener("wheel", onEnd, false);
  doc.addEventListener("dblclick", onEnd, true);

  doc.__zoomhintTeardown = function () {
    doc.removeEventListener("mousedown", onStart, true);
    doc.removeEventListener("wheel", onStart, true);
    doc.removeEventListener("mouseup", onEnd, true);
    doc.removeEventListener("wheel", onEnd, false);
    doc.removeEventListener("dblclick", onEnd, true);
  };
})();
"""


def _script() -> str:
    """The delivered script, with the Python-side constants folded in."""
    import json

    return (
        _JS.replace("__HOLD__", str(int(HOLD_MS)))
        .replace("__CSS__", json.dumps(_CSS))
        .replace("__SVG__", json.dumps(_SVG))
        .replace("__ZOOMED__", ZOOMED_LABEL)
        .replace("__RESET__", RESET_LABEL)
    )


def payload() -> str:
    """The full frame contents. Exposed so a test can read it without a browser."""
    return f"<script>{_script()}</script>"


def inject() -> None:
    """Install the zoom hint for this run. Safe to call on every rerun."""
    components.html(payload(), height=0)
