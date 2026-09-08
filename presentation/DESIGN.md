# Design system - Energy Consumption Pattern Analysis deck

A 20-slide, 1920×1080 conference deck for `presentation/`. It reads like a thesis
defense or a conference talk about this project, not like a page a website
generator produced. This file is the contract; every rule below is enforced in
`src/styles/main.css` and in the slide markup of `index.html`.

The deck is the third surface of one design language. The other two already
exist in this repo:

- `src/dashboard_ui.py` - the Streamlit dashboard (MIDNIGHT canvas, CYAN/GREEN/
  AMBER/INDIGO accents, four-band day-part shading, distinct-hue cluster palette).
- `web/` - the Vercel app (`web/public/data/*.json` contract files, `dark_mode_plots`).

The deck keeps its own cinematic black-canvas, large-serif-display instinct
(it already reads like a keynote), but borrows the dashboard's accent hues, its
day-part band motif, and its honesty conventions. A viewer who has seen the
dashboard should recognize the deck as the same project; a viewer who has not
should be able to look the dashboard up afterwards and find the same colors.

---

## 1. Tokens

### 1.1 Color

Named tokens, adapted from `src/dashboard_ui.py` (values quoted from lines 45–65
of that file) and the existing deck canvas.

| Token | Hex | Role | Source |
| --- | --- | --- | --- |
| `--canvas` | `#000000` | slide background | existing deck (`main.css` `--black`) |
| `--panel` | `#141A24` | raised surface (cards, diagram nodes) | `PANEL` in `dashboard_ui.py` |
| `--panel-hi` | `#1B2230` | hover / nested surface | `PANEL_HI` in `dashboard_ui.py` |
| `--line` | `#262E3D` | hairlines, table rules, connector strokes | `LINE` in `dashboard_ui.py` |
| `--ink` | `#EAECEF` | primary text | `INK` in `dashboard_ui.py` |
| `--mist` | `#8A93A6` | secondary text, body | `MIST` in `dashboard_ui.py` |
| `--slate` | `#5B657A` | tertiary text, source captions | `SLATE` in `dashboard_ui.py` |
| `--cyan` | `#3BC9DE` | primary accent, data / transform family | `CYAN` in `dashboard_ui.py` |
| `--green` | `#4FD1A5` | validation, evaluation, agreement | `GREEN` in `dashboard_ui.py` |
| `--amber` | `#F5A524` | model / selection emphasis, caution | `AMBER` in `dashboard_ui.py` |
| `--indigo` | `#6C8CFF` | night end of day-part ramp, focus | `INDIGO` in `dashboard_ui.py` |
| `--rose` | `#F26D6D` | negative deviation, error | `ROSE` in `dashboard_ui.py` |
| `--violet` | `#B085F5` | qualitative extra hue | `VIOLET` in `dashboard_ui.py` |

Cluster colors follow `CLUSTER_COLORS = (AMBER, CYAN, VIOLET, GREEN, ROSE, INDIGO)`
from `dashboard_ui.py` line 75. The flagship run selects K = 4, so the deck uses
the first four, in order, for clusters 0–3:

| Cluster index | Hue | Hex |
| --- | --- | --- |
| 0 | AMBER | `#F5A524` |
| 1 | CYAN | `#3BC9DE` |
| 2 | VIOLET | `#B085F5` |
| 3 | GREEN | `#4FD1A5` |

Every occurrence of a cluster hue carries its name as a label - never color
alone. (Rule: *never color alone*.)

### 1.2 Day-part bands (reused motif)

The dashboard shades a 24-hour day into four bands (`PERIODS` in
`dashboard_ui.py` lines 89–98):

| Hours | Band | Tint |
| --- | --- | --- |
| 0–6 | Night | indigo, `rgba(108,140,255,0.06)` |
| 6–12 | Morning | cyan, `rgba(59,201,222,0.06)` |
| 12–18 | Afternoon | green, `rgba(79,209,165,0.06)` |
| 18–24 | Evening | amber, `rgba(245,165,36,0.06)` |

The deck applies these bands **only** to hour-of-day charts (the cluster hourly
patterns slide and the seasonal mean-shape slide), as vertical shading behind
the plotted curve, exactly as the dashboard does. Anywhere else they are
decoration and are removed.

### 1.3 Surface fills

Surface fills are flat. No gradients, no box-shadows, no inner glows.

- Panel surface: `var(--panel)` fill, `1px solid var(--line)` border,
  radius `6px` (matching the diagram-node radius in §4).
- Emphasis card: `color-mix(in srgb, var(--accent) 11%, var(--panel-hi))` fill
  with a `3px` top border in the accent - the same recipe as the dashboard's
  `arch-card`. Used for cluster cards and other genuinely-emphasized elements
  only; not for every card.
