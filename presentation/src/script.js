// ============================================
// ENERGY CONSUMPTION PATTERN ANALYSIS
// Presentation Script
// ============================================

class PresentationController {
    constructor() {
        this.currentSlide = 1;
        this.totalSlides = 20;
        this.slides = document.querySelectorAll('.slide');
        this.presentationMode = false;
        this.init();
    }

    init() {
        this.setupEventListeners();
        this.updateUI();
        this.showSlide(1);
    }

    setupEventListeners() {
        document.addEventListener('keydown', (e) => this.handleKeyPress(e));
        document.getElementById('prev-btn').addEventListener('click', () => this.previousSlide());
        document.getElementById('next-btn').addEventListener('click', () => this.nextSlide());
        document.getElementById('export-btn').addEventListener('click', () => this.exportToPowerPoint());
        this.setupSwipeHandlers();
    }

    handleKeyPress(e) {
        switch (e.key) {
            case 'ArrowRight': case ' ': case 'PageDown':
                e.preventDefault(); this.nextSlide(); break;
            case 'ArrowLeft': case 'PageUp':
                e.preventDefault(); this.previousSlide(); break;
            case 'Home':
                e.preventDefault(); this.goToSlide(1); break;
            case 'End':
                e.preventDefault(); this.goToSlide(this.totalSlides); break;
            case 'f': case 'F':
                e.preventDefault(); this.toggleFullscreen(); break;
            case 'p': case 'P':
                e.preventDefault(); this.togglePresentationMode(); break;
            case 'Escape':
                if (this.presentationMode) this.togglePresentationMode();
                break;
        }
    }

    nextSlide() { if (this.currentSlide < this.totalSlides) this.goToSlide(this.currentSlide + 1); }
    previousSlide() { if (this.currentSlide > 1) this.goToSlide(this.currentSlide - 1); }

    goToSlide(n) {
        if (n < 1 || n > this.totalSlides) return;
        this.slides[this.currentSlide - 1].classList.remove('active');
        this.currentSlide = n;
        this.slides[this.currentSlide - 1].classList.add('active');
        this.updateUI();
    }

    showSlide(n) {
        this.slides.forEach(s => s.classList.remove('active'));
        this.slides[n - 1].classList.add('active');
        this.updateUI();
    }

    updateUI() {
        document.getElementById('slide-counter').textContent = `${this.currentSlide} / ${this.totalSlides}`;
        const pct = (this.currentSlide / this.totalSlides) * 100;
        document.getElementById('progress-fill').style.width = `${pct}%`;
        document.getElementById('prev-btn').disabled = this.currentSlide === 1;
        document.getElementById('next-btn').disabled = this.currentSlide === this.totalSlides;
    }

    toggleFullscreen() {
        if (!document.fullscreenElement) {
            document.documentElement.requestFullscreen().catch(() => {});
        } else if (document.exitFullscreen) {
            document.exitFullscreen();
        }
    }

    togglePresentationMode() {
        this.presentationMode = !this.presentationMode;
        document.body.classList.toggle('presentation-mode', this.presentationMode);
        if (this.presentationMode && !document.fullscreenElement) this.toggleFullscreen();
    }

    setupSwipeHandlers() {
        let startX = 0;
        document.addEventListener('touchstart', (e) => { startX = e.changedTouches[0].screenX; });
        document.addEventListener('touchend', (e) => {
            const dx = startX - e.changedTouches[0].screenX;
            if (Math.abs(dx) > 50) { dx > 0 ? this.nextSlide() : this.previousSlide(); }
        });
    }

    // ============================================
    // POWERPOINT EXPORT
    // ============================================

    async exportToPowerPoint() {
        try {
            if (typeof PptxGenJS === 'undefined') {
                alert('PowerPoint export library not loaded. Check your internet connection.'); return;
            }
            const pptx = new PptxGenJS();
            pptx.author = 'Energy Consumption Pattern Analysis';
            pptx.title = 'Energy Consumption Pattern Analysis — PCA and K-Means';
            pptx.defineLayout({ name: 'CUSTOM', width: 10, height: 5.625 });
            pptx.layout = 'CUSTOM';

            for (let i = 0; i < this.totalSlides; i++) {
                await this.exportSlide(pptx, i + 1);
            }
            const fn = `Energy_Consumption_Analysis_${new Date().toISOString().split('T')[0]}.pptx`;
            await pptx.writeFile({ fileName: fn });
            alert(`Exported as ${fn}`);
        } catch (err) {
            console.error('Export error:', err);
            alert('Export failed. Check console for details.');
        }
    }

    async exportSlide(pptx, slideNumber) {
        const slide = pptx.addSlide();
        const el = this.slides[slideNumber - 1];
        slide.background = { color: '000000' };

        const sc = el.querySelector('.slide-content');
        if (sc && sc.classList.contains('cover')) {
            this._exportCover(slide, el);
        } else {
            this._exportContent(slide, el);
        }
        this._addLogo(slide);
    }

