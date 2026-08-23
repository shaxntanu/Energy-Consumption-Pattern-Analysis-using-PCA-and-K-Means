"""Design system for the Streamlit dashboard.

One place for the visual language: colour tokens, the injected CSS (typography,
layout chrome, components) and a Plotly template so every chart speaks the same
palette.

The organising idea is the shape of the day. Every chart in this project has the
hour of the day on its x-axis, and the clusters differ by *when* people use
energy, not how much, so the interface is built around a 24-hour load curve and
a faint four-band shading (night, morning, afternoon, evening) behind every hour
axis. That motif, not a logo, is the signature.

Two colour ideas sit on top of that:

- The instrument's own accent is an electric cyan. It marks anything the reader
  acts on: links, focus rings, section rules, the primary controls. Energy green
  is the second accent and is reserved for validation and agreement.
- The load curve itself is coloured on a temperature ramp, cool indigo for the
  small hours through to warm amber at the evening peak. Amber and indigo are
  kept for that ramp and for warnings, so they never compete with the cyan of
  the chrome.

Cluster identity is always colour *and* label, never colour alone, so the
qualitative cluster palette is a distinct-hue set rather than an ordered ramp.

Nothing here computes or changes a result. It only decides how the numbers that
the pipeline already produced are shown.
"""
from __future__ import annotations

from typing import Iterable, Sequence

import plotly.graph_objects as go
import plotly.io as pio
import streamlit as st

# --- Colour tokens -----------------------------------------------------------
# Surfaces run from the graphite canvas up through raised panels.
MIDNIGHT = "#0B0E14"    # app background, the darkest surface
PANEL = "#141A24"       # raised surface: cards, sidebar
PANEL_HI = "#1B2230"    # hover / nested surface
LINE = "#262E3D"        # hairline rules and borders
INK = "#EAECEF"         # primary text
MIST = "#8A93A6"        # secondary text, captions, axis ticks
SLATE = "#5B657A"       # tertiary text, disabled

# Accents. CYAN is the brand and the interactive colour; GREEN is validation.
CYAN = "#3BC9DE"        # primary accent: links, focus, section rules, controls
CYAN_DEEP = "#1E9DB2"   # pressed / hover on the primary
GREEN = "#4FD1A5"       # secondary accent: agreement, validation, positive
GREEN_DEEP = "#2FA980"

# Reserved. AMBER and INDIGO are the poles of the load-curve temperature ramp
# (indigo = the small hours, amber = the evening peak) and stand in for warnings.
INDIGO = "#6C8CFF"      # night end of the ramp
AMBER = "#F5A524"       # peak end of the ramp, and caution
AMBER_DEEP = "#E0871B"
ROSE = "#F26D6D"        # negative deviation, error
VIOLET = "#B085F5"      # extra qualitative hue

# Qualitative palette for cluster IDs. Cluster numbers are arbitrary, so this is
# a distinct-hue set rather than an ordered ramp. It deliberately does not lead
# with the brand cyan alone, so a cluster is never mistaken for a control.
CLUSTER_COLORS: tuple[str, ...] = (AMBER, CYAN, VIOLET, GREEN, ROSE, INDIGO)

# The load-curve temperature ramp: cool night through warm evening peak. Used
# for the single population/hero curve where hour maps to colour. Cluster curves
# use their qualitative cluster colour instead.
DAY_RAMP: tuple[tuple[float, str], ...] = (
    (0.0, INDIGO),
    (0.35, CYAN),
    (0.62, GREEN),
    (1.0, AMBER),
)

# Four day-parts, each a start hour, end hour, label and faint fill. These are
# the shading behind every hour axis and the definition of the *_share features.
PERIODS: tuple[tuple[int, int, str, str], ...] = (
    (0, 6, "Night", "rgba(108,140,255,0.05)"),
    (6, 12, "Morning", "rgba(59,201,222,0.05)"),
    (12, 18, "Afternoon", "rgba(79,209,165,0.05)"),
    (18, 24, "Evening", "rgba(245,165,36,0.07)"),
)

_TEMPLATE_NAME = "energy_dark"


def cluster_color(i: int) -> str:
    """Colour for a cluster ID, wrapping if there are more clusters than hues."""
    return CLUSTER_COLORS[int(i) % len(CLUSTER_COLORS)]


