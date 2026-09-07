// ============================================
// ENERGY CONSUMPTION PATTERN ANALYSIS
// Presentation Script
// ============================================

class PresentationController {
    constructor() {
        this.currentSlide = 1;
        this.totalSlides = 20; // Fixed to match 20-slide presentation
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
        // Keyboard navigation
        document.addEventListener('keydown', (e) => this.handleKeyPress(e));
        
        // Button navigation
        document.getElementById('prev-btn').addEventListener('click', () => this.previousSlide());
        document.getElementById('next-btn').addEventListener('click', () => this.nextSlide());
        
        // Export button
        document.getElementById('export-btn').addEventListener('click', () => this.exportToPowerPoint());
        
        // Touch/swipe support (optional)
        this.setupSwipeHandlers();
    }
    
    handleKeyPress(e) {
        switch(e.key) {
            case 'ArrowRight':
            case ' ':
            case 'PageDown':
                e.preventDefault();
                this.nextSlide();
                break;
            case 'ArrowLeft':
            case 'PageUp':
                e.preventDefault();
                this.previousSlide();
                break;
            case 'Home':
                e.preventDefault();
                this.goToSlide(1);
                break;
            case 'End':
                e.preventDefault();
                this.goToSlide(this.totalSlides);
                break;
            case 'f':
            case 'F':
                e.preventDefault();
                this.toggleFullscreen();
                break;
            case 'p':
            case 'P':
                e.preventDefault();
                this.togglePresentationMode();
                break;
            case 'Escape':
                if (this.presentationMode) {
                    this.togglePresentationMode();
                }
                break;
        }
    }
    
    nextSlide() {
        if (this.currentSlide < this.totalSlides) {
            this.goToSlide(this.currentSlide + 1);
        }
    }
    
    previousSlide() {
        if (this.currentSlide > 1) {
            this.goToSlide(this.currentSlide - 1);
        }
    }
    
    goToSlide(slideNumber) {
        if (slideNumber < 1 || slideNumber > this.totalSlides) return;
        
        // Hide current slide
        this.slides[this.currentSlide - 1].classList.remove('active');
        
        // Show new slide
        this.currentSlide = slideNumber;
        this.slides[this.currentSlide - 1].classList.add('active');
        
        this.updateUI();
    }
    
    showSlide(slideNumber) {
        this.slides.forEach(slide => slide.classList.remove('active'));
        this.slides[slideNumber - 1].classList.add('active');
        this.updateUI();
    }
    
    updateUI() {
        // Update counter
        document.getElementById('slide-counter').textContent = `${this.currentSlide} / ${this.totalSlides}`;
        
        // Update progress bar
        const progress = (this.currentSlide / this.totalSlides) * 100;
        document.getElementById('progress-fill').style.width = `${progress}%`;
        
        // Update button states
        document.getElementById('prev-btn').disabled = this.currentSlide === 1;
        document.getElementById('next-btn').disabled = this.currentSlide === this.totalSlides;
    }
    
    toggleFullscreen() {
        if (!document.fullscreenElement) {
            document.documentElement.requestFullscreen().catch(err => {
                console.error('Error attempting to enable fullscreen:', err);
            });
        } else {
            if (document.exitFullscreen) {
                document.exitFullscreen();
            }
        }
    }
    
    togglePresentationMode() {
        this.presentationMode = !this.presentationMode;
        
        if (this.presentationMode) {
            document.body.classList.add('presentation-mode');
            // Auto-enter fullscreen in presentation mode
            if (!document.fullscreenElement) {
                this.toggleFullscreen();
            }
        } else {
            document.body.classList.remove('presentation-mode');
        }
    }
    
    setupSwipeHandlers() {
        let touchStartX = 0;
        let touchEndX = 0;
        
        document.addEventListener('touchstart', (e) => {
            touchStartX = e.changedTouches[0].screenX;
        });
        
        document.addEventListener('touchend', (e) => {
            touchEndX = e.changedTouches[0].screenX;
            this.handleSwipe();
        });
        
        const handleSwipe = () => {
            const swipeThreshold = 50;
            const diff = touchStartX - touchEndX;
            
            if (Math.abs(diff) > swipeThreshold) {
                if (diff > 0) {
                    this.nextSlide();
                } else {
                    this.previousSlide();
                }
            }
        };
        
        this.handleSwipe = handleSwipe;
    }
    
