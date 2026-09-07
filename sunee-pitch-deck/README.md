# SUNEE Pitch Deck

A modern, browser-based presentation deck for SUNEE - Intelligent Energy Intelligence platform.

## Features

### 🎨 Premium Design System
- Dark mode optimized for presentations and projectors
- Gradient accents with cyan (#00D9FF) and violet (#7C3AED)
- Clean typography with excellent readability
- Smooth transitions between slides

### ⌨️ Interactive Navigation
- **Arrow Keys** (← →): Navigate between slides
- **Space Bar**: Next slide
- **Home/End**: Jump to first/last slide
- **Click Navigation**: On-screen buttons with slide counter
- **Touch/Swipe**: Full mobile support

### ✏️ Editable Content
- **Click any text** to edit inline (contenteditable)
- **Auto-save**: All changes saved to localStorage
- **Persistent**: Edits remain after page reload
- **Reset**: Clear localStorage to restore original content

### 📊 PowerPoint Export
- Export to `.pptx` format with one click
- Preserves layout, content, and branding
- Requires PptxGenJS library (see setup below)

### 🎭 Presentation Mode
- **Press P**: Hide controls, auto-hide cursor
- **Mouse movement**: Temporarily shows controls
- **Press F**: Toggle fullscreen

## Quick Start

### 1. Open the Deck
```bash
# Simply open in any modern browser
start index.html
```

Or use a local server:
```bash
# Python
python -m http.server 8000

# Node.js
npx serve

# Then open http://localhost:8000
```

### 2. Enable PowerPoint Export (Optional)
Add this line before the closing `</body>` tag in `index.html`:
```html
<script src="https://cdn.jsdelivr.net/npm/pptxgenjs@3.12.0/dist/pptxgen.bundle.js"></script>
```

## Slide Structure

The deck contains **12 slides**:

1. **Cover** - SUNEE branding and tagline
2. **The Problem** - Industry pain points
3. **Why Now** - Market timing and opportunity
4. **Introducing SUNEE** - Product introduction
5. **How It Works** - Platform workflow (4-step process)
6. **Platform Capabilities** - 6 key features
7. **Product Experience** - Dashboard and use cases
8. **Technology** - ML pipeline and architecture
9. **Market Opportunity** - TAM breakdown ($40B+)
10. **Competitive Advantage** - Differentiation matrix
11. **Vision** - Long-term mission statement
12. **Closing** - Contact information

## Customization

### Colors
Edit `styles.css` variables:
```css
:root {
    --bg-primary: #0a0a0a;
    --accent-primary: #00d9ff;
    --accent-secondary: #7c3aed;
    /* ... */
}
```

### Content
All text is contenteditable by default:
- Click any text to edit
- Changes auto-save to localStorage
- Refresh page to reload saved content

### Slides
Add/remove slides in `index.html`:
```html
<div class="slide" data-slide="13">
    <div class="slide-content">
        <!-- Your content -->
    </div>
</div>
```

Update `totalSlides` in `script.js`:
```javascript
const totalSlides = 13; // Change this number
```

## Keyboard Reference

| Key | Action |
|-----|--------|
| `←` `→` | Previous/Next slide |
| `↑` `↓` | Previous/Next slide |
| `Space` | Next slide |
| `Home` | First slide |
| `End` | Last slide |
| `F` | Toggle fullscreen |
| `P` | Presentation mode |

## Browser Compatibility

- ✅ Chrome/Edge (recommended)
- ✅ Firefox
- ✅ Safari
- ✅ Mobile browsers (iOS, Android)

## File Structure

```
sunee-pitch-deck/
├── index.html          # Main presentation file
├── styles.css          # Design system and styling
├── script.js           # Navigation and interaction logic
├── README.md           # This file
└── assets/             # Optional: images, icons, fonts
    ├── images/
    ├── icons/
    └── fonts/
```

## Tips for Presenting

1. **Before presenting**: Press `F` for fullscreen, then `P` for presentation mode
2. **During editing**: Click any text to customize for your audience
3. **For export**: Add PptxGenJS script tag, click "Export to PowerPoint"
4. **On mobile**: Use swipe gestures to navigate

## Technical Details

- **No build process**: Pure HTML/CSS/JS
- **No dependencies**: Works offline (except PowerPoint export)
- **Lightweight**: ~40KB total (uncompressed)
- **Standards-compliant**: Modern ES6+, CSS Grid, Flexbox

## License

Part of the SUNEE Energy Intelligence project.

---

**Built for SUNEE** | Intelligent Energy Intelligence Platform