def register_plotly_template() -> None:
    """Register and activate the shared dark Plotly template.

    Idempotent: registering the same template twice is harmless, and setting it
    as the default means px/go figures created afterwards inherit it without
    every call site repeating the styling.
    """
    template = go.layout.Template(
        layout=dict(
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            font=dict(family="Inter, system-ui, sans-serif", color=INK, size=13),
            title=dict(font=dict(family="Space Grotesk, sans-serif", size=18, color=INK), x=0.0, xanchor="left"),
            colorway=list(CLUSTER_COLORS),
            xaxis=dict(
                gridcolor="rgba(255,255,255,0.05)", zerolinecolor="rgba(255,255,255,0.10)",
                linecolor=LINE, tickfont=dict(family="IBM Plex Mono, monospace", size=11, color=MIST),
                title=dict(font=dict(family="IBM Plex Mono, monospace", size=12, color=MIST)),
            ),
            yaxis=dict(
                gridcolor="rgba(255,255,255,0.05)", zerolinecolor="rgba(255,255,255,0.10)",
                linecolor=LINE, tickfont=dict(family="IBM Plex Mono, monospace", size=11, color=MIST),
                title=dict(font=dict(family="IBM Plex Mono, monospace", size=12, color=MIST)),
            ),
            legend=dict(bgcolor="rgba(0,0,0,0)", font=dict(size=12, color=MIST),
                        bordercolor=LINE),
            margin=dict(l=54, r=24, t=54, b=48),
            colorscale=dict(sequential=[[pos, col] for pos, col in DAY_RAMP]),
            hoverlabel=dict(bgcolor=PANEL, bordercolor=LINE,
                            font=dict(family="Inter, sans-serif", color=INK, size=12)),
        )
    )
    pio.templates[_TEMPLATE_NAME] = template
    pio.templates.default = f"plotly_dark+{_TEMPLATE_NAME}"


def add_time_of_day_bands(fig: go.Figure) -> go.Figure:
    """Shade the four day-parts behind an hour-of-day x-axis.

    This is the recurring signature that ties every hourly chart together. It
    always draws the four bands across the full plot height, so only call it on a
    figure whose x-axis really is the hour of the day (0..23); on any other axis
    the bands would be meaningless.

    Args:
        fig: A figure whose x-axis is the hour of the day (0..23).

    Returns:
        The same figure, with band rectangles and small labels added.
    """
    for start, end, label, fill in PERIODS:
        fig.add_vrect(
            x0=start, x1=end, fillcolor=fill, line_width=0, layer="below",
            annotation_text=label, annotation_position="top left",
            annotation=dict(font=dict(family="IBM Plex Mono, monospace", size=9, color=MIST)),
        )
    return fig


def _fonts_and_variables() -> str:
    """Font import and CSS custom properties shared by every rule below."""
    return f"""
@import url('https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@400;500;600;700&family=Inter:wght@400;500;600&family=IBM+Plex+Mono:wght@400;500;600&display=swap');
:root {{
  --midnight: {MIDNIGHT}; --panel: {PANEL}; --panel-hi: {PANEL_HI};
  --line: {LINE}; --ink: {INK}; --mist: {MIST}; --slate: {SLATE};
  --cyan: {CYAN}; --cyan-deep: {CYAN_DEEP}; --green: {GREEN}; --green-deep: {GREEN_DEEP};
  --indigo: {INDIGO}; --amber: {AMBER}; --amber-deep: {AMBER_DEEP}; --rose: {ROSE};
  --display: 'Space Grotesk', system-ui, sans-serif;
  --body: 'Inter', system-ui, sans-serif;
  --mono: 'IBM Plex Mono', ui-monospace, monospace;
}}
"""


