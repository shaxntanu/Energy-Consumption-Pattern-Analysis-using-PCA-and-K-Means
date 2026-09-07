// ============================================
// SUNEE ACADEMIC DECK — INTERACTIVE CONTROLS
// Navigation + Content Editing + PowerPoint Export
// ============================================

let currentSlide = 1;
const totalSlides = 20;

// Initialize on load
document.addEventListener('DOMContentLoaded', () => {
    initializeNavigation();
    initializeExport();
    updateSlideCounter();
    loadContent();
});

// ==================
// SLIDE NAVIGATION
// ==================

function initializeNavigation() {
    document.getElementById('prev-btn').addEventListener('click', () => navigateSlide(-1));
    document.getElementById('next-btn').addEventListener('click', () => navigateSlide(1));

    document.addEventListener('keydown', (e) => {
        if (e.target.hasAttribute('contenteditable')) return;

        if (e.key === 'ArrowLeft' || e.key === 'ArrowUp') {
            navigateSlide(-1);
        } else if (e.key === 'ArrowRight' || e.key === 'ArrowDown' || e.key === ' ') {
            e.preventDefault();
            navigateSlide(1);
        } else if (e.key === 'Home') {
            goToSlide(1);
        } else if (e.key === 'End') {
            goToSlide(totalSlides);
        } else if (e.key === 'f' || e.key === 'F') {
            toggleFullscreen();
        } else if (e.key === 'p' || e.key === 'P') {
            togglePresentationMode();
        }
    });

    let touchStartX = 0;
    document.addEventListener('touchstart', (e) => {
        touchStartX = e.changedTouches[0].screenX;
    });
    document.addEventListener('touchend', (e) => {
        const touchEndX = e.changedTouches[0].screenX;
        if (touchEndX < touchStartX - 50) navigateSlide(1);
        if (touchEndX > touchStartX + 50) navigateSlide(-1);
    });
}

function navigateSlide(direction) {
    const newSlide = currentSlide + direction;
    if (newSlide >= 1 && newSlide <= totalSlides) {
        goToSlide(newSlide);
    }
}

function goToSlide(slideNumber) {
    const currentEl = document.querySelector(`.slide[data-slide="${currentSlide}"]`);
    if (currentEl) currentEl.classList.remove('active');

    currentSlide = slideNumber;
    const newEl = document.querySelector(`.slide[data-slide="${currentSlide}"]`);
    if (newEl) {
        newEl.classList.add('active');
        // Scroll slide content to top
        const content = newEl.querySelector('.slide-content');
        if (content) content.scrollTop = 0;
    }
    updateSlideCounter();
}

function updateSlideCounter() {
    const counter = document.getElementById('slide-counter');
    counter.textContent = `${currentSlide} / ${totalSlides}`;
}

// ==================
// POWERPOINT EXPORT
// ==================

function initializeExport() {
    document.getElementById('export-btn').addEventListener('click', exportToPowerPoint);
}

async function chartToBase64(imgEl) {
    try {
        const src = imgEl.currentSrc || imgEl.src;
        if (!src) return null;
        const image = new Image();
        image.crossOrigin = 'anonymous';
        await new Promise((resolve, reject) => {
            image.onload = resolve;
            image.onerror = reject;
            image.src = src;
        });
        if (!image.naturalWidth || !image.naturalHeight) return null;
        const canvas = document.createElement('canvas');
        canvas.width = image.naturalWidth;
        canvas.height = image.naturalHeight;
        canvas.getContext('2d').drawImage(image, 0, 0);
        return canvas.toDataURL('image/png');
    } catch (e) {
        console.warn('Chart embed failed:', e);
        return null;
    }
}

function resolveChartPath(path) {
    try { return new URL(path, document.baseURI).href; }
    catch (e) { return path; }
}

function fitBox(naturalW, naturalH, boxW, boxH) {
    const ratio = Math.min(boxW / naturalW, boxH / naturalH);
    return { w: naturalW * ratio, h: naturalH * ratio };
}

