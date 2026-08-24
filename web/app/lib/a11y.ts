/**
 * Accessibility utilities and helpers
 */

/**
 * Announces a message to screen readers
 */
export function announceToScreenReader(message: string, priority: 'polite' | 'assertive' = 'polite') {
  const ariaLive = document.getElementById('aria-live') || createAriaLive();
  
  if (priority === 'assertive') {
    ariaLive.setAttribute('aria-live', 'assertive');
  } else {
    ariaLive.setAttribute('aria-live', 'polite');
  }
  
  ariaLive.textContent = message;
}

/**
 * Create aria-live region for announcements
 */
function createAriaLive() {
  const div = document.createElement('div');
  div.id = 'aria-live';
  div.className = 'sr-only';
  div.setAttribute('aria-live', 'polite');
  div.setAttribute('aria-atomic', 'true');
  document.body.appendChild(div);
  return div;
}

/**
 * Check if user prefers reduced motion
 */
export function prefersReducedMotion(): boolean {
  return window.matchMedia('(prefers-reduced-motion: reduce)').matches;
}

/**
 * Check if user prefers dark mode
 */
export function prefersDarkMode(): boolean {
  return window.matchMedia('(prefers-color-scheme: dark)').matches;
}

/**
 * Get accessible color contrast
 */
export function getContrastRatio(rgb1: string, rgb2: string): number {
  const getLuminance = (rgb: string) => {
    const [r, g, b] = rgb.match(/\d+/g)!.map(x => parseInt(x) / 255);
    const [rs, gs, bs] = [r, g, b].map(c =>
      c <= 0.03928 ? c / 12.92 : Math.pow((c + 0.055) / 1.055, 2.4)
    );
    return 0.2126 * rs + 0.7152 * gs + 0.0722 * bs;
  };
  
  const l1 = getLuminance(rgb1);
  const l2 = getLuminance(rgb2);
  const lighter = Math.max(l1, l2);
  const darker = Math.min(l1, l2);
  
  return (lighter + 0.05) / (darker + 0.05);
}

/**
 * Skip to main content functionality
 */
export function setupSkipLink() {
  const skipLink = document.createElement('a');
  skipLink.href = '#main-content';
  skipLink.className = 'sr-only focus:not-sr-only';
  skipLink.textContent = 'Skip to main content';
  
  skipLink.style.cssText = `
    position: absolute;
    top: 0;
    left: 0;
    z-index: 9999;
    padding: 1rem;
    background: #3BC9DE;
    color: #0B0E14;
    font-weight: bold;
  `;
  
  document.body.prepend(skipLink);
}

/**
 * Make interactive elements keyboard navigable
 */
export function makeKeyboardAccessible(element: HTMLElement, callback: () => void) {
  element.addEventListener('keydown', (e) => {
    if (e.key === 'Enter' || e.key === ' ') {
      e.preventDefault();
      callback();
    }
  });
}

/**
 * Set up focus management for modals
 */
export function trapFocus(element: HTMLElement) {
  const focusableElements = element.querySelectorAll(
    'button, [href], input, select, textarea, [tabindex]:not([tabindex="-1"])'
  );
  
  const firstElement = focusableElements[0] as HTMLElement;
  const lastElement = focusableElements[focusableElements.length - 1] as HTMLElement;
  
  element.addEventListener('keydown', (e) => {
    if (e.key === 'Tab') {
      if (e.shiftKey && document.activeElement === firstElement) {
        e.preventDefault();
        lastElement.focus();
      } else if (!e.shiftKey && document.activeElement === lastElement) {
        e.preventDefault();
        firstElement.focus();
      }
    }
  });
}
