# Energy Consumption Pattern Analysis — Academic Presentation

Complete 20-slide academic presentation deck for the Energy Consumption Pattern Analysis project. Built with SpaceX-inspired black canvas design system and actual matplotlib dark mode plots.

## 📊 Overview

- **20 Technical Slides** covering complete methodology from problem to results
- **SpaceX-Inspired Design** with black canvas (#000), uppercase typography, minimal accent
- **Actual Dark Mode Plots** from `../dark_mode_plots/figures/`
- **Academic Focus** — not a business pitch, proper research presentation
- **Keyboard Navigation** with fullscreen and presentation modes

## 🎯 Slide Structure

### Complete 20-Slide Breakdown

1. **Title** — Cover with key metrics (ARI 0.81, K=4, 95% variance)
2. **Problem Statement** — Shape-first vs traditional scale-based segmentation
3. **Methodology Pipeline** — 5-step end-to-end workflow
4. **Dataset** — Synthetic archetypes + real-world adapter pathway
5. **Preprocessing** — 5-step data pipeline with Z-score normalization
6. **Feature Engineering** — 51 features (24 shape + 27 summary)
7. **PCA Results** — 10 components capture 95.05% variance
8. **PCA Loadings** — Component interpretation heatmap
9. **K Selection** — Elbow + silhouette evidence for K=4
10. **Cluster Distribution** — 4 behavioral archetypes with sizes
11. **Cluster Profiles** — Detailed characterization of each archetype
12. **Validation** — ARI 0.81 archetype recovery confirmation
13. **Silhouette Analysis** — Cluster quality visualization
14. **Explainability (SHAP)** — Feature importance by cluster
15. **Longitudinal Stability** — Quarterly ARI > 0.89
16. **Seasonal Patterns** — Amplitude vs phase analysis
17. **Feature Ablation** — Shape vs summary contributions
18. **Web Platform** — Vercel explorer + Streamlit simulator
19. **Limitations** — Honest constraints and future work
20. **Conclusion** — 5 key takeaways with demo links

## ⌨️ Keyboard Shortcuts

| Key | Action |
|-----|--------|
| `→` `Space` `PageDown` | Next slide |
| `←` `PageUp` | Previous slide |
| `Home` | First slide |
| `End` | Last slide |
| `F` | Toggle fullscreen |
| `P` | Toggle presentation mode |
| `Esc` | Exit fullscreen/presentation |

## 🎨 Design System

### SpaceX-Inspired Aesthetic

- **Pure Black Canvas** — `#000000` background (not dark gray)
- **Uppercase Typography** — All headlines in uppercase for engineering aesthetic
- **Minimal Accent** — Cyan (`#00d992`) for highlights, blue/amber sparingly
- **Inter Font Family** — No D-DIN (licensing), using Inter at 700-800 weights
- **Tight Spacing** — Condensed line-height (1.1) for display sizes
- **Card-Based Layout** — Gray-bordered cards on black for content grouping

### Color Palette

```css
--black: #000000        /* Primary canvas */
--white: #ffffff        /* Primary text */
--accent-cyan: #00d992  /* Primary accent */
--accent-blue: #0066ff  /* Secondary accent */
--accent-amber: #f2b04b /* Warnings/limitations */
--gray-100 to --gray-600 /* Neutral scale */
```

### Typography Scale

- **Headline:** 64px (cover: 72px), 800 weight, uppercase
- **Subheadline:** 20px, 400 weight
- **Body:** 16px, 400 weight
- **Kicker:** 12px, 700 weight, uppercase, cyan
- **Mono:** SF Mono / Consolas for metrics

## 🚀 Usage

### Local Viewing

Open `index.html` in a modern browser:

```bash
# Windows
start sunee-pitch-deck/index.html

# macOS
open sunee-pitch-deck/index.html

# Linux
xdg-open sunee-pitch-deck/index.html
```

### Live Presentation

1. Press `F` for fullscreen
2. Press `P` for presentation mode (auto-fullscreen + hide controls on idle)
3. Navigate with arrow keys or space
4. Press `Esc` to exit

### Export Options

**Print to PDF:**
1. Press `Ctrl+P` (Windows/Linux) or `Cmd+P` (macOS)
2. Select "Save as PDF"
3. Set scale to 100%
4. Recommended: Landscape orientation

**PowerPoint Export:**
- Currently displays alert (WIP)
- Alternative: Use PDF export and import into PowerPoint

## 📦 Assets & Dependencies

### External Dependencies

- **PptxGenJS** — Loaded from CDN (future PowerPoint export)
- **Inter Font** — Google Fonts import in CSS

### Local Assets

All matplotlib dark mode plots referenced from parent directory:

```
../dark_mode_plots/figures/
├── explained_variance.png
├── component_loadings.png
├── elbow_curve.png
├── k_selection_metrics.png
├── hourly_patterns.png
├── silhouette_scores.png
├── archetype_recovery.png
├── shap_cluster_importance.png
├── longitudinal_cluster_stability.png
├── seasonal_daily_energy_and_peak_hour.png
├── seasonal_mean_shape_by_season.png
└── ablation_comparison.png
```

**Important:** Presentation expects plots to exist at `../dark_mode_plots/figures/`. If running from different directory, update image paths in `index.html`.

## 🏗️ File Structure

```
sunee-pitch-deck/
├── index.html              # 20-slide HTML deck
├── styles.css              # SpaceX-inspired design system
├── script.js               # Navigation controller
├── README.md               # This file
├── DESIGN.md               # SpaceX design system reference
├── 1-s2.md                 # Research paper on presentation skills
├── pcbi.1009554.md         # 10 rules for effective slides
└── sunee-mascot.png        # Logo (not used in academic version)
```

## 🔧 Customization

### Update Content

All slide content is directly in `index.html`. Edit text, metrics, or descriptions inline.

### Change Colors

Edit CSS variables in `styles.css`:

```css
:root {
  --accent-cyan: #YOUR_COLOR;
  --accent-blue: #YOUR_COLOR;
}
```

### Add/Remove Slides

1. Duplicate a `<div class="slide">` block in HTML
2. Update `data-slide` attribute
3. Update `totalSlides: 20` in `script.js`
4. Update navigation counter

### Swap Matplotlib Plots

Replace image `src` paths in HTML:

```html
<img src="../dark_mode_plots/figures/YOUR_PLOT.png" alt="Description">
```

## 🌐 Browser Compatibility

| Browser | Version | Support |
|---------|---------|---------|
| Chrome | 90+ | ✅ Full |
| Firefox | 88+ | ✅ Full |
| Safari | 14+ | ✅ Full |
| Edge | 90+ | ✅ Full |

**Requirements:**
- Modern browser with ES6+ support
- JavaScript enabled
- Viewport: 1920×1080 recommended (scales to window)

## 📱 Responsive Behavior

Presentation adapts to viewport:
- **Desktop (>1200px):** Optimal layout, all grids intact
- **Tablet (768-1200px):** 2-column grids, smaller typography
- **Mobile (<768px):** Single-column layout, touch-friendly

**Recommended:** Present on 1920×1080 display or use fullscreen mode.

## 🐛 Troubleshooting

### Images not loading

Check that dark_mode_plots exists:
```bash
ls ../dark_mode_plots/figures/*.png
```

If running from different directory, update paths in HTML.

### Navigation not working

1. Check browser console for JavaScript errors
2. Ensure `script.js` is loaded (check Network tab)
3. Try refreshing page

### Fullscreen not working

Some browsers require user gesture before fullscreen. Click anywhere on page first, then press `F`.

## 📊 Academic Context

This presentation follows principles from:

1. **"Presentation and publication skills: How to present a paper"** (Grimble et al., 2023)
   - Keep it short and simple (KISS)
   - One key message per slide
   - Readable from back of room

2. **"Ten simple rules for effective presentation slides"** (Naegle, 2021)
   - Include only one idea per slide
   - Design with color-blind audience in mind
   - Build complex diagrams progressively

## 🎓 Design Philosophy

**NOT a business pitch deck.** This is an academic research presentation:

- ✅ Complete methodology disclosure
- ✅ Honest limitations section
- ✅ Validation metrics front-and-center
- ✅ References to actual committed data
- ❌ No aspirational claims
- ❌ No marketing language
- ❌ No invented metrics

**Design choices reflect research rigor:**
- Black canvas = serious technical content
- Uppercase typography = engineering precision
- Minimal decoration = data speaks for itself
- Actual plots = reproducible results

## 🔗 Related Links

- **Live Web Explorer:** https://energy-consumption-pattern.vercel.app
- **Streamlit Simulator:** https://energy-consumption-pattern-vqrh.streamlit.app
- **GitHub Repository:** https://github.com/shaxntanu/Energy-Consumption-Pattern-Analysis-using-PCA-and-K-Means

## 📝 Version History

- **v1.0** — Initial 20-slide academic deck with SpaceX-inspired design
- Replaces generic business pitch with technical research presentation
- Integrates actual matplotlib dark mode plots
- Follows academic presentation best practices

---

**Built for technical audiences. Every slide backed by committed analysis results.**
