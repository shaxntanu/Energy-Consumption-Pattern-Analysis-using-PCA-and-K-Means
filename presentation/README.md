# Energy Consumption Pattern Analysis — Presentation Deck

Complete technical presentation deck for the Energy Consumption Pattern Analysis project. Built with OpenAI-inspired design system featuring dark mode aesthetics, premium typography, and interactive navigation.

## 📊 Overview

- **34 Technical Slides** covering complete methodology, results, and web platform
- **Dark Mode Design** with black background and clean visual hierarchy
- **Premium Typography** using Charter serif for titles, system sans for body
- **Interactive Navigation** with keyboard shortcuts and presentation mode
- **PowerPoint Export** built-in PPTX generation with PptxGenJS

## 🎯 Slide Structure

### Section Breakdown

1. **Cover Slide** — Project title and key metrics
2. **Problem (1.0)** — Shape-first segmentation motivation
3. **Dataset (2.0)** — 200 consumers, 365 days, 1.75M records
4. **Preprocessing (3.0)** — 5-step pipeline from raw data to modeling table
5. **Feature Engineering (4.0)** — 51 behavioral features (24 shape + 27 summary)
6. **PCA (5.0)** — Dimensionality reduction to 10 components (95.05% variance)
7. **K-Means (6.0)** — Evidence-based K=4 selection and cluster distribution
8. **Validation (7.0)** — ARI 0.81 archetype recovery, silhouette analysis
9. **Explainability (8.0)** — SHAP-based post-hoc XAI
10. **Seasonal Analysis (9.0)** — Amplitude, phase, and annual variation
11. **Longitudinal Stability (10.0)** — Quarterly stability checks (ARI > 0.89)
12. **Technology (11.0)** — Python pipeline + C++ engine + web platform
13. **Web Application (12.0)** — Vercel explorer and Streamlit simulator
14. **Results (13.0)** — Four discovered archetypes and key findings
15. **Limitations (14.0)** — Honest assessment and future work
16. **Conclusion** — Summary with live demo links

## ⌨️ Keyboard Shortcuts

| Key | Action |
|-----|--------|
| `→` `Space` `PageDown` | Next slide |
| `←` `PageUp` | Previous slide |
| `Home` | First slide |
| `End` | Last slide |
| `F` | Toggle fullscreen |
| `P` | Toggle presentation mode |
| `Esc` | Exit presentation mode |

## 🎨 Design System

### Colors

```css
--black: #000000        /* Primary background */
--white: #ffffff        /* Primary text */
--blue-vivid: #0066ff   /* Accent color */
--green-vivid: #10b981  /* Success/validation */
--gray-*: #...          /* 9-step gray scale */
```

### Typography

- **Section Titles:** 180px Charter serif
- **Slide Titles:** 56px Charter serif
- **Body Text:** 20px System sans-serif
- **Code/Data:** 18px SF Mono / Consolas

### Spacing

8px base unit with consistent scaling (`--space-xs` to `--space-3xl`)

## 🚀 Usage

### Local Development

1. Open `presentation/index.html` in a modern browser:
   ```cmd
   start presentation\index.html
   ```

2. Navigate with arrow keys or on-screen controls

3. Press `F` for fullscreen, `P` for presentation mode

### Live Presentation

1. Press `P` to enter presentation mode
2. Auto-enters fullscreen
3. Controls auto-hide (hover to reveal)
4. Navigate with arrow keys or clicker

### Export to PowerPoint

1. Click **"Export to PowerPoint"** button (top-right)
2. Wait for processing (may take 10-20 seconds)
3. Downloads `Energy_Consumption_Analysis_YYYY-MM-DD.pptx`
4. Compatible with PowerPoint 2016+ and Google Slides

## 📦 Assets

The deck loads its images from sibling directories in the repo (relative paths):

- **Mascot:** `../sunee-pitch-deck/sunee-mascot.png` (SUNEE mascot, bottom-left on every slide)
- **Dark-mode figures:** `../dark_mode_plots/figures/` (featured plots: `explained_variance.png`, `elbow_curve.png`, `k_selection_metrics.png`, `silhouette_scores.png`, `hourly_patterns.png`)
- **Ablation figures:** `../dark_mode_plots/ablation/` (5 arms × 5 charts; the full set is documented in the top-level README §22.3)

## 🏗️ Architecture

```
presentation/
├── index.html              # Main presentation file (20 slides)
├── README.md               # This file
├── src/
│   ├── styles/
│   │   └── main.css        # Complete design system
│   ├── script.js           # Navigation and export logic
│   ├── components/         # (Future: reusable components)
│   └── utils/              # (Future: helper functions)
└── assets/                 # (removed; images load from ../dark_mode_plots/ and ../sunee-pitch-deck/)
```

## 🔧 Customization

### Change Accent Color

Edit `src/styles/main.css`:
```css
:root {
    --blue-vivid: #YOUR_COLOR;
}
```

### Modify Typography

```css
:root {
    --font-serif: 'Your Serif Font', serif;
    --font-sans: 'Your Sans Font', sans-serif;
}
```

### Add New Slides

1. Copy a slide `<section>` block in `index.html`
2. Update `data-slide="N"` attribute
3. Add content following existing patterns
4. Update `totalSlides` in script or let it auto-detect

### Embed Additional Plots

```html
<div class="visualization-container">
    <img src="../dark_mode_plots/figures/your_plot.png" 
         alt="Description" 
         class="full-width-viz">
</div>
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
- Internet connection (for PptxGenJS CDN)

## 📱 Responsive Notes

While optimized for 1920×1080 presentation display, the deck includes responsive breakpoints for:
- Development preview on smaller screens
- Mobile/tablet viewing (limited)

**Recommended:** Present on 1920×1080 display or use fullscreen mode.

## 🐛 Troubleshooting

### Images not loading

Check that paths in `index.html` match actual file locations:
```
../dark_mode_plots/figures/explained_variance.png
```

### PowerPoint export fails

1. Check internet connection (PptxGenJS loads from CDN)
2. Try in a different browser
3. Check browser console for errors

### Slides not advancing

1. Ensure JavaScript is enabled
2. Check console for errors
3. Try refreshing the page

## 🔗 Related Links

- **Live Explorer:** https://energy-consumption-pattern.vercel.app
- **Streamlit Simulator:** https://energy-consumption-pattern-vqrh.streamlit.app
- **GitHub Repository:** https://github.com/shaxntanu/Energy-Consumption-Pattern-Analysis-using-PCA-and-K-Means

## 📝 Technical Specifications

- **Resolution:** 1920 × 1080 (16:9)
- **Total Slides:** 34
- **Color Space:** sRGB
- **Font Formats:** Web-safe system fonts
- **Image Format:** PNG (dark mode optimized)
- **Export Format:** PPTX (PowerPoint 2016+)

## 🎓 Credits

- **Design Inspiration:** OpenAI presentation aesthetics
- **Logo:** SUNEE mascot
- **Data Visualizations:** Matplotlib + Seaborn (dark mode)
- **Export Library:** PptxGenJS by GitBrent
- **Project:** Shashwat Gupta

## 📄 License

This presentation deck is part of the Energy Consumption Pattern Analysis project. See main repository LICENSE for details.

---

**Built with precision for technical audiences. Every slide tells the complete story.**