def _css() -> str:
    """The full stylesheet. Split into font/variable and rule halves only so the
    f-string braces stay readable; the rule half is a plain string."""
    return _fonts_and_variables() + """
/* Base typography ------------------------------------------------------- */
html, body, [data-testid="stAppViewContainer"], [data-testid="stMarkdownContainer"] {
  font-family: var(--body);
  color: var(--ink);
}
[data-testid="stAppViewContainer"] { background: var(--midnight); }
.block-container { padding-top: 2.2rem; padding-bottom: 4rem; max-width: 1180px; }
h1, h2, h3, h4 { font-family: var(--display); letter-spacing: -0.02em; color: var(--ink); }
p, li { line-height: 1.62; }
a { color: var(--cyan); text-decoration: none; }
a:hover { text-decoration: underline; }

/* Hide Streamlit chrome but keep the sidebar toggle usable --------------- */
#MainMenu, [data-testid="stToolbar"], [data-testid="stDecoration"], footer { visibility: hidden; }
[data-testid="stHeader"] { background: transparent; }

/* Sidebar --------------------------------------------------------------- */
[data-testid="stSidebar"] { background: var(--panel); border-right: 1px solid var(--line); }
[data-testid="stSidebar"] .block-container { padding-top: 1.5rem; }
[data-testid="stSidebar"] h1, [data-testid="stSidebar"] h2, [data-testid="stSidebar"] h3 {
  font-size: 0.74rem; text-transform: uppercase; letter-spacing: 0.2em;
  font-family: var(--mono); color: var(--mist); font-weight: 600;
}

/* Kicker / eyebrow ------------------------------------------------------ */
.kicker {
  font-family: var(--mono); font-size: 0.72rem; font-weight: 600;
  text-transform: uppercase; letter-spacing: 0.22em; color: var(--cyan);
  display: inline-block; margin-bottom: 0.6rem;
}

/* Hero ------------------------------------------------------------------ */
.hero { padding: 0.4rem 0 1.6rem 0; border-bottom: 1px solid var(--line); margin-bottom: 1.8rem; }
.hero h1 {
  font-size: clamp(2.4rem, 5.5vw, 4rem); font-weight: 700; line-height: 1.03;
  margin: 0 0 0.9rem 0;
}
.hero .lede { font-size: clamp(1rem, 1.6vw, 1.2rem); color: var(--mist); max-width: 62ch; margin: 0; }
.hero .accent { color: var(--cyan); }

/* Section headers ------------------------------------------------------- */
.section { margin: 2.4rem 0 1.1rem 0; }
.section h2 { font-size: clamp(1.4rem, 2.6vw, 1.9rem); font-weight: 600; margin: 0.2rem 0 0.4rem 0; }
.section .lede { color: var(--mist); max-width: 70ch; margin: 0; }

/* Metric cards ---------------------------------------------------------- */
.metric-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(150px, 1fr)); gap: 0.85rem; margin: 0.4rem 0 0.6rem 0; }
.metric-card {
  background: var(--panel); border: 1px solid var(--line); border-radius: 14px;
  padding: 1rem 1.1rem; transition: transform 0.18s ease, border-color 0.18s ease;
}
.metric-card:hover { transform: translateY(-2px); border-color: var(--cyan-deep); }
.metric-card .label {
  font-family: var(--mono); font-size: 0.68rem; text-transform: uppercase;
  letter-spacing: 0.14em; color: var(--mist); margin-bottom: 0.5rem;
}
.metric-card .value {
  font-family: var(--display); font-size: 1.9rem; font-weight: 600; color: var(--ink);
  line-height: 1; font-feature-settings: 'tnum' 1; font-variant-numeric: tabular-nums;
}
.metric-card .sub { font-family: var(--mono); font-size: 0.72rem; color: var(--mist); margin-top: 0.45rem; }
.metric-card.accent { border-left: 3px solid var(--cyan); }

/* Synthetic-data badge -------------------------------------------------- */
.badge-synthetic {
  display: inline-flex; align-items: center; gap: 0.5rem;
  background: rgba(245,165,36,0.10); border: 1px solid rgba(245,165,36,0.35);
  color: var(--amber); font-family: var(--mono); font-size: 0.72rem;
  text-transform: uppercase; letter-spacing: 0.12em; font-weight: 600;
  padding: 0.4rem 0.8rem; border-radius: 999px;
}
.badge-synthetic::before { content: ""; width: 7px; height: 7px; border-radius: 50%; background: var(--amber); }

/* Tag / chip ------------------------------------------------------------ */
.tag {
  display: inline-block; font-family: var(--mono); font-size: 0.68rem;
  letter-spacing: 0.1em; text-transform: uppercase; color: var(--mist);
  border: 1px solid var(--line); border-radius: 999px; padding: 0.2rem 0.65rem;
  margin: 0 0.35rem 0.35rem 0;
}

/* Panels and rules ------------------------------------------------------ */
.panel { background: var(--panel); border: 1px solid var(--line); border-radius: 14px; padding: 1.2rem 1.3rem; }
.hairline { border: none; border-top: 1px solid var(--line); margin: 1.8rem 0; }
.note {
  border-left: 3px solid var(--cyan); background: var(--panel);
  padding: 0.85rem 1.1rem; border-radius: 0 10px 10px 0; color: var(--mist);
}
.note strong { color: var(--ink); }
.note.warn { border-left-color: var(--amber); }

/* Archetype (cluster identity) card ------------------------------------- */
.arch-card {
  background: var(--panel); border: 1px solid var(--line); border-radius: 14px;
  padding: 1.1rem 1.2rem; border-top: 3px solid var(--swatch, var(--cyan));
  height: 100%;
}
.arch-card .arch-name {
  font-family: var(--display); font-weight: 600; font-size: 1.15rem; color: var(--ink);
  display: flex; align-items: center; gap: 0.55rem; margin-bottom: 0.15rem;
}
.arch-card .arch-name .dot { width: 11px; height: 11px; border-radius: 50%; background: var(--swatch, var(--cyan)); flex: none; }
.arch-card .arch-meta { font-family: var(--mono); font-size: 0.72rem; color: var(--mist); margin-bottom: 0.7rem; }
.arch-card ul { margin: 0; padding-left: 1.05rem; }
.arch-card li { font-size: 0.85rem; color: var(--ink); margin-bottom: 0.3rem; line-height: 1.5; }
.arch-card li span { color: var(--mist); }

/* Numbered step card (the quickstart) ------------------------------------ */
.step-card {
  background: var(--panel); border: 1px solid var(--line); border-radius: 14px;
  padding: 1.1rem 1.2rem; height: 100%; position: relative;
}
.step-card .step-n {
  font-family: var(--mono); font-size: 0.72rem; letter-spacing: 0.14em;
  color: var(--cyan); font-variant-numeric: tabular-nums; margin-bottom: 0.5rem;
  user-select: none;
}
.step-card .step-t {
  font-family: var(--display); font-weight: 600; font-size: 1.05rem;
  color: var(--ink); margin-bottom: 0.4rem; line-height: 1.25;
}
.step-card .step-b { font-size: 0.85rem; color: var(--mist); line-height: 1.55; }

/* Four-part insight block ----------------------------------------------- */
.insight { background: var(--panel); border: 1px solid var(--line); border-radius: 14px; padding: 1.15rem 1.25rem; margin-bottom: 0.9rem; }
.insight .insight-head { font-family: var(--display); font-weight: 600; font-size: 1.05rem; color: var(--ink); margin-bottom: 0.75rem; display: flex; align-items: center; gap: 0.5rem; }
.insight .insight-head .dot { width: 10px; height: 10px; border-radius: 50%; background: var(--swatch, var(--cyan)); }
.insight .row { display: grid; grid-template-columns: 128px 1fr; gap: 0.6rem 1rem; padding: 0.4rem 0; border-top: 1px solid var(--line); }
.insight .row:first-of-type { border-top: none; }
.insight .k { font-family: var(--mono); font-size: 0.66rem; letter-spacing: 0.14em; text-transform: uppercase; color: var(--mist); padding-top: 0.1rem; }
.insight .k.obs { color: var(--cyan); }
.insight .k.ev { color: var(--mist); }
.insight .k.interp { color: var(--green); }
.insight .k.act { color: var(--amber); }
.insight .v { font-size: 0.9rem; color: var(--ink); line-height: 1.55; }
.insight .v.mono { font-family: var(--mono); font-size: 0.82rem; color: var(--mist); }

/* Research reference card ----------------------------------------------- */
.research { display: grid; grid-template-columns: repeat(auto-fit, minmax(320px, 1fr)); gap: 0.9rem; }
.ref-card { background: var(--panel); border: 1px solid var(--line); border-radius: 14px; padding: 1.15rem 1.25rem; }
.ref-card .ref-title { font-family: var(--display); font-weight: 600; font-size: 1rem; color: var(--ink); line-height: 1.35; margin-bottom: 0.3rem; }
.ref-card .ref-authors { font-size: 0.82rem; color: var(--mist); margin-bottom: 0.7rem; }
.ref-card .ref-grid { display: grid; grid-template-columns: 84px 1fr; gap: 0.3rem 0.8rem; margin-bottom: 0.7rem; }
.ref-card .ref-grid .rk { font-family: var(--mono); font-size: 0.64rem; letter-spacing: 0.12em; text-transform: uppercase; color: var(--slate); padding-top: 0.12rem; }
.ref-card .ref-grid .rv { font-size: 0.82rem; color: var(--ink); }
.ref-card .ref-why { font-size: 0.85rem; color: var(--mist); line-height: 1.55; border-top: 1px solid var(--line); padding-top: 0.7rem; }
.ref-card a { font-family: var(--mono); font-size: 0.74rem; }

/* Pipeline stepper (a genuine sequence, so numbered) -------------------- */
.pipe { display: grid; grid-template-columns: repeat(auto-fit, minmax(150px, 1fr)); gap: 0.7rem; }
.pipe .step { background: var(--panel); border: 1px solid var(--line); border-radius: 12px; padding: 0.9rem 1rem; }
.pipe .step .n { font-family: var(--mono); font-size: 0.72rem; color: var(--cyan); letter-spacing: 0.1em; }
.pipe .step .t { font-family: var(--display); font-weight: 600; margin-top: 0.3rem; color: var(--ink); }
.pipe .step .d { font-size: 0.82rem; color: var(--mist); margin-top: 0.25rem; line-height: 1.45; }

/* Masthead -------------------------------------------------------------- */
/* The band that used to be the landing page's top navigation. It carries
   identity and the outbound links only; the page nav itself lives in the
   sidebar, so there is one place to change pages and no competing menus. */
.masthead {
  display: flex; align-items: center; gap: 1rem; flex-wrap: wrap;
  padding: 0.55rem 0 0.9rem 0; margin-bottom: 1.4rem;
  border-bottom: 1px solid var(--line);
}
.masthead .brand {
  font-family: var(--display); font-weight: 600; font-size: 0.95rem;
  color: var(--ink); display: flex; align-items: center; gap: 0.5rem;
  letter-spacing: -0.01em;
}
.masthead .brand .slash {
  font-family: var(--mono); color: var(--cyan); font-weight: 500; font-size: 1.05rem;
}
.masthead .where {
  font-family: var(--mono); font-size: 0.68rem; letter-spacing: 0.16em;
  text-transform: uppercase; color: var(--slate);
  padding-left: 1rem; border-left: 1px solid var(--line);
}
.masthead .where b { color: var(--mist); font-weight: 500; }
.masthead .spacer { flex: 1 1 auto; }
.masthead .out {
  font-family: var(--mono); font-size: 0.7rem; letter-spacing: 0.1em;
  text-transform: uppercase; color: var(--mist);
  border: 1px solid var(--line); border-radius: 999px; padding: 0.34rem 0.8rem;
  transition: color 0.18s ease, border-color 0.18s ease, background 0.18s ease;
}
.masthead .out:hover {
  color: var(--cyan); border-color: var(--cyan-deep);
  background: rgba(59,201,222,0.07); text-decoration: none;
}

/* Story chapters -------------------------------------------------------- */
/* Numbered because the study genuinely is a sequence: each chapter depends on
   the one before it. The number is information, not ornament. */
.chapter { margin: 2.6rem 0 1.2rem 0; }
.chapter .ch-head { display: flex; align-items: baseline; gap: 1rem; }
.chapter .ch-n {
  font-family: var(--mono); font-size: 0.78rem; font-weight: 600; color: var(--cyan);
  letter-spacing: 0.1em; padding-top: 0.15rem; flex: none;
  font-variant-numeric: tabular-nums;
}
.chapter .ch-kicker {
  font-family: var(--mono); font-size: 0.7rem; font-weight: 600;
  text-transform: uppercase; letter-spacing: 0.22em; color: var(--mist);
}
.chapter h2 {
  font-size: clamp(1.5rem, 2.9vw, 2.1rem); font-weight: 600;
  margin: 0.35rem 0 0.7rem 0; line-height: 1.12;
}
.chapter .ch-body { color: var(--mist); font-size: 1.02rem; max-width: 68ch; margin: 0; }
.chapter .ch-body strong { color: var(--ink); font-weight: 600; }
.chapter .ch-body em { color: var(--ink); font-style: italic; }
.chapter .ch-indent { padding-left: 2.6rem; }
@media (max-width: 640px) { .chapter .ch-indent { padding-left: 0; } }

/* Footer ---------------------------------------------------------------- */
.foot {
  margin-top: 3rem; padding-top: 1.2rem; border-top: 1px solid var(--line);
  display: flex; flex-wrap: wrap; gap: 0.6rem 1.4rem; align-items: baseline;
}
.foot .f-run { font-family: var(--mono); font-size: 0.72rem; color: var(--slate); }
.foot .f-line { font-size: 0.86rem; color: var(--mist); }
.foot .spacer { flex: 1 1 auto; }

/* Sidebar navigation ---------------------------------------------------- */
/* Buttons rather than a radio, so the pages can be grouped under real
   headings. Streamlit's own button semantics are kept, so each item is still a
   focusable, keyboard-operable control. */
.nav-group {
  font-family: var(--mono); font-size: 0.63rem; font-weight: 600;
  text-transform: uppercase; letter-spacing: 0.2em; color: var(--slate);
  margin: 1.1rem 0 0.35rem 0;
}
.nav-group:first-of-type { margin-top: 0.2rem; }
[data-testid="stSidebar"] .stButton > button {
  background: transparent; color: var(--mist); border: none;
  border-left: 2px solid transparent; border-radius: 0 6px 6px 0;
  font-family: var(--body); font-size: 0.86rem; font-weight: 500;
  text-align: left; justify-content: flex-start;
  padding: 0.34rem 0.7rem; width: 100%; min-height: 0;
  transition: color 0.15s ease, background 0.15s ease, border-color 0.15s ease;
}
[data-testid="stSidebar"] .stButton > button:hover {
  background: var(--panel-hi); color: var(--ink); border-left-color: var(--slate);
}
[data-testid="stSidebar"] .stButton > button[kind="primary"],
[data-testid="stSidebar"] .stButton > button[data-testid="stBaseButton-primary"] {
  background: rgba(59,201,222,0.09); color: var(--cyan);
  border-left-color: var(--cyan); font-weight: 600;
}
[data-testid="stSidebar"] .stButton > button[kind="primary"]:hover,
[data-testid="stSidebar"] .stButton > button[data-testid="stBaseButton-primary"]:hover {
  background: rgba(59,201,222,0.14); color: var(--cyan);
}
[data-testid="stSidebar"] [data-testid="stVerticalBlock"] { gap: 0.12rem; }

/* Streamlit widgets ----------------------------------------------------- */
[data-testid="stDataFrame"] { border: 1px solid var(--line); border-radius: 12px; }
.stRadio > label, .stSelectbox label, .stSlider label, .stMultiSelect label { color: var(--mist) !important; font-family: var(--mono); font-size: 0.8rem; }
.stButton > button {
  background: var(--cyan); color: var(--midnight); border: none; border-radius: 10px;
  font-family: var(--body); font-weight: 600; padding: 0.5rem 1.1rem;
}
.stButton > button:hover { background: var(--cyan-deep); color: var(--midnight); }
[data-testid="stMetricValue"] { font-family: var(--display); font-variant-numeric: tabular-nums; }

/* Accessibility --------------------------------------------------------- */
*:focus-visible { outline: 2px solid var(--cyan); outline-offset: 2px; }
@media (prefers-reduced-motion: reduce) { .metric-card { transition: none; } }
@media (max-width: 640px) { .block-container { padding-left: 1rem; padding-right: 1rem; } .insight .row { grid-template-columns: 1fr; gap: 0.2rem; } }
"""


