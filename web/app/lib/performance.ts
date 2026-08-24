/**
 * Performance monitoring utilities
 * Last updated: deployment trigger
 */

export interface PerformanceMetrics {
  fcp: number | null;
  lcp: number | null;
  cls: number | null;
  ttfb: number | null;
  tti: number | null;
}

/**
 * Get Core Web Vitals
 */
export function getWebVitals(): PerformanceMetrics {
  const metrics: PerformanceMetrics = {
    fcp: null,
    lcp: null,
    cls: null,
    ttfb: null,
    tti: null
  };

  // First Contentful Paint
  const fcp = performance.getEntriesByName('first-contentful-paint')[0];
  if (fcp) metrics.fcp = Math.round(fcp.startTime);

  // Largest Contentful Paint
  if ('PerformanceObserver' in window) {
    try {
      const lcpObserver = new PerformanceObserver((list) => {
        const entries = list.getEntries();
        const lastEntry = entries[entries.length - 1];
        metrics.lcp = Math.round(lastEntry.renderTime || lastEntry.loadTime);
      });
      lcpObserver.observe({ entryTypes: ['largest-contentful-paint'] });
    } catch (e) {
      console.error('LCP observer failed:', e);
    }
  }

  // Cumulative Layout Shift
  if ('PerformanceObserver' in window) {
    try {
      const clsObserver = new PerformanceObserver((list) => {
        for (const entry of list.getEntries()) {
          if ((entry as any).hadRecentInput) continue;
          metrics.cls = Math.round((metrics.cls || 0) + (entry as any).value);
        }
      });
      clsObserver.observe({ entryTypes: ['layout-shift'] });
    } catch (e) {
      console.error('CLS observer failed:', e);
    }
  }

  // Time to First Byte
  const navigation = performance.getEntriesByType('navigation')[0] as PerformanceNavigationTiming;
  if (navigation) {
    metrics.ttfb = Math.round(navigation.responseStart - navigation.requestStart);
  }

  // Time to Interactive (approximation)
  const tti = performance.getEntriesByName('measure', 'measure').find(m => m.name.includes('tti'));
  if (tti) metrics.tti = Math.round(tti.duration);

  return metrics;
}

/**
 * Log performance metrics
 */
export function logPerformanceMetrics() {
  if (typeof window === 'undefined') return;

  window.addEventListener('load', () => {
    const metrics = getWebVitals();
    console.table(metrics);
    
    // Send to analytics if available
    if (window.gtag) {
      window.gtag('event', 'page_view', {
        'fcp_ms': metrics.fcp,
        'lcp_ms': metrics.lcp,
        'cls': metrics.cls,
        'ttfb_ms': metrics.ttfb
      });
    }
  });
}

/**
 * Measure function execution time
 */
export function measurePerformance(name: string, fn: () => void) {
  const start = performance.now();
  fn();
  const end = performance.now();
  const duration = end - start;
  
  if (duration > 1000) {
    console.warn(`⚠️  ${name} took ${duration.toFixed(2)}ms`);
  } else {
    console.log(`✓ ${name} took ${duration.toFixed(2)}ms`);
  }
}

/**
 * Check if device has slow network
 */
export function hasSlowNetwork(): boolean {
  if ('connection' in navigator) {
    const connection = (navigator as any).connection;
    const effectiveType = connection?.effectiveType;
    return effectiveType === '2g' || effectiveType === '3g' || connection?.saveData;
  }
  return false;
}

/**
 * Check if device has reduced battery
 */
export function hasBatteryOptimization(): boolean {
  if ('getBattery' in navigator) {
    return (navigator as any).getBattery()
      .then((battery: any) => battery.level < 0.2)
      .catch(() => false);
  }
  return false;
}

declare global {
  interface Window {
    gtag?: (event: string, name: string, params: any) => void;
  }
}