    // ============================================
    // POWERPOINT EXPORT
    // ============================================
    
    async exportToPowerPoint() {
        try {
            console.log('Starting PowerPoint export...');
            
            // Check if PptxGenJS is loaded
            if (typeof PptxGenJS === 'undefined') {
                alert('PowerPoint export library not loaded. Please check your internet connection.');
                return;
            }
            
            const pptx = new PptxGenJS();
            
            // Set presentation properties
            pptx.author = 'Energy Consumption Pattern Analysis';
            pptx.company = 'SUNEE';
            pptx.title = 'Energy Consumption Pattern Analysis — PCA and K-Means';
            pptx.subject = 'Machine Learning Analysis Presentation';
            
            // Define slide layout (16:9)
            pptx.defineLayout({ name: 'CUSTOM', width: 10, height: 5.625 });
            pptx.layout = 'CUSTOM';
            
            // Export each slide
            for (let i = 0; i < this.totalSlides; i++) {
                await this.exportSlide(pptx, i + 1);
            }
            
            // Save the presentation
            const filename = `Energy_Consumption_Analysis_${new Date().toISOString().split('T')[0]}.pptx`;
            await pptx.writeFile({ fileName: filename });
            
            console.log('PowerPoint export complete!');
            alert(`Presentation exported successfully as ${filename}`);
            
        } catch (error) {
            console.error('Error exporting to PowerPoint:', error);
            alert('Error exporting presentation. Check console for details.');
        }
    }
    
    async exportSlide(pptx, slideNumber) {
        const slide = pptx.addSlide();
        const slideElement = this.slides[slideNumber - 1];
        
        // Set black background
        slide.background = { color: '000000' };
        
        // Get slide content
        const slideContent = slideElement.querySelector('.slide-content');
        
        // Detect slide type and export accordingly
        if (slideContent.classList.contains('cover')) {
            this.exportCoverSlide(slide, slideElement);
        } else if (slideContent.classList.contains('section-intro')) {
            this.exportSectionIntro(slide, slideElement);
        } else {
            this.exportContentSlide(slide, slideElement);
        }
        
        // Add SUNEE logo to every slide
        this.addSuneeLogo(slide);
    }
    
    exportCoverSlide(slide, slideElement) {
        const title = slideElement.querySelector('.cover-title')?.textContent || '';
        const subtitle = slideElement.querySelector('.cover-subtitle')?.textContent || '';
        const meta = slideElement.querySelector('.cover-meta')?.textContent || '';
        
        slide.addText(title, {
            x: 0.5,
            y: 1.5,
            w: 9,
            h: 1.5,
            fontSize: 60,
            fontFace: 'Georgia',
            color: 'FFFFFF',
            bold: false,
            valign: 'top'
        });
        
        slide.addText(subtitle, {
            x: 0.5,
            y: 3.2,
            w: 9,
            h: 0.6,
            fontSize: 24,
            color: 'D4D4D4',
            valign: 'top'
        });
        
        slide.addText(meta, {
            x: 0.5,
            y: 4.2,
            w: 9,
            h: 0.4,
            fontSize: 14,
            fontFace: 'Courier New',
            color: '737373',
            valign: 'top'
        });
    }
    
    exportSectionIntro(slide, slideElement) {
        const sectionNumber = slideElement.querySelector('.section-number')?.textContent || '';
        const sectionTitle = slideElement.querySelector('.section-title')?.textContent || '';
        
        slide.addText(sectionNumber, {
            x: 0.5,
            y: 1.2,
            w: 9,
            h: 0.4,
            fontSize: 16,
            fontFace: 'Courier New',
            color: '525252',
            valign: 'top'
        });
        
        slide.addText(sectionTitle, {
            x: 0.5,
            y: 1.8,
            w: 9,
            h: 2,
            fontSize: 72,
            fontFace: 'Georgia',
            color: 'FFFFFF',
            bold: false,
            valign: 'top'
        });
    }
    