def inject_theme() -> None:
    """Inject the design system. Call once, first thing on every page."""
    st.markdown(f"<style>{_css()}</style>", unsafe_allow_html=True)
    register_plotly_template()


# --- HTML component helpers --------------------------------------------------
# Each returns nothing and writes directly, so pages read as a sequence of
# calls. All user-facing strings are the caller's; these only wrap structure.

def hero(title_html: str, lede: str) -> None:
    """Page hero. The kicker is separate so callers control the eyebrow."""
    st.markdown(
        f'<div class="hero"><h1>{title_html}</h1><p class="lede">{lede}</p></div>',
        unsafe_allow_html=True,
    )


def kicker(text: str) -> None:
    """Uppercase mono eyebrow label."""
    st.markdown(f'<span class="kicker">{text}</span>', unsafe_allow_html=True)


def section(title: str, lede: str = "", eyebrow: str = "") -> None:
    """Section header with an optional eyebrow and one-line description."""
    parts = ['<div class="section">']
    if eyebrow:
        parts.append(f'<span class="kicker">{eyebrow}</span>')
    parts.append(f"<h2>{title}</h2>")
    if lede:
        parts.append(f'<p class="lede">{lede}</p>')
    parts.append("</div>")
    st.markdown("".join(parts), unsafe_allow_html=True)


