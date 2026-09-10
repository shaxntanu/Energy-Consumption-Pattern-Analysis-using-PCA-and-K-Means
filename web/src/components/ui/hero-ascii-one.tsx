import { useEffect, useState } from 'react';
import './hero-ascii-one.css';

const PROJECT_ID = 'OMzqyUv6M3kSnv0JeAtC';
const SCRIPT_URL = 'https://cdn.jsdelivr.net/gh/hiunicornstudio/unicornstudio.js@v1.4.33/dist/unicornStudio.umd.js';
const SCRIPT_ID = 'load-shape-unicorn-runtime';
const METER_HEIGHTS = [4, 10, 7, 15, 9, 12, 5, 11];
type Scene = { destroy?: () => void };
type Runtime = { init: () => Promise<Scene[]> };
type Status = 'static' | 'loading' | 'ready' | 'unavailable';

const getRuntime = () => (window as Window & { UnicornStudio?: Runtime }).UnicornStudio;
let runtimePromise: Promise<Runtime> | undefined;
// Serialize initialization so StrictMode/remounts cannot initialize the same
// DOM scene concurrently. Each effect destroys only the scenes it receives.
let sceneQueue: Promise<void> = Promise.resolve();

function loadRuntime(): Promise<Runtime> {
  const existing = getRuntime();
  if (existing?.init) return Promise.resolve(existing);
  if (runtimePromise) return runtimePromise;
  runtimePromise = new Promise<Runtime>((resolve, reject) => {
    const script = document.createElement('script');
    script.id = SCRIPT_ID;
    script.src = SCRIPT_URL;
    script.async = true;
    const finish = (error?: Error) => {
      window.clearTimeout(timeout);
      script.onload = null;
      script.onerror = null;
      const runtime = getRuntime();
      if (error || !runtime?.init) {
        script.remove();
        reject(error || new Error('Animation runtime did not initialize'));
      } else resolve(runtime);
    };
    const timeout = window.setTimeout(() => finish(new Error('Animation script timed out')), 12000);
    script.onload = () => finish();
    script.onerror = () => finish(new Error('Animation script could not load'));
    document.head.appendChild(script);
  }).catch((error) => {
    runtimePromise = undefined;
    throw error;
  });
  return runtimePromise;
}

function destroyScenes(scenes: Scene[]) {
  for (const scene of scenes) {
    try { scene.destroy?.(); } catch { /* A failed visual cleanup must not affect navigation. */ }
  }
}

export default function HeroAsciiOne() {
  const [eligible, setEligible] = useState(false);
  const [paused, setPaused] = useState(false);
  const [status, setStatus] = useState<Status>('static');
  const active = eligible && !paused;

  useEffect(() => {
    const desktop = window.matchMedia('(min-width: 1024px)');
    const reduced = window.matchMedia('(prefers-reduced-motion: reduce)');
    const update = () => setEligible(desktop.matches && !reduced.matches && !document.hidden);
    update();
    desktop.addEventListener('change', update);
    reduced.addEventListener('change', update);
    document.addEventListener('visibilitychange', update);
    return () => {
      desktop.removeEventListener('change', update);
      reduced.removeEventListener('change', update);
      document.removeEventListener('visibilitychange', update);
    };
  }, []);

  useEffect(() => {
    if (!active) {
      setStatus('static');
      return;
    }
    let cancelled = false;
    let timedOut = false;
    let owned: Scene[] = [];
    setStatus('loading');
    const timeout = window.setTimeout(() => {
      timedOut = true;
      if (!cancelled) setStatus('unavailable');
    }, 20000);
    sceneQueue = sceneQueue.catch(() => {}).then(async () => {
      try {
        if (cancelled || timedOut) return;
        const runtime = await loadRuntime();
        if (cancelled || timedOut) return;
        const scenes = await runtime.init();
        if (!Array.isArray(scenes) || scenes.length === 0) throw new Error('No animation scene returned');
        if (cancelled || timedOut) destroyScenes(scenes);
        else {
          owned = scenes;
          setStatus('ready');
        }
      } catch {
        if (!cancelled) setStatus('unavailable');
      } finally {
        window.clearTimeout(timeout);
      }
    });
    return () => {
      cancelled = true;
      window.clearTimeout(timeout);
      destroyScenes(owned);
    };
  }, [active]);

  const statusLabel = {
    static: 'STATIC.VIEW', loading: 'SCENE.LOADING', ready: 'SCENE.READY', unavailable: 'STATIC.FALLBACK',
  }[status];

  return (
    <header className="ascii-hero" id="top" aria-labelledby="ascii-hero-title">
      <div className="ascii-hero__stars" aria-hidden="true" />
      {/* Decorative only: the external animation is never evidence of ML results. */}
      <div className="ascii-hero__visual" aria-hidden="true" inert>
        <div
          className={`ascii-hero__scene${status === 'ready' ? ' is-ready' : ''}`}
          data-us-project={active ? PROJECT_ID : undefined}
        />
      </div>
      <div className="ascii-hero__corners" aria-hidden="true"><i /><i /><i /><i /></div>
      <div className="ascii-hero__topline">
        <span>LOAD SHAPE LAB</span>
        <span>PCA / K-MEANS</span>
      </div>
      <div className="ascii-hero__content">
        <div className="ascii-hero__copy">
          <div className="ascii-hero__rule" aria-hidden="true"><span />∞<span /></div>
          <p className="ascii-hero__eyebrow">When energy is used matters.</p>
          <h1 id="ascii-hero-title">Energy use is a pattern, not just a number.</h1>
          <div className="ascii-hero__dots" aria-hidden="true" />
          <p className="ascii-hero__description">
            A synthetic year of household electricity readings. Behavioural features,
            PCA and K-Means reveal daily rhythms—then we check their stability across
            seasons and time. A controlled study, not a claim about real households.
          </p>
          <div className="ascii-hero__actions">
            <a href="#charts">Explore the charts<span aria-hidden="true"> ↗</span></a>
            <a href="#about">Understand the method</a>
          </div>
          <div className="ascii-hero__notation" aria-hidden="true"><span>∞</span><span />SHAPE.NOT.SCALE</div>
        </div>
      </div>
      <div className="ascii-hero__footer">
        <div className="ascii-hero__footer-group">
          <span>SYNTHETIC.STUDY</span>
          <div className="ascii-hero__meters" aria-hidden="true">
            {METER_HEIGHTS.map((height, index) => <i key={index} style={{ height }} />)}
          </div>
        </div>
        <div className="ascii-hero__footer-group">
          <span role="status" aria-live="polite">{statusLabel}</span>
          {eligible && <button type="button" aria-pressed={paused} onClick={() => setPaused((value) => !value)}>
            {paused ? 'Resume visual' : 'Pause visual'}
          </button>}
          <a href="https://www.unicorn.studio/" target="_blank" rel="noopener noreferrer">Visual: Unicorn Studio<span className="ascii-hero__sr-only"> (opens in a new tab)</span></a>
        </div>
      </div>
    </header>
  );
}