    _exportCover(slide, el) {
        const title = el.querySelector('.cover-title')?.textContent || '';
        const sub = el.querySelector('.cover-subtitle')?.textContent || '';
        const meta = el.querySelector('.cover-meta')?.textContent || '';
        slide.addText(title, { x: 0.5, y: 1.5, w: 9, h: 1.5, fontSize: 56, fontFace: 'Georgia', color: 'FFFFFF', valign: 'top' });
        slide.addText(sub, { x: 0.5, y: 3.2, w: 9, h: 0.6, fontSize: 22, color: 'D4D4D4', valign: 'top' });
        slide.addText(meta, { x: 0.5, y: 4.2, w: 9, h: 0.4, fontSize: 12, fontFace: 'Courier New', color: '5B657A', valign: 'top' });
    }

    _exportContent(slide, el) {
        const kicker = el.querySelector('.slide-label')?.textContent || '';
        const title = el.querySelector('.slide-title')?.textContent || '';

        if (kicker) {
            slide.addText(kicker, { x: 0.5, y: 0.35, w: 9, h: 0.3, fontSize: 11, color: '5B657A', fontFace: 'Arial', valign: 'top' });
        }
        if (title) {
            slide.addText(title, { x: 0.5, y: 0.75, w: 9, h: 0.9, fontSize: 30, fontFace: 'Georgia', color: 'EAECEF', valign: 'top' });
        }

        // Charts - PLACEHOLDER FOR MANUAL IMAGE INSERTION
        // Images cannot be loaded from file:// URLs due to CORS restrictions
        // To add charts to exported PowerPoint:
        // 1. Export the presentation
        // 2. Open the .pptx file
        // 3. Manually insert images from dark_mode_plots/figures/ folder
        // 4. Position them in the main content area
        
        const imgs = el.querySelectorAll('img[src*="dark_mode_plots"]');
        let yOff = 1.8;
        if (imgs.length > 0) {
            slide.addText('[CHART PLACEHOLDER - Insert image manually from dark_mode_plots/figures/]', 
                { x: 0.5, y: yOff, w: 9, h: 1, fontSize: 14, color: '5B657A', fontFace: 'Courier New', valign: 'middle', align: 'center' });
        }
        
        // Original image code (commented out due to CORS):
        // imgs.forEach((img, i) => {
        //     try {
        //         slide.addImage({ path: img.src, x: 0.5, y: yOff + i * 0.15, w: 9, h: 3, sizing: { type: 'contain' } });
        //     } catch (e) { console.warn('Image skip:', img.src); }
        // });

        // Tables (export as text)
        const tables = el.querySelectorAll('.data-table');
        tables.forEach(t => {
            let rows = [];
            t.querySelectorAll('tr').forEach(tr => {
                let cells = [];
                tr.querySelectorAll('th, td').forEach(td => {
                    cells.push({ text: td.textContent.trim(), options: { fontSize: 11, color: 'EAECEF', fontFace: 'Courier New' } });
                });
                rows.push(cells);
            });
            if (rows.length) {
                slide.addTable(rows, { x: 0.5, y: yOff, w: 9, border: { pt: 0.5, color: '262E3D' } });
            }
        });

        // Body text
        const ps = el.querySelectorAll('.content-card p, .info-box p');
        let tY = 4.8;
        ps.forEach((p, i) => {
            if (i < 3) {
                const t = p.textContent.trim();
                if (t.length > 0 && t.length < 200) {
                    slide.addText(t, { x: 0.5, y: tY, w: 9, h: 0.5, fontSize: 13, color: '8A93A6', valign: 'top' });
                    tY += 0.55;
                }
            }
        });

        // Source line
        const src = el.querySelector('.source');
        if (src) {
            slide.addText(src.textContent.trim(), { x: 0.5, y: 5.0, w: 9, h: 0.3, fontSize: 9, fontFace: 'Courier New', color: '5B657A', valign: 'bottom' });
        }
    }

    _addLogo(slide) {
        slide.addText('SUNEE', { x: 8.8, y: 5.1, w: 1, h: 0.3, fontSize: 10, color: '5B657A', bold: true, valign: 'bottom' });
    }
}

// --- Init ---
document.addEventListener('DOMContentLoaded', () => {
    const p = new PresentationController();
    window.presentation = p;
});

// Prevent ctrl+zoom
document.addEventListener('wheel', (e) => { if (e.ctrlKey) e.preventDefault(); }, { passive: false });

// Hash-based deep linking
window.addEventListener('popstate', () => {
    const n = parseInt(window.location.hash.replace('#', ''));
    if (n && !isNaN(n)) window.presentation?.goToSlide(n);
});