def metric_cards(items: Sequence[dict]) -> None:
    """Row of metric cards.

    Args:
        items: dicts with 'label', 'value' and optional 'sub' and 'accent'.
    """
    cards = []
    for it in items:
        cls = "metric-card accent" if it.get("accent") else "metric-card"
        sub = f'<div class="sub">{it["sub"]}</div>' if it.get("sub") else ""
        cards.append(
            f'<div class="{cls}"><div class="label">{it["label"]}</div>'
            f'<div class="value">{it["value"]}</div>{sub}</div>'
        )
    st.markdown(f'<div class="metric-grid">{"".join(cards)}</div>', unsafe_allow_html=True)


def synthetic_badge(text: str = "Synthetic data") -> None:
    """The standing reminder that none of these consumers are real."""
    st.markdown(f'<span class="badge-synthetic">{text}</span>', unsafe_allow_html=True)


def tags(labels: Iterable[str]) -> None:
    """A row of small mono chips, for feature groups or run facts."""
    chips = "".join(f'<span class="tag">{t}</span>' for t in labels)
    st.markdown(chips, unsafe_allow_html=True)


def note(html: str, warn: bool = False) -> None:
    """A ruled aside for caveats and context. Cyan by default, amber for warn."""
    cls = "note warn" if warn else "note"
    st.markdown(f'<div class="{cls}">{html}</div>', unsafe_allow_html=True)