    exportContentSlide(slide, slideElement) {
        const label = slideElement.querySelector('.slide-label')?.textContent || '';
        const title = slideElement.querySelector('.slide-title')?.textContent || '';
        
        // Add label
        if (label) {
            slide.addText(label, {
                x: 0.5,
                y: 0.4,
                w: 9,
                h: 0.3,
                fontSize: 11,
                color: '525252',
                bold: true,
                valign: 'top'
            });
        }
        
        // Add title
        if (title) {
            slide.addText(title, {
                x: 0.5,
                y: 0.8,
                w: 9,
                h: 1,
                fontSize: 32,
                fontFace: 'Georgia',
                color: 'FFFFFF',
                valign: 'top'
            });
        }
        
        // Try to find and export images (charts load from ../dark_mode_plots/)
        const images = slideElement.querySelectorAll('img[src*="dark_mode_plots"]');
        if (images.length > 0) {
            const imgY = 2.0;
            const imgW = 9;
            const imgH = 3;
            
            images.forEach((img, index) => {
                try {
                    slide.addImage({
                        path: img.src,
                        x: 0.5,
                        y: imgY + (index * 0.2),
                        w: imgW,
                        h: imgH,
                        sizing: { type: 'contain' }
                    });
                } catch (e) {
                    console.warn(`Could not add image ${img.src}:`, e);
                }
            });
        }
        
        // Add text content (simplified)
        const paragraphs = slideElement.querySelectorAll('.content-card p, .info-box p');
        let textY = 2.2;
        
        paragraphs.forEach((p, index) => {
            if (index < 3) { // Limit to first 3 paragraphs
                const text = p.textContent.trim();
                if (text.length > 0 && text.length < 200) {
                    slide.addText(text, {
                        x: 0.5,
                        y: textY,
                        w: 9,
                        h: 0.6,
                        fontSize: 14,
                        color: 'D4D4D4',
                        valign: 'top'
                    });
                    textY += 0.7;
                }
            }
        });
    }
    
    addSuneeLogo(slide) {
        // Add SUNEE text placeholder (since we can't reliably embed the logo image)
        slide.addText('SUNEE', {
            x: 0.3,
            y: 5.0,
            w: 1,
            h: 0.4,
            fontSize: 12,
            color: 'A3A3A3',
            bold: true,
            valign: 'bottom'
        });
    }
}

// ============================================
// INITIALIZE ON DOM LOAD
// ============================================

document.addEventListener('DOMContentLoaded', () => {
    console.log('Initializing presentation...');
    const presentation = new PresentationController();
    
    // Make it globally accessible for debugging
    window.presentation = presentation;
    
    console.log(`Loaded ${presentation.totalSlides} slides`);
});

// ============================================
// UTILITY FUNCTIONS
// ============================================

// Prevent default zoom behavior
document.addEventListener('wheel', (e) => {
    if (e.ctrlKey) {
        e.preventDefault();
    }
}, { passive: false });

// Handle browser back/forward
window.addEventListener('popstate', () => {
    // Optionally sync with URL hash for slide numbers
    const hash = window.location.hash.replace('#', '');
    const slideNum = parseInt(hash);
    if (slideNum && !isNaN(slideNum)) {
        window.presentation?.goToSlide(slideNum);
    }
});

// Performance optimization: lazy load images
if ('IntersectionObserver' in window) {
    const imageObserver = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                const img = entry.target;
                if (img.dataset.src) {
                    img.src = img.dataset.src;
                    img.removeAttribute('data-src');
                    imageObserver.unobserve(img);
                }
            }
        });
    });
    
    // Observe all images with data-src attribute
    document.querySelectorAll('img[data-src]').forEach(img => {
        imageObserver.observe(img);
    });
}

// Export for external use
if (typeof module !== 'undefined' && module.exports) {
    module.exports = PresentationController;
}