async function exportToPowerPoint() {
    if (typeof PptxGenJS === 'undefined') {
        alert('PowerPoint export library not loaded.');
        return;
    }

    const exportBtn = document.getElementById('export-btn');
    const originalText = exportBtn.textContent;
    exportBtn.textContent = 'Exporting...';
    exportBtn.disabled = true;

    const missingCharts = [];

    try {
        const pptx = new PptxGenJS();
        pptx.layout = 'LAYOUT_16x9';
        pptx.author = 'SUNEE';
        pptx.company = 'SUNEE Energy Analytics';
        pptx.subject = 'Characterizing Household Energy Consumption Patterns';
        pptx.title = 'SUNEE — PCA and K-Means Analysis';

        for (let i = 1; i <= totalSlides; i++) {
            missingCharts.push(...(await exportSlide(pptx, i)));
        }

        await pptx.writeFile({ fileName: 'SUNEE-Academic-Deck.pptx' });

        exportBtn.textContent = '✓ Exported!';
        setTimeout(() => {
            exportBtn.textContent = originalText;
            exportBtn.disabled = false;
        }, 2000);

        if (missingCharts.length > 0) {
            const lines = missingCharts.map(p => `  ${resolveChartPath(p)}`);
            alert(
                'PowerPoint saved.\n\nSome chart images could not be embedded (browser security).\n' +
                'Place these files manually:\n\n' + lines.join('\n')
            );
        } else {
            alert('PowerPoint saved with all charts embedded.');
        }
    } catch (error) {
        console.error('Export error:', error);
        alert('Export failed. Check console for details.');
        exportBtn.textContent = originalText;
        exportBtn.disabled = false;
    }
}