- Containers that are purely structural (a table wrapper, a figure frame) use a
  hairline border on `var(--canvas)`, no fill.

---

## 2. Typography

### 2.1 Families

Three faces, two of which are the "two clearly distinct" design families; the
third is a functional mono for data and citations.

| Family | Used for | Existing precedent |
| --- | --- | --- |
| `Charter`, Georgia, Times New Roman, serif | Display: cover title, section title, slide headline, stat numerals | deck `main.css` `--font-serif` |
| Inter, system sans | Body, labels, tables' headers, UI controls | dashboard body face |
| IBM Plex Mono, SF Mono, Consolas | Data, captions, citations, table numerals | dashboard mono face |

### 2.2 Scale

Tiers, with size / weight / line-height / letter-spacing. Body floor is 18px.

| Tier | Size | Weight | Line-height | Letter-spacing | Notes |
| --- | --- | --- | --- | --- | --- |
| Cover title | 96px | 400 | 1.05 | −0.02em | one thesis sentence, ≤ 12 words |
| Section title | 150px | 400 | 0.95 | −0.03em | one word or a short phrase |
| Slide headline | 54px | 400 | 1.12 | −0.01em | a complete sentence; the conclusion of the slide |
| Kicker | 15px | 500 | 1.4 | +0.01em | sentence case; never ALL-CAPS, never tracked |
| Body | 20px | 400 | 1.6 | normal | floor 18px in tables/captions |
| Caption / citation | 14px | 400 | 1.5 | normal | IBM Plex Mono, `--slate` |
| Table numeral | 17px | 400 | 1.3 | normal | IBM Plex Mono, `font-variant-numeric: tabular-nums` |
| Stat numeral | 64px | 400 | 1.0 | −0.01em | serif, always with a label |

### 2.3 Rules

- **Sentence case everywhere.** No ALL-CAPS labels, no tracked-out eyebrows.
  The one exception is the literal company mark `SUNEE` in the fixed logo
  (top-right), which is a brand wordmark and is kept.
- **No italics.**
- **No single-word accent** inside a headline (no one word italic, bold, or a
  different color to "pop").
- **No middle-dot meta strings** (`A · B · C`), **no `WORD - fragment` labels**.
  When a slide needs a provenance line it is a plain mono sentence: `Source:
  web/public/data/clustering.json · config 99c7a6631340d301`.
- **Line length < 80 chars** for body copy (serif display may exceed).
- Numerals in any data table or stat are tabular.

---

## 3. Layout

- Slides are fixed 1920×1080 (`--slide-width` / `--slide-height`), content
  column max 1560px, side padding 80px. Left-aligned throughout - this is a
  conference deck, not a landing page.
- One idea per slide. The headline is a complete sentence that states the
  slide's conclusion, not a topic label.
- **≤ 6 elements per slide** counting distinct content blocks (a chart counts
  as one, a 4-row table as one, a diagram as one). Whitespace is the layout tool.
- **Never a text-only slide.** Every slide carries at least one non-text element:
  a chart, a table, a diagram, or a data-driven figure.
- Numbering is used **only for real sequences**: the five deck sections
  (01 Cover through 05 Closing) and the pipeline step order. Cluster cards and
  feature lists are not sequences and are not numbered.
- Alignment: headlines and body left-aligned on the same 80px grid; charts and
  tables align to it; the cover title sits low-left with the dataset facts as a
  mono provenance line beneath.

---

## 4. Diagrams (draw.io style, inline SVG)

Exactly three diagrams ship in the deck, each redrawn as inline SVG - never
screenshots, never Mermaid renders. Spec:

- Nodes 160×64 on an 8px grid; rounded rect, corner radius 6px; stroke 1.5px;
  fill `color-mix(in srgb, var(--swatch) 11%, var(--panel-hi))`.
- One accent per stage family: cyan = data/generate, indigo = transform,
  amber = model, green = evaluation, violet = output (matches dashboard usage
  where those hues already mean those things).
- Diamond shape only for a genuine branch (a decision), never for a plain step.
- Connectors orthogonal (right-angle elbows), 1.5px, `--line`, solid; arrowhead
  is a small filled triangle in `--mist`. Dashed only for "optional / reference
  input" edges.
- Labels ≤ 2 lines, 15px Inter, `--ink` for the title line, `--mist` for the
  sub-line.
- Flat, no shadow, no gradient, no glow.

The three diagrams:

