// ═══════════════════════════════════════════════════════════════
// ENERGY CONSUMPTION PATTERN ANALYSIS — PRESENTATION CONTROLLER
// ═══════════════════════════════════════════════════════════════

const presentation = {
  currentSlide: 1,
  totalSlides: 20,
  
  init() {
    this.updateCounter();
    this.bindEvents();
    this.showSlide(1);
  },
  
  bindEvents() {
    document.getElementById('prev-btn').addEventListener('click', () => this.prevSlide());
    document.getElementById('next-btn').addEventListener('click', () => this.nextSlide());
    document.getElementById('export-btn').addEventListener('click', () => this.exportToPowerPoint());
    
    document.addEventListener('keydown', (e) => {
      if (e.key === 'ArrowLeft' || e.key === 'PageUp') {
        e.preventDefault();
        this.prevSlide();
      } else if (e.key === 'ArrowRight' || e.key === 'PageDown' || e.key === ' ') {
        e.preventDefault();
        this.nextSlide();
      } else if (e.key === 'Home') {
        e.preventDefault();
        this.goToSlide(1);
      } else if (e.key === 'End') {
        e.preventDefault();
        this.goToSlide(this.totalSlides);
      } else if (e.key === 'f' || e.key === 'F') {
        e.preventDefault();
        toggleFullscreen();
      } else if (e.key === 'p' || e.key === 'P') {
        e.preventDefault();
        togglePresentationMode();
      }
    });
  },
  
  showSlide(n) {
    const slides = document.querySelectorAll('.slide');
    slides.forEach(slide => slide.classList.remove('active'));
    
    if (n > 0 && n <= this.totalSlides) {
      slides[n - 1].classList.add('active');
      this.currentSlide = n;
      this.updateCounter();
    }
  },
  
  nextSlide() {
    if (this.currentSlide < this.totalSlides) {
      this.showSlide(this.currentSlide + 1);
    }
  },
  
  prevSlide() {
    if (this.currentSlide > 1) {
      this.showSlide(this.currentSlide - 1);
    }
  },
  
  goToSlide(n) {
    this.showSlide(n);
  },
  
  updateCounter() {
    document.getElementById('slide-counter').textContent = `${this.currentSlide} / ${this.totalSlides}`;
  },
  
  exportToPowerPoint() {
    if (typeof PptxGenJS === 'undefined') {
      alert('PowerPoint export library not loaded. Please check your internet connection.');
      return;
    }
    
    alert('PowerPoint export feature coming soon. For now, use browser print-to-PDF (Ctrl+P).');
  }
};

// Fullscreen toggle
function toggleFullscreen() {
  if (!document.fullscreenElement) {
    document.documentElement.requestFullscreen().catch(err => {
      console.error('Fullscreen error:', err);
    });
  } else {
    document.exitFullscreen();
  }
}

// Presentation mode (hide controls)
let presentationMode = false;
function togglePresentationMode() {
  presentationMode = !presentationMode;
  document.body.classList.toggle('presentation-mode', presentationMode);
  if (presentationMode && !document.fullscreenElement) {
    toggleFullscreen();
  }
}

// Initialize on load
document.addEventListener('DOMContentLoaded', () => {
  presentation.init();
  console.log('Presentation loaded: 20 slides');
});