def hairline() -> None:
    """A thin horizontal rule."""
    st.markdown('<hr class="hairline" />', unsafe_allow_html=True)


def archetype_card(name: str, color: str, meta: str, bullets: Sequence[str]) -> None:
    """A cluster identity card: colour swatch, name, one meta line, and bullets.

    Args:
        name: Cluster name, e.g. "Evening-Peaking".
        color: The cluster's qualitative colour (see cluster_color).
        meta: A single mono line, e.g. "49 consumers - 24.5% - peaks 20:00".
        bullets: Short defining characteristics, HTML allowed for emphasis.
    """
    lis = "".join(f"<li>{b}</li>" for b in bullets)
    st.markdown(
        f'<div class="arch-card" style="--swatch:{color}">'
        f'<div class="arch-name"><span class="dot"></span>{name}</div>'
        f'<div class="arch-meta">{meta}</div>'
        f"<ul>{lis}</ul></div>",
        unsafe_allow_html=True,
    )


def step_card(number: int, title: str, body: str) -> None:
    """One numbered step in a short sequence.

    The number is real information here - the steps are meant to be done in
    order - so it is set in the mono face and left unselectable, the same
    treatment the chapter numbers get.
    """
    st.markdown(
        f'<div class="step-card">'
        f'<div class="step-n">STEP {number:02d}</div>'
        f'<div class="step-t">{title}</div>'
        f'<div class="step-b">{body}</div></div>',
        unsafe_allow_html=True,
    )


