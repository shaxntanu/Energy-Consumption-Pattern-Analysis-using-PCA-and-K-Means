"""Design system for the Streamlit dashboard.

One place for the visual language: colour tokens, the injected CSS (typography,
layout chrome, components) and a Plotly template so every chart speaks the same
palette. The organising idea is time of day. Every chart in this project has the
hour of the day on its x-axis, and the clusters differ by *when* people use
energy, so colour runs on a temperature axis, cool indigo for the small hours
through to warm amber at the evening peak, and a faint four-band shading behind
the hour axis marks night, morning, afternoon and evening. That motif, not a
logo, is what the interface is built around.

Nothing here computes or changes a result. It only decides how the numbers that
the pipeline already produced are shown.
"""
from __future__ import annotations

from typing import Iterable, Sequence

import plotly.graph_objects as go
import plotly.io as pio
import streamlit as st

# --- Colour tokens -----------------------------------------------------------
# Named hex values. The two accents are the poles of the time-of-day axis:
# INDIGO reads as night and off-peak, AMBER as the evening energy peak.
MIDNIGHT = "#0B0E14"    # app background, the darkest surface
PANEL = "#141A24"       # raised surface: cards, sidebar
PANEL_HI = "#1B2230"    # hover / nested surface
LINE = "#262E3D"        # hairline rules and borders
INK = "#EAECEF"         # primary text
MIST = "#8A93A6"        # secondary text, captions, axis ticks
AMBER = "#F5A524"       # primary accent, the peak
AMBER_DEEP = "#E0871B"
INDIGO = "#6C8CFF"      # secondary accent, the night
TEAL = "#3FB8AF"
ROSE = "#E0596B"
VIOLET = "#B085F5"
GREEN = "#8CC152"

# Qualitative palette for cluster IDs. Cluster numbers are arbitrary, so this is
# a distinct-hue set rather than an ordered ramp; amber and indigo lead because
# they are the palette's own poles.
CLUSTER_COLORS: tuple[str, ...] = (AMBER, INDIGO, TEAL, ROSE, VIOLET, GREEN)