1. **Full pipeline** (slide 5): Generate (200 consumers, 4 archetypes) →
   Validate provenance (Zephyr weather) → Preprocess with the leakage boundary →
   Engineer 51 features (24 hourly + 27 summary) → Standardize + PCA (10
   components) → Sweep K 2–10, select by rule → Explain (SHAP surrogate) →
   Evaluate → branch: synthetic → ARI/NMI vs archetypes; real → internal
   silhouette/CH/DB + stability → Export.
2. **K-selection rule** (slide 10): K 2–10 → filter (min share 5%, min stability
   ARI 0.6) → normalize silhouette / CH / DB → composite score (mean of the
   three normalized) → within 5% tolerance of the best score → smallest K wins.
3. **Leakage boundary** (slide 6): Raw panel → drop `archetype`,
   `seasonal_phase`, other truth columns before feature engineering → features
   hold only what a meter+calendar could observe → labels used in evaluation
   only, never during clustering.

---

## 5. Charts and tables

- Charts are real matplotlib PNGs, either reused from `dark_mode_plots/figures/`
  (already dark-canvas) or `outputs/figures/`, or freshly rendered in this
  palette for this deck. No screenshots of notebook cells, no web-plot grabs.
- On-screen chart images are placed with `max-width` / `max-height` and left
  alignment; the mono source caption sits beneath.
- Tables use IBM Plex Mono with `tabular-nums`, hairline `--line` rules, header
  row in `--ink`, body in `--mist`, highlighted cell in the relevant accent
  (with a label, never color alone).
- Hour-of-day charts get the day-part bands from §1.2.
- Any figure whose `docs/verification.md` status is not VALIDATED is marked
  `pending` on the slide in a mono caption - never a plausible-looking number.

---

## 6. Copy principles

- Headlines are the slide's conclusion, written for a listener who walked in
  mid-talk. "Two homes can share a bill and share nothing else" beats
  "Motivation".
- Every quantitative claim on every slide traces to a named file in this repo:
  `RESULTS.md`, `docs/verification.md`, `outputs/reports/analysis_summary.md`,
  or a `web/public/data/*.json` contract. The source line on the slide names
  the file and, where relevant, the config hash (flagship `99c7a6631340d301`,
  30-day `6896387297178841`).
- If a number cannot be traced, it does not appear on a slide. If a step is
  unexecuted or unverifiable, the slide says so in the pipeline's own voice
  (e.g. seasonal: `available: false`, reason: one season present), matching
  `docs/verification.md` and `RESULTS.md`.
- No emoji anywhere, in the HTML or in the exported PPTX. The project enforces
  this on its dashboard (`tests/test_app_smoke.py`); the deck holds the same
  rule.
- Present tense, active voice, no sales language. This is a results talk.

---

## 7. Do / don't

| Do | Don't |
| --- | --- |
| Keep the black canvas and large serif display | Don't switch to cream + terracotta, near-black + acid-green, or broadsheet hairlines |
| Use the dashboard's CYAN/GREEN/AMBER/INDIGO accents | Don't default back to one blue `#0066ff` + one green `#10b981` |
| Sentence-case kickers | Don't use tracked ALL-CAPS eyebrows above every heading |
| Flat surfaces, 1px `--line` borders, one 6px radius | Don't use identical rounded cards everywhere with soft grey shadows and gradient washes |
| Differentiate structure from emphasis (hue-coded cards only where real) | Don't give every card the same fill/radius regardless of hierarchy |
| Number only real sequences (sections, pipeline) | Don't stamp `01 / 02 / 03` on non-sequences |
| Cite the source file and config hash on every quantitative slide | Don't float numbers with no provenance |
| Mark unverifiable steps `pending` | Don't invent or round for effect |
| Day-part bands on hour-of-day charts only | Don't use the bands as generic decoration |
| Color + label always | Don't encode meaning in color alone |
| ≤ 6 elements, ≥ 1 non-text element, one conclusion per slide | Don't build text walls or stat-card grids |

---

## 8. The 20 slides (outline)

Sections: 01 Cover · 02 Data · 03 Method · 04 Results · 05 Closing. Each slide
lists its headline, its non-text element(s), and its source contract.

1. **01 · Grouped by when a home uses power, not how much.** Cover. 1,752,000
   hourly records, 200 consumers × 365 days, 51 features, K = 4.
   Source: `RESULTS.md`, `outputs/reports/analysis_summary.md`.
2. **02 · Two homes can share a bill and share nothing else.** Two 24-hour
   curves with the same daily total, different shapes (fresh small matplotlib
   figure or `hourly_patterns.png`). Source: `web/public/data/profiles.json`.
3. **02 · Timing tells a utility what magnitude alone cannot.** The three
   timing features (`evening_share`, `peak_to_avg_ratio`, `weekend_ratio`) as a
   compact table with population vs cluster values. Source:
   `web/public/data/profiles.json`.