async function exportSlide(pptx, slideNumber) {
    const slideEl = document.querySelector(`.slide[data-slide="${slideNumber}"]`);
    if (!slideEl) return [];

    const slide = pptx.addSlide();
    slide.background = { color: '0a0a0a' };

    const slideContent = slideEl.querySelector('.slide-content');
    const missingCharts = [];

    // ---- Charts ----
    const chartImgs = slideContent.querySelectorAll('.chart-img');
    if (chartImgs.length > 0) {
        return await placeCharts(slide, slideContent, chartImgs, missingCharts, slideNumber);
    }

    // ---- Title (cover slides) ----
    const isCover = slideEl.classList.contains('cover');
    let yPos = 0.55;

    // Eyebrow / kicker
    const kickerEl = slideContent.querySelector('.kicker');
    if (kickerEl && kickerEl.textContent.trim()) {
        slide.addText(kickerEl.textContent.trim().toUpperCase(), {
            x: 0.6, y: yPos, w: 11, h: 0.3,
            fontSize: 11, bold: true, color: '00D9FF',
            fontFace: 'Consolas', charSpacing: 2
        });
        yPos += 0.42;
    }

    // Headline
    const titleEl = slideContent.querySelector('.headline, .closing-title');
    if (titleEl && titleEl.textContent.trim()) {
        slide.addText(titleEl.textContent.trim(), {
            x: 0.6, y: yPos, w: 12.1, h: isCover ? 1.8 : 1.2,
            fontSize: isCover ? 36 : 28,
            bold: false, color: 'FFFFFF',
            align: isCover ? 'center' : 'left',
            valign: 'top', breakLine: true
        });
        yPos += isCover ? 1.6 : 1.2;
    }

    // Subtitle
    const subtitleEl = slideContent.querySelector('.subtitle, .closing-sub');
    if (subtitleEl && subtitleEl.textContent.trim()) {
        slide.addText(subtitleEl.textContent.trim(), {
            x: 0.6, y: yPos, w: 12.1, h: 0.6,
            fontSize: 16, color: 'B4B4B4', valign: 'top',
            align: isCover ? 'center' : 'left'
        });
        yPos += 0.8;
    }

    // Lead paragraph
    const leadEl = slideContent.querySelector('.lead');
    if (leadEl && leadEl.textContent.trim()) {
        slide.addText(leadEl.textContent.trim(), {
            x: 0.6, y: yPos, w: 12.1, h: 0.8,
            fontSize: 15, color: 'B4B4B4', valign: 'top'
        });
        yPos += 0.9;
    }

    yPos = Math.max(yPos, 2.0);

    // ---- Metric cards ----
    const metricCards = slideContent.querySelectorAll('.metric-card');
    if (metricCards.length > 0) {
        const mcWidth = Math.min(2.8, 11.5 / metricCards.length);
        metricCards.forEach((card, i) => {
            const value = card.querySelector('.metric-value');
            const label = card.querySelector('.metric-label');
            const x = 0.6 + i * (mcWidth + 0.2);
            if (value && value.textContent.trim()) {
                slide.addText(value.textContent.trim(), {
                    x: x, y: yPos, w: mcWidth, h: 0.5,
                    fontSize: 22, bold: true, color: '00D9FF',
                    fontFace: 'Consolas', align: 'center'
                });
            }
            if (label && label.textContent.trim()) {
                slide.addText(label.textContent.trim(), {
                    x: x, y: yPos + 0.45, w: mcWidth, h: 0.35,
                    fontSize: 10, color: '6B6B6B', align: 'center',
                    fontFace: 'Consolas'
                });
            }
        });
        yPos += 1.0;
    }

    // ---- Cards ----
    const cards = slideContent.querySelectorAll('.card');
    if (cards.length > 0 && yPos < 6.5) {
        const cols = cards.length <= 2 ? 2 : cards.length <= 4 ? 2 : 3;
        const cardW = (12.1 - (cols - 1) * 0.2) / cols;
        cards.forEach((card, i) => {
            if (i >= 6) return;
            const col = i % cols;
            const row = Math.floor(i / cols);
            const x = 0.6 + col * (cardW + 0.2);
            const y = yPos + row * 1.4;
            if (y > 6.0) return;

            let textRuns = [];
            const tag = card.querySelector('.tag');
            const h3 = card.querySelector('h3');
            const p = card.querySelector('p');
            if (tag && tag.textContent.trim()) {
                textRuns.push({ text: tag.textContent.trim().toUpperCase() + '\n', options: { fontSize: 9, color: '00D9FF', fontFace: 'Consolas', bold: true } });
            }
            if (h3 && h3.textContent.trim()) {
                textRuns.push({ text: h3.textContent.trim() + '\n', options: { fontSize: 14, color: 'FFFFFF', bold: true } });
            }
            if (p && p.textContent.trim()) {
                textRuns.push({ text: p.textContent.trim(), options: { fontSize: 11, color: 'B4B4B4' } });
            }
            if (textRuns.length) {
                slide.addText(textRuns, { x: x, y: y, w: cardW, h: 1.3, valign: 'top' });
            }
        });
    }

    // ---- Tables ----
    const tables = slideContent.querySelectorAll('.data-table');
    if (tables.length > 0) {
        tables.forEach((table) => {
            const rows = [];
            // Header
            const headers = [];
            table.querySelectorAll('thead th').forEach(th => {
                headers.push({ text: th.textContent.trim(), options: { fontSize: 9, bold: true, color: 'FFFFFF', fontFace: 'Consolas' } });
            });
            rows.push(headers);
            // Body
            table.querySelectorAll('tbody tr').forEach(tr => {
                const cells = [];
                tr.querySelectorAll('td').forEach(td => {
                    const isHighlight = td.classList.contains('highlight');
                    cells.push({
                        text: td.textContent.trim(),
                        options: { fontSize: 10, color: isHighlight ? '00D9FF' : 'B4B4B4', fontFace: td.classList.contains('mono') ? 'Consolas' : 'Calibri' }
                    });
                });
                rows.push(cells);
            });
            slide.addTable(rows, {
                x: 0.6, y: yPos, w: 12.1,
                border: { type: 'solid', pt: 0.5, color: '3D3A39' },
                colW: Array(headers.length).fill(12.1 / headers.length),
                rowH: 0.35,
                autoPage: false
            });
        });
    }

    // ---- Bullet lists ----
    const bullets = slideContent.querySelectorAll('.bullet-list li');
    if (bullets.length > 0) {
        let bulletY = yPos;
        bullets.forEach((li) => {
            if (bulletY > 6.5) return;
            slide.addText('  ' + li.textContent.trim(), {
                x: 0.6, y: bulletY, w: 12.1, h: 0.35,
                fontSize: 13, color: 'B4B4B4', valign: 'top'
            });
            bulletY += 0.38;
        });
    }

    // ---- References ----
    const refs = slideContent.querySelectorAll('.ref-list li');
    if (refs.length > 0) {
        let refY = yPos;
        refs.forEach((li) => {
            if (refY > 6.8) return;
            const num = li.querySelector('.ref-num');
            const text = li.querySelector('span:last-child') || li;
            slide.addText(
                [
                    { text: (num ? num.textContent.trim() + ' ' : ''), options: { color: '00D9FF', bold: true, fontFace: 'Consolas', fontSize: 11 } },
                    { text: text.textContent.trim(), options: { color: 'B4B4B4', fontSize: 11 } }
                ],
                { x: 0.6, y: refY, w: 12.1, h: 0.4, valign: 'top' }
            );
            refY += 0.42;
        });
    }

    // ---- Contact / footer line ----
    const contactEl = slideContent.querySelector('.contact-line');
    if (contactEl && contactEl.textContent.trim()) {
        slide.addText(contactEl.textContent.trim(), {
            x: 0.6, y: 6.4, w: 12.1, h: 0.4,
            fontSize: 12, color: '6B6B6B', align: 'center', fontFace: 'Consolas'
        });
    }

    // ---- Section titles (for limitations page) ----
    const sectionTitles = slideContent.querySelectorAll('.section-title');
    if (sectionTitles.length > 0 && yPos < 5.0) {
        sectionTitles.forEach(st => {
            slide.addText(st.textContent.trim(), {
                x: 0.6, y: yPos, w: 5.5, h: 0.35,
                fontSize: 16, bold: true, color: 'FFFFFF'
            });
            yPos += 0.4;
        });
    }

    addFooter(slide, slideNumber);
    return missingCharts;
}