def insight_block(head: str, color: str, observation: str, evidence: str,
                  interpretation: str = "", action: str = "") -> None:
    """A four-part evidence block: observation, evidence, interpretation, action.

    Keeps the honest structure of the recommendation engine (a measured
    deviation, not a causal claim) visible in the layout itself. Any of the four
    parts may be empty; an empty part is omitted rather than shown blank, because
    the recommendation engine emits observation, evidence and action but no
    separate interpretation, and inventing one to fill the slot would be a
    fabrication.
    """
    rows = [("obs", "Observation", observation, "v"),
            ("ev", "Evidence", evidence, "v mono"),
            ("interp", "Interpretation", interpretation, "v"),
            ("act", "Possible action", action, "v")]
    body = "".join(
        f'<div class="row"><div class="k {cls}">{label}</div><div class="{vcls}">{text}</div></div>'
        for cls, label, text, vcls in rows if text
    )
    st.markdown(
        f'<div class="insight" style="--swatch:{color}">'
        f'<div class="insight-head"><span class="dot"></span>{head}</div>'
        f"{body}</div>",
        unsafe_allow_html=True,
    )


def research_card_html(title: str, authors: str, year: str, venue: str, method: str,
                       dataset: str, why: str, url: str, url_label: str = "DOI") -> str:
    """Markup for one research reference card. Every field is the caller's; this
    only lays them out. Do not pass invented bibliographic data to it."""
    return (
        f'<div class="ref-card">'
        f'<div class="ref-title">{title}</div>'
        f'<div class="ref-authors">{authors} - {year} - {venue}</div>'
        f'<div class="ref-grid">'
        f'<div class="rk">Method</div><div class="rv">{method}</div>'
        f'<div class="rk">Dataset</div><div class="rv">{dataset}</div>'
        f"</div>"
        f'<div class="ref-why">{why}</div>'
        f'<div style="margin-top:0.6rem"><a href="{url}" target="_blank" rel="noopener">{url_label}</a></div>'
        "</div>"
    )