4. **02 · 200 consumers, four hidden rhythms, one real weather feed.** Dataset
   facts table: 200 × 365, 4 archetypes, Zephyr Station weather provenance,
   real-world adapter (24 meters, CASE A). Source: `RESULTS.md` §4–§5,
   `docs/verification.md`.
5. **03 · One deterministic path from meter to validated cluster.** Pipeline
   diagram (SVG #1). Source: `docs/flow_diagram.md`,
   `outputs/reports/analysis_summary.md`.
6. **03 · The answer key never reaches the model.** Leakage boundary diagram
   (SVG #3). Source: `docs/verification.md`, pipeline source.
7. **03 · 51 features, not one of them is size.** Feature groups table: 24
   hourly shape bins + 27 summary (day-period shares, peak sin/cos, weekend
   ratio, base-load share, harmonics, Haar details, entropy/Gini, CV, skew,
   kurtosis). Source: `RESULTS.md` §4.
8. **03 · 51 correlated numbers collapse into 10 that matter.** PCA method
   statement + component-loadings chart. Source: `web/public/data/pca.json`.
9. **03 · Ten components hold 95.05% of the variance.** `explained_variance.png`
   + loadings table (PC1–PC5 reads). Source: `web/public/data/pca.json`.
10. **03 · K is picked by a rule fixed in advance, not by eye.** K-selection
    diagram (SVG #2). Source: `web/public/data/clustering.json`
    (selection trace: min share 0.05, min ARI 0.6, tolerance 0.05).
11. **03 · Silhouette peaks at K = 5; the rule says K = 4.** K-sweep table
    (K 2–10: silhouette, CH, DB, composite, selected) with the tolerance band
    noted. Source: `web/public/data/clustering.json`, `RESULTS.md` §4.
12. **04 · Four rhythms of a day.** Cluster cards (hue-coded, named, sizes
    39/52/47/62) + `hourly_patterns.png` with day-part bands. Source:
    `web/public/data/profiles.json`, `RESULTS.md` §4.
13. **04 · Recovery peaks exactly where the rule landed.** ARI/NMI by K +
    crosstab; ARI 0.8127 / NMI 0.8284 at K = 4, best recovery K = 4. Source:
    `web/public/data/validation.json`.
14. **04 · SHAP says which hours separate the groups.** `shap_cluster_importance.png`
    + top global features; surrogate CV 0.985. Source:
    `web/public/data/explainability.json`.
15. **04 · A ±25% seasonal swing, the same four groups underneath.** Seasonal
    charts (amplitude 0.202 vs injected 0.25, phase r 0.678, agreement 0.885)
    with day-part bands. Source: `web/public/data/seasonal.json`, `RESULTS.md`.
16. **04 · Mean agreement 0.88 across four quarters.** `longitudinal_cluster_stability.png`
    + per-quarter ARI table (0.838 / 0.892 / 0.946 / 0.851). Source:
    `web/public/data/longitudinal.json`.
17. **04 · The top two feature sets are statistically indistinguishable.**
    Ablation + seed-robustness honest read: behavioral 0.641 ± 0.115 vs shape
    0.646 single draw. Source: `web/public/data/benchmark.json`,
    `outputs/reports/analysis_summary.md`.
18. **05 · Same method, two apps, one optional native kernel.** Delivery table:
    Streamlit dashboard, Vercel web app, optional C++ engine (K-Means 6.45×,
    PCA 0.29× on the wide set - reported honestly). Source:
    `web/public/data/benchmark.json`, README.
19. **05 · A 30-day window already broke this rule once.** Limitations, told
    with Run 1: seasonal `available: false`, no longitudinal, ARI 0.585 vs
    0.813. Source: `RESULTS.md` §3, `docs/verification.md`.
20. **05 · The shape of a day is real, recoverable, and modestly separated.**
    Takeaway. Source: `RESULTS.md` §6 (honesty notes), links to dashboard + web.

---

## 9. Compliance hooks (checked before done)

- `script.js` `totalSlides` stays `20`; slide elements are
  `<section class="slide">` and navigation matches.
- No emoji in `index.html`, `main.css`, or anything the PPTX export embeds
  (grep for the emoji ranges).
- Export (`src/script.js`) keeps reading `.slide-label`, `.slide-title`,
  `.chart-img`, `.content-card p`, `.info-box p`, and `img[src*="dark_mode_plots"]`;
  any markup restructure keeps these hooks or updates the export in the same
  change.
- Sound-off: every slide's text is complete without audio (no "as you can see",
  no reliance on the presenter's voice).
- Every quantitative slide carries a mono source line naming a file in this
  repo.