async function placeCharts(slide, slideContent, chartImgs, missingCharts, slideNumber) {
    const isPair = chartImgs.length > 1;
    const imgTop = isPair ? 2.0 : 1.8;
    const imgBottom = 6.3;

    for (let index = 0; index < chartImgs.length; index++) {
        const imgEl = chartImgs[index];
        const path = imgEl.getAttribute('data-chart-path') || imgEl.getAttribute('src') || 'chart.png';
        const b64 = await chartToBase64(imgEl);

        if (b64) {
            const naturalW = imgEl.naturalWidth || 1600;
            const naturalH = imgEl.naturalHeight || 900;
            const boxW = isPair ? 5.9 : 12.1;
            const boxH = imgBottom - imgTop;
            const fit = fitBox(naturalW, naturalH, boxW, boxH);
            const x = isPair ? 0.6 + index * 6.15 : 0.6 + (boxW - fit.w) / 2;
            const y = imgTop + (boxH - fit.h) / 2;
            slide.addImage({ data: b64, x: x, y: y, w: fit.w, h: fit.h });
        } else {
            missingCharts.push(path);
            const noteX = isPair ? 0.6 + index * 6.15 : 0.6;
            slide.addText(`[ Chart ]\nPlace:\n${path}`, {
                x: noteX, y: imgTop + 0.2, w: isPair ? 5.9 : 12.1, h: 3.0,
                fontSize: 11, color: '00D9FF', fontFace: 'Consolas', valign: 'top'
            });
        }
    }

    // Captions
    const captions = slideContent.querySelectorAll('.chart-caption');
    captions.forEach((cap) => {
        if (cap.textContent.trim()) {
            slide.addText(cap.textContent.trim(), {
                x: 0.6, y: 6.4, w: 12.1, h: 0.5,
                fontSize: 10, color: '6B6B6B', italic: true, valign: 'top'
            });
        }
    });

    // Metric cards below charts
    const metricCards = slideContent.querySelectorAll('.metric-card');
    if (metricCards.length > 0) {
        const mcWidth = Math.min(2.8, 11.5 / metricCards.length);
        metricCards.forEach((card, i) => {
            const value = card.querySelector('.metric-value');
            const label = card.querySelector('.metric-label');
            const x = 0.6 + i * (mcWidth + 0.2);
            const y = 6.4;
            if (value && value.textContent.trim()) {
                slide.addText(value.textContent.trim(), {
                    x: x, y: y, w: mcWidth, h: 0.3,
                    fontSize: 16, bold: true, color: '00D9FF',
                    fontFace: 'Consolas', align: 'center'
                });
            }
            if (label && label.textContent.trim()) {
                slide.addText(label.textContent.trim(), {
                    x: x, y: y + 0.28, w: mcWidth, h: 0.25,
                    fontSize: 8, color: '6B6B6B', align: 'center',
                    fontFace: 'Consolas'
                });
            }
        });
    }

    addFooter(slide, slideNumber);
    return missingCharts;
}