# Four day-parts, each a start hour, end hour, label and faint fill. These are
# the shading behind every hour axis and the definition of the *_share features.
PERIODS: tuple[tuple[int, int, str, str], ...] = (
    (0, 6, "Night", "rgba(108,140,255,0.05)"),
    (6, 12, "Morning", "rgba(63,184,175,0.05)"),
    (12, 18, "Afternoon", "rgba(245,211,107,0.06)"),
    (18, 24, "Evening", "rgba(245,165,36,0.08)"),
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
            title=dict(font=dict(family="Space Grotesk, sans-serif", size=18, color=INK)),
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
            colorscale=dict(sequential=[[0, INDIGO], [0.5, "#7d7fb0"], [1, AMBER]]),
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
  --line: {LINE}; --ink: {INK}; --mist: {MIST};
  --amber: {AMBER}; --amber-deep: {AMBER_DEEP}; --indigo: {INDIGO};
  --display: 'Space Grotesk', system-ui, sans-serif;
  --body: 'Inter', system-ui, sans-serif;
  --mono: 'IBM Plex Mono', ui-monospace, monospace;
}}
"""


def _css() -> str:
    """The full stylesheet. Split into font/variable and rule halves only so the
    f-string braces stay readable."""
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
a { color: var(--amber); text-decoration: none; }
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
  text-transform: uppercase; letter-spacing: 0.22em; color: var(--amber);
  display: inline-block; margin-bottom: 0.6rem;
}

/* Hero ------------------------------------------------------------------ */
.hero { padding: 0.4rem 0 1.6rem 0; border-bottom: 1px solid var(--line); margin-bottom: 1.8rem; }
.hero h1 {
  font-size: clamp(2.4rem, 5.5vw, 4rem); font-weight: 700; line-height: 1.03;
  margin: 0 0 0.9rem 0;
}
.hero .lede { font-size: clamp(1rem, 1.6vw, 1.2rem); color: var(--mist); max-width: 60ch; margin: 0; }
.hero .accent { color: var(--amber); }

/* Section headers ------------------------------------------------------- */
.section { margin: 2.4rem 0 1.1rem 0; }
.section h2 { font-size: clamp(1.4rem, 2.6vw, 1.9rem); font-weight: 600; margin: 0.2rem 0 0.4rem 0; }
.section .lede { color: var(--mist); max-width: 68ch; margin: 0; }

/* Metric cards ---------------------------------------------------------- */
.metric-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(150px, 1fr)); gap: 0.85rem; margin: 0.4rem 0 0.6rem 0; }
.metric-card {
  background: var(--panel); border: 1px solid var(--line); border-radius: 14px;
  padding: 1rem 1.1rem; transition: transform 0.18s ease, border-color 0.18s ease;
}
.metric-card:hover { transform: translateY(-2px); border-color: var(--amber-deep); }
.metric-card .label {
  font-family: var(--mono); font-size: 0.68rem; text-transform: uppercase;
  letter-spacing: 0.14em; color: var(--mist); margin-bottom: 0.5rem;
}
.metric-card .value {
  font-family: var(--display); font-size: 1.9rem; font-weight: 600; color: var(--ink);
  line-height: 1; font-feature-settings: 'tnum' 1; font-variant-numeric: tabular-nums;
}
.metric-card .sub { font-family: var(--mono); font-size: 0.72rem; color: var(--mist); margin-top: 0.45rem; }
.metric-card.accent { border-left: 3px solid var(--amber); }

/* Synthetic-data badge -------------------------------------------------- */
.badge-synthetic {
  display: inline-flex; align-items: center; gap: 0.5rem;
  background: rgba(245,165,36,0.10); border: 1px solid rgba(245,165,36,0.35);
  color: var(--amber); font-family: var(--mono); font-size: 0.72rem;
  text-transform: uppercase; letter-spacing: 0.12em; font-weight: 600;
  padding: 0.4rem 0.8rem; border-radius: 999px;
}
.badge-synthetic::before { content: ""; width: 7px; height: 7px; border-radius: 50%; background: var(--amber); }

/* Panels and rules ------------------------------------------------------ */
.panel { background: var(--panel); border: 1px solid var(--line); border-radius: 14px; padding: 1.2rem 1.3rem; }
.hairline { border: none; border-top: 1px solid var(--line); margin: 1.8rem 0; }
.note {
  border-left: 3px solid var(--indigo); background: var(--panel);
  padding: 0.85rem 1.1rem; border-radius: 0 10px 10px 0; color: var(--mist);
}
.note strong { color: var(--ink); }

/* Pipeline stepper (a genuine sequence, so numbered) -------------------- */
.pipe { display: grid; grid-template-columns: repeat(auto-fit, minmax(150px, 1fr)); gap: 0.7rem; }
.pipe .step { background: var(--panel); border: 1px solid var(--line); border-radius: 12px; padding: 0.9rem 1rem; }
.pipe .step .n { font-family: var(--mono); font-size: 0.72rem; color: var(--amber); letter-spacing: 0.1em; }
.pipe .step .t { font-family: var(--display); font-weight: 600; margin-top: 0.3rem; color: var(--ink); }
.pipe .step .d { font-size: 0.82rem; color: var(--mist); margin-top: 0.25rem; line-height: 1.45; }

/* Streamlit widgets ----------------------------------------------------- */
[data-testid="stDataFrame"] { border: 1px solid var(--line); border-radius: 12px; }
.stRadio > label, .stSelectbox label, .stSlider label { color: var(--mist) !important; font-family: var(--mono); font-size: 0.8rem; }

/* Accessibility --------------------------------------------------------- */
*:focus-visible { outline: 2px solid var(--amber); outline-offset: 2px; }
@media (prefers-reduced-motion: reduce) { .metric-card { transition: none; } }
@media (max-width: 640px) { .block-container { padding-left: 1rem; padding-right: 1rem; } }
"""


def inject_theme() -> None:
    """Inject the design system. Call once, first thing on every page."""
    st.markdown(f"<style>{_css()}</style>", unsafe_allow_html=True)
    register_plotly_template()


# --- HTML component helpers --------------------------------------------------
# Each returns nothing and writes directly, so pages read as a sequence of
# calls. All user-facing strings are the caller's; these only wrap structure.

def hero(title_html: str, lede: str) -> None:
    """Page hero: an eyebrow is not included so callers control the kicker."""
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


def note(html: str) -> None:
    """An indigo-ruled aside for caveats and context."""
    st.markdown(f'<div class="note">{html}</div>', unsafe_allow_html=True)


def hairline() -> None:
    """A thin horizontal rule."""
    st.markdown('<hr class="hairline" />', unsafe_allow_html=True)


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