def research_card(title: str, authors: str, year: str, venue: str, method: str,
                  dataset: str, why: str, url: str, url_label: str = "DOI") -> None:
    """Render a single research reference card on its own."""
    st.markdown(research_card_html(title, authors, year, venue, method, dataset, why,
                                   url, url_label), unsafe_allow_html=True)


def research_grid(cards: Sequence[dict]) -> None:
    """Render a run of research cards inside the responsive grid.

    Args:
        cards: dicts whose keys match research_card_html's parameters. Only pass
            bibliographic data you have verified against a source, never invented.
    """
    html = "".join(research_card_html(**card) for card in cards)
    st.markdown(f'<div class="research">{html}</div>', unsafe_allow_html=True)


def pipeline(steps: Iterable[tuple[str, str]]) -> None:
    """The pipeline as numbered stages, because the order carries meaning.

    Args:
        steps: (title, description) pairs in pipeline order.
    """
    html = ['<div class="pipe">']
    for i, (title, desc) in enumerate(steps, 1):
        html.append(
            f'<div class="step"><div class="n">{i:02d}</div>'
            f'<div class="t">{title}</div><div class="d">{desc}</div></div>'
        )
    html.append("</div>")
    st.markdown("".join(html), unsafe_allow_html=True)


# --- Masthead, chapters and footer -------------------------------------------
# These carry the presentation the static landing page had. They are structure
# only: the words and the numbers arrive from the caller, which reads them from
# the live analysis, so nothing here can drift out of step with a run.

def masthead(section_label: str, links: Sequence[tuple[str, str]] = (),
             brand: str = "Load-Shape Study") -> None:
    """The identity band at the top of every page.

    Args:
        section_label: Where the reader currently is, shown as a breadcrumb.
        links: (label, url) pairs for outbound links only. Page navigation
            belongs in the sidebar; putting it here too would make two menus.
        brand: The project's short name.
    """
    outs = "".join(
        f'<a class="out" href="{url}" target="_blank" rel="noopener">{label}</a>'
        for label, url in links
    )
    st.markdown(
        f'<div class="masthead">'
        f'<span class="brand"><span class="slash">/</span>{brand}</span>'
        f'<span class="where"><b>{section_label}</b></span>'
        f'<span class="spacer"></span>{outs}</div>',
        unsafe_allow_html=True,
    )


def chapter(number: int, kicker_text: str, title: str, body_html: str = "") -> None:
    """One numbered movement of the story.

    Args:
        number: 1-based position, rendered zero-padded.
        kicker_text: The short eyebrow, e.g. "The method".
        title: The chapter's claim, as a sentence.
        body_html: Prose; inline HTML is allowed for emphasis only.
    """
    body = f'<div class="ch-indent"><p class="ch-body">{body_html}</p></div>' if body_html else ""
    st.markdown(
        f'<div class="chapter">'
        f'<div class="ch-head"><span class="ch-n">{number:02d}</span>'
        f'<span class="ch-kicker">{kicker_text}</span></div>'
        f'<div class="ch-indent"><h2>{title}</h2></div>{body}</div>',
        unsafe_allow_html=True,
    )


def nav_group(label: str) -> None:
    """A heading over one run of sidebar navigation items."""
    st.sidebar.markdown(f'<div class="nav-group">{label}</div>', unsafe_allow_html=True)


def footer(run_line: str, tagline: str, links: Sequence[tuple[str, str]] = ()) -> None:
    """The closing band.

    Args:
        run_line: A mono line identifying the run, e.g. its config hash.
        tagline: One sentence on what the study claims.
        links: (label, url) outbound pairs.
    """
    outs = "".join(
        f'<a class="out" href="{url}" target="_blank" rel="noopener">{label}</a>'
        for label, url in links
    )
    st.markdown(
        f'<div class="foot"><span class="f-run">{run_line}</span>'
        f'<span class="f-line">{tagline}</span>'
        f'<span class="spacer"></span>{outs}</div>',
        unsafe_allow_html=True,
    )