function addFooter(slide, slideNumber) {
    slide.addText('SUNEE · PCA + K-Means Energy Analysis', {
        x: 0.6, y: 7.05, w: 6, h: 0.3,
        fontSize: 9, color: '6B6B6B', fontFace: 'Consolas'
    });
    slide.addText(`${slideNumber} / ${totalSlides}`, {
        x: 10.7, y: 7.05, w: 2, h: 0.3,
        fontSize: 9, color: '6B6B6B', align: 'right', fontFace: 'Consolas'
    });
}

// ==================
// CONTENT EDITING
// ==================

document.addEventListener('input', (e) => {
    if (e.target.hasAttribute('contenteditable')) saveContent();
});

function saveContent() {
    const content = {};
    document.querySelectorAll('.slide').forEach((slide, index) => {
        const editables = slide.querySelectorAll('[contenteditable="true"]');
        const slideData = [];
        editables.forEach((el, i) => {
            slideData.push({ index: i, html: el.innerHTML });
        });
        content[`slide-${index + 1}`] = slideData;
    });
    try { localStorage.setItem('sunee-deck-content', JSON.stringify(content)); }
    catch (e) { console.warn('Could not save:', e); }
}

function loadContent() {
    let saved;
    try { saved = localStorage.getItem('sunee-deck-content'); }
    catch (e) { return; }
    if (!saved) return;

    try {
        const content = JSON.parse(saved);
        document.querySelectorAll('.slide').forEach((slide, index) => {
            const key = `slide-${index + 1}`;
            if (!content[key]) return;
            const editables = slide.querySelectorAll('[contenteditable="true"]');
            content[key].forEach(s => {
                if (editables[s.index]) editables[s.index].innerHTML = s.html;
            });
        });
    } catch (e) { console.warn('Could not restore:', e); }
}

function resetContent() {
    if (confirm('Reset all content to original? This cannot be undone.')) {
        try { localStorage.removeItem('sunee-deck-content'); } catch (e) {}
        location.reload();
    }
}

// ==================
// UTILITY
// ==================

function toggleFullscreen() {
    if (!document.fullscreenElement) {
        document.documentElement.requestFullscreen();
    } else {
        document.exitFullscreen();
    }
}

let presentationMode = false;
let hideControlsTimeout;

function togglePresentationMode() {
    presentationMode = !presentationMode;
    document.body.classList.toggle('presenting', presentationMode);
}

document.addEventListener('mousemove', () => {
    if (presentationMode) {
        document.body.classList.remove('presenting');
        clearTimeout(hideControlsTimeout);
        hideControlsTimeout = setTimeout(() => {
            if (presentationMode) document.body.classList.add('presenting');
        }, 2000);
    }
});

console.log('%c▶ SUNEE Academic Deck loaded', 'color:#00d992;font-weight:bold');
console.log('%c← → Navigate  |  F Fullscreen  |  P Present  |  Home/End Jump', 'color:#8b949e');
