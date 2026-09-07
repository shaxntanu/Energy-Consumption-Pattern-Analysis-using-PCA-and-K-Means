// ============================================
// SUNEE PITCH DECK - INTERACTIVE CONTROLS
// Navigation + Content Editing + PowerPoint Export
// ============================================

let currentSlide = 1;
const totalSlides = 17;

// Initialize on load
document.addEventListener('DOMContentLoaded', () => {
    initializeNavigation();
    initializeExport();
    updateSlideCounter();
});

// ==================
// SLIDE NAVIGATION
// ==================

function initializeNavigation() {
    // Button navigation
    document.getElementById('prev-btn').addEventListener('click', () => navigateSlide(-1));
    document.getElementById('next-btn').addEventListener('click', () => navigateSlide(1));
    
    // Keyboard navigation
    document.addEventListener('keydown', (e) => {
        if (e.key === 'ArrowLeft' || e.key === 'ArrowUp') {
            navigateSlide(-1);
        } else if (e.key === 'ArrowRight' || e.key === 'ArrowDown' || e.key === ' ') {
            e.preventDefault();
            navigateSlide(1);
        } else if (e.key === 'Home') {
            goToSlide(1);
        } else if (e.key === 'End') {
            goToSlide(totalSlides);
        }
    });
    
    // Touch/swipe support
    let touchStartX = 0;
    let touchEndX = 0;
    
    document.addEventListener('touchstart', (e) => {
        touchStartX = e.changedTouches[0].screenX;
    });
    
    document.addEventListener('touchend', (e) => {
        touchEndX = e.changedTouches[0].screenX;
        handleSwipe();
    });
    
    function handleSwipe() {
        if (touchEndX < touchStartX - 50) {
            navigateSlide(1);
        }
        if (touchEndX > touchStartX + 50) {
            navigateSlide(-1);
        }
    }
}

function navigateSlide(direction) {
    const newSlide = currentSlide + direction;
    
    if (newSlide >= 1 && newSlide <= totalSlides) {
        goToSlide(newSlide);
    }
}

function goToSlide(slideNumber) {
    // Remove active class from current slide
    const currentSlideEl = document.querySelector(`.slide[data-slide="${currentSlide}"]`);
    if (currentSlideEl) {
        currentSlideEl.classList.remove('active');
    }
    
    // Add active class to new slide
    currentSlide = slideNumber;
    const newSlideEl = document.querySelector(`.slide[data-slide="${currentSlide}"]`);
    if (newSlideEl) {
        newSlideEl.classList.add('active');
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
    const exportBtn = document.getElementById('export-btn');
    exportBtn.addEventListener('click', exportToPowerPoint);
}

async function exportToPowerPoint() {
    // Check if PptxGenJS is loaded
    if (typeof PptxGenJS === 'undefined') {
        alert('PowerPoint export library not loaded. Please include PptxGenJS library:\n<script src="https://cdn.jsdelivr.net/npm/pptxgenjs@3.12.0/dist/pptxgen.bundle.js"></script>');
        return;
    }
    
    const exportBtn = document.getElementById('export-btn');
    const originalText = exportBtn.textContent;
    exportBtn.textContent = 'Exporting...';
    exportBtn.disabled = true;
    
    try {
        const pptx = new PptxGenJS();
        
        // Presentation settings
        pptx.layout = 'LAYOUT_16x9';
        pptx.author = 'SUNEE';
        pptx.company = 'SUNEE Energy Intelligence';
        pptx.subject = 'SUNEE Pitch Deck';
        pptx.title = 'SUNEE - Intelligent Energy Intelligence';
        
        // Export each slide
        for (let i = 1; i <= totalSlides; i++) {
            await exportSlide(pptx, i);
        }
        
        // Save the presentation
        await pptx.writeFile({ fileName: 'SUNEE-Pitch-Deck.pptx' });
        
        exportBtn.textContent = '✓ Exported!';
        setTimeout(() => {
            exportBtn.textContent = originalText;
            exportBtn.disabled = false;
        }, 2000);
    } catch (error) {
        console.error('Export error:', error);
        alert('Export failed. Please check console for details.');
        exportBtn.textContent = originalText;
        exportBtn.disabled = false;
    }
}

async function exportSlide(pptx, slideNumber) {
    const slideEl = document.querySelector(`.slide[data-slide="${slideNumber}"]`);
    if (!slideEl) return;
    
    const slide = pptx.addSlide();
    
    // Set slide background
    slide.background = { color: '0a0a0a' };
    
    // Extract content based on slide type
    const slideContent = slideEl.querySelector('.slide-content');
    
    // Get slide title if present
    const title = slideContent.querySelector('.slide-title, .cover-title, .closing-title, .vision-statement, .section-title, .page-title, .big-text');
    if (title) {
        const titleText = title.textContent.trim();
        // Large title for cover (1), vision (16), closing (17)
        const fontSize = (slideNumber === 1 || slideNumber === 16 || slideNumber === 17) ? 72 : 24;

        slide.addText(titleText, {
            x: 0.5,
            y: 0.5,
            w: 9,
            h: 1,
            fontSize: fontSize,
            bold: true,
            color: 'FFFFFF',
            align: 'center'
        });
    }
    
    // Extract main content
    const contentElements = slideContent.querySelectorAll('p, h3, h4, .big-statement, .sdg-desc, .sdg-title, .sdg-number, ul, li');
    let yPos = title ? 2 : 1;
    
    contentElements.forEach((el, index) => {
        if (el.classList.contains('slide-title') ||
            el.classList.contains('cover-title') ||
            el.classList.contains('closing-title') ||
            el.classList.contains('vision-statement') ||
            el.classList.contains('section-title') ||
            el.classList.contains('page-title') ||
            el.classList.contains('big-text')) {
            return; // Skip, already added
        }
        
        const text = el.textContent.trim();
        if (!text) return;
        
        let fontSize = 14;
        let bold = false;
        let color = 'B4B4B4';
        
        if (el.classList.contains('big-statement')) {
            fontSize = 36;
            bold = true;
            color = 'FFFFFF';
        } else if (el.tagName === 'H3') {
            fontSize = 28;
            bold = true;
            color = '00D9FF';
        } else if (el.tagName === 'H4') {
            fontSize = 20;
            bold = true;
            color = 'FFFFFF';
        } else if (el.classList.contains('sdg-title')) {
            fontSize = 20;
            bold = true;
            color = 'FFFFFF';
        } else if (el.classList.contains('sdg-number')) {
            fontSize = 14;
            bold = true;
            color = '00D9FF';
        } else if (el.classList.contains('sdg-desc')) {
            fontSize = 14;
            bold = false;
            color = 'B4B4B4';
        } else if (el.tagName === 'UL') {
            // Handle list - process children
            const listItems = el.querySelectorAll('li');
            listItems.forEach((li, liIndex) => {
                const liText = li.textContent.trim();
                if (!liText) return;
                slide.addText(`• ${liText}`, {
                    x: 0.8,
                    y: yPos,
                    w: 8.5,
                    h: 'auto',
                    fontSize: 13,
                    bold: false,
                    color: 'B4B4B4',
                    valign: 'top'
                });
                yPos += (13 / 72) * 1.4;
            });
            return; // Skip normal processing since we handled it
        } else if (el.tagName === 'LI') {
            // Skip individual LI elements since we process them in UL
            return;
        }

        slide.addText(text, {
            x: 0.5,
            y: yPos,
            w: 9,
            h: 'auto',
            fontSize: fontSize,
            bold: bold,
            color: color,
            valign: 'top'
        });

        yPos += (fontSize / 72) * 1.5;
    });

    // Add footer
    slide.addText('SUNEE', {
        x: 0.5,
        y: 6.8,
        w: 2,
        h: 0.3,
        fontSize: 10,
        color: '6B6B6B'
    });
    
    slide.addText(`${slideNumber}`, {
        x: 8.5,
        y: 6.8,
        w: 1,
        h: 0.3,
        fontSize: 10,
        color: '6B6B6B',
        align: 'right'
    });
}

// ==================
// CONTENT EDITING
// ==================

// Auto-save edited content to localStorage
document.addEventListener('input', (e) => {
    if (e.target.hasAttribute('contenteditable')) {
        saveContent();
    }
});

function saveContent() {
    const slides = document.querySelectorAll('.slide');
    const content = {};
    
    slides.forEach((slide, index) => {
        const editableElements = slide.querySelectorAll('[contenteditable="true"]');
        const slideContent = [];
        
        editableElements.forEach((el, elIndex) => {
            slideContent.push({
                index: elIndex,
                html: el.innerHTML
            });
        });
        
        content[`slide-${index + 1}`] = slideContent;
    });
    
    localStorage.setItem('sunee-deck-content', JSON.stringify(content));
}

function loadContent() {
    const savedContent = localStorage.getItem('sunee-deck-content');
    if (!savedContent) return;
    
    const content = JSON.parse(savedContent);
    const slides = document.querySelectorAll('.slide');
    
    slides.forEach((slide, index) => {
        const slideKey = `slide-${index + 1}`;
        if (!content[slideKey]) return;
        
        const editableElements = slide.querySelectorAll('[contenteditable="true"]');
        const slideContent = content[slideKey];
        
        slideContent.forEach((saved) => {
            if (editableElements[saved.index]) {
                editableElements[saved.index].innerHTML = saved.html;
            }
        });
    });
}

// Load saved content on page load
document.addEventListener('DOMContentLoaded', () => {
    loadContent();
});

// ==================
// UTILITY FUNCTIONS
// ==================

// Reset content to original
function resetContent() {
    if (confirm('Reset all content to original? This cannot be undone.')) {
        localStorage.removeItem('sunee-deck-content');
        location.reload();
    }
}

// Fullscreen toggle
function toggleFullscreen() {
    if (!document.fullscreenElement) {
        document.documentElement.requestFullscreen();
    } else {
        document.exitFullscreen();
    }
}

// Keyboard shortcut: F for fullscreen
document.addEventListener('keydown', (e) => {
    if (e.key === 'f' || e.key === 'F') {
        if (!e.target.hasAttribute('contenteditable')) {
            toggleFullscreen();
        }
    }
});

// ==================
// PRESENTATION MODE
// ==================

let presentationMode = false;

function togglePresentationMode() {
    presentationMode = !presentationMode;
    
    const navControls = document.querySelector('.nav-controls');
    const exportBtn = document.querySelector('.export-btn');
    const hint = document.querySelector('body::after');
    
    if (presentationMode) {
        navControls.style.opacity = '0';
        exportBtn.style.opacity = '0';
        document.body.style.cursor = 'none';
    } else {
        navControls.style.opacity = '1';
        exportBtn.style.opacity = '1';
        document.body.style.cursor = 'default';
    }
}

// Keyboard shortcut: P for presentation mode
document.addEventListener('keydown', (e) => {
    if (e.key === 'p' || e.key === 'P') {
        if (!e.target.hasAttribute('contenteditable')) {
            togglePresentationMode();
        }
    }
});

// Show controls on mouse move in presentation mode
let hideControlsTimeout;
document.addEventListener('mousemove', () => {
    if (presentationMode) {
        const navControls = document.querySelector('.nav-controls');
        const exportBtn = document.querySelector('.export-btn');
        
        navControls.style.opacity = '1';
        exportBtn.style.opacity = '1';
        document.body.style.cursor = 'default';
        
        clearTimeout(hideControlsTimeout);
        hideControlsTimeout = setTimeout(() => {
            navControls.style.opacity = '0';
            exportBtn.style.opacity = '0';
            document.body.style.cursor = 'none';
        }, 2000);
    }
});

console.log('🎯 SUNEE Pitch Deck loaded');
console.log('Keyboard shortcuts:');
console.log('  ← → : Navigate slides');
console.log('  F   : Toggle fullscreen');
console.log('  P   : Presentation mode');
console.log('  Home/End : First/Last slide');
