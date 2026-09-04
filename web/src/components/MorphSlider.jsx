import { useEffect, useRef, useState, useMemo } from "react";

/**
 * MorphSlider — WebGL image morphing slider.
 * Adapted from @react-bits/MorphSlider-JS-CSS for this project's theme.
 * Displays analysis result images with smooth transitions.
 */
export default function MorphSlider({
  items = [
    { image: "/results/load_shapes.png", caption: "Load Shapes" },
    { image: "/results/pca_variance.png", caption: "PCA Variance" },
    { image: "/results/k_selection.png", caption: "K-Selection" },
    { image: "/results/cluster_radar.png", caption: "Cluster Radar" },
    { image: "/results/validation_sweep.png", caption: "Validation" },
  ],
  transition = "melt",
  intensity = 0.55,
  aberration = 0.35,
  drift = 0.4,
  autoplay = false,
  overlayColor = "#05060a",
  duration = 1.1,
  ease = "power2.inOut",
  scale = 2.4,
  autoplayDelay = 4,
  loop = true,
  radius = 16,
  showCaptions = true,
  showControls = true,
  showIndicators = true,
  className = "",
}) {
  const containerRef = useRef(null);
  const canvasRef = useRef(null);
  const [currentIndex, setCurrentIndex] = useState(0);
  const [isTransitioning, setIsTransitioning] = useState(false);
  const [webglSupported, setWebglSupported] = useState(true);
  const [reducedMotion, setReducedMotion] = useState(false);
  const [imagesLoaded, setImagesLoaded] = useState({});

  // Refs for animation
  const animationRef = useRef(null);
  const progressRef = useRef(0);
  const startTimeRef = useRef(0);
  const targetIndexRef = useRef(0);
  const texturesRef = useRef([]);
  const autoplayTimerRef = useRef(null);

  // Transition types
  const TRANSITIONS = {
    melt: `
      float melt(vec2 uv, float progress) {
        float noise = fract(sin(dot(uv * 50.0 + progress * 10.0, vec2(12.9898, 78.233))) * 43758.5453);
        return step(progress + noise * 0.3, uv.y);
      }
    `,
    wave: `
      float wave(vec2 uv, float progress) {
        float wave = sin(uv.x * 20.0 + progress * 10.0) * 0.05;
        return step(progress + wave, uv.y);
      }
    `,
    slide: `
      float slide(vec2 uv, float progress) {
        return step(progress, uv.x);
      }
    `,
    zoom: `
      float zoom(vec2 uv, float progress) {
        vec2 center = vec2(0.5);
        float dist = distance(uv, center);
        return step(progress * 2.0, dist);
      }
    `,
    dissolve: `
      float dissolve(vec2 uv, float progress) {
        float noise = fract(sin(dot(uv * 100.0, vec2(12.9898, 78.233))) * 43758.5453);
        return step(progress, noise);
      }
    `,
  };

  useEffect(() => {
    // Check WebGL support
    const canvas = document.createElement("canvas");
    const gl = canvas.getContext("webgl") || canvas.getContext("experimental-webgl");
    setWebglSupported(!!gl);

    // Check reduced motion
    const mediaQuery = window.matchMedia("(prefers-reduced-motion: reduce)");
    setReducedMotion(mediaQuery.matches);
    const handler = (e) => setReducedMotion(e.matches);
    mediaQuery.addEventListener("change", handler);
    return () => mediaQuery.removeEventListener("change", handler);
  }, []);

  // Preload images
  useEffect(() => {
    const loadImage = (src) => new Promise((resolve) => {
      const img = new Image();
      img.crossOrigin = "anonymous";
      img.onload = () => resolve({ src, img, loaded: true });
      img.onerror = () => resolve({ src, img: null, loaded: false });
      img.src = src;
    });

    const loadAll = async () => {
      const results = await Promise.all(items.map((item) => loadImage(item.image)));
      const loaded = {};
      results.forEach((r) => { loaded[r.src] = r.loaded; });
      setImagesLoaded(loaded);
    };
    loadAll();
  }, [items]);

  if (!webglSupported || reducedMotion) {
    // Fallback: simple image carousel
    return (
      <div className={`morphslider-fallback ${className}`} style={{ position: "relative", width: "100%", height: "500px", overflow: "hidden", borderRadius: radius }}>
        {items.map((item, i) => (
          <div
            key={i}
            style={{
              position: "absolute",
              inset: 0,
              opacity: i === currentIndex ? 1 : 0,
              transition: "opacity 0.5s ease",
              display: "flex",
              alignItems: "center",
              justifyContent: "center",
              background: overlayColor,
            }}
          >
            <img src={item.image} alt={item.caption} style={{ maxWidth: "100%", maxHeight: "100%", objectFit: "contain", borderRadius: radius }} />
            {showCaptions && (
              <div style={{ position: "absolute", bottom: 20, left: 20, right: 20, color: "white", fontFamily: '"IBM Plex Mono", monospace', fontSize: "0.9rem", textAlign: "center", background: "rgba(0,0,0,0.6)", padding: 10, borderRadius: 8 }}>
                {item.caption}
              </div>
            )}
          </div>
        ))}
        {showControls && (
          <>
            <button onClick={() => goTo((currentIndex - 1 + items.length) % items.length)} style={{ position: "absolute", left: 20, top: "50%", transform: "translateY(-50%)", zIndex: 10, background: "rgba(255,255,255,0.2)", border: "none", color: "white", padding: "10px 15px", borderRadius: 50, cursor: "pointer" }}>‹</button>
            <button onClick={() => goTo((currentIndex + 1) % items.length)} style={{ position: "absolute", right: 20, top: "50%", transform: "translateY(-50%)", zIndex: 10, background: "rgba(255,255,255,0.2)", border: "none", color: "white", padding: "10px 15px", borderRadius: 50, cursor: "pointer" }}>›</button>
          </>
        )}
      </div>
    );
  }

  // Initialize WebGL
  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;

    import("ogl").then(({ Renderer, Program, Mesh, Geometry, Texture, Vec2 }) => {
      const dpr = Math.min(window.devicePixelRatio || 1, 2);
      const renderer = new Renderer({
        canvas,
        dpr,
        alpha: true,
        premultipliedAlpha: true,
      });

      const gl = renderer.gl;
      gl.enable(gl.BLEND);
      gl.blendFunc(gl.SRC_ALPHA, gl.ONE_MINUS_SRC_ALPHA);

      // Load textures
      const loadTexture = (src) => new Promise((resolve) => {
        const img = new Image();
        img.crossOrigin = "anonymous";
        img.onload = () => {
          const texture = new Texture(gl, { generateMipmaps: false });
          texture.image = img;
          texture.needsUpdate = true;
          resolve(texture);
        };
        img.onerror = () => resolve(null);
        img.src = src;
      });

      const loadTextures = async () => {
        const texs = await Promise.all(items.map((item) => loadTexture(item.image)));
        texturesRef.current = texs.filter(Boolean);
      };
      loadTextures();

      // Shaders
      const vertex = `
        attribute vec2 position;
        attribute vec2 uv;
        varying vec2 vUv;
        void main() {
          vUv = uv;
          gl_Position = vec4(position, 0.0, 1.0);
        }
      `;

      const fragment = `
        precision highp float;
        uniform sampler2D uTexture1;
        uniform sampler2D uTexture2;
        uniform float uProgress;
        uniform float uIntensity;
        uniform float uAberration;
        uniform float uDrift;
        uniform vec2 uResolution;
        uniform float uTime;
        varying vec2 vUv;

        ${TRANSITIONS[transition] || TRANSITIONS.melt}

        // Aberration
        vec3 sampleAberration(sampler2D tex, vec2 uv, float progress, float aberration) {
          float offset = aberration * progress * (1.0 - progress) * 0.02;
          float r = texture2D(tex, uv + vec2(offset, 0.0)).r;
          float g = texture2D(tex, uv).g;
          float b = texture2D(tex, uv - vec2(offset, 0.0)).b;
          return vec3(r, g, b);
        }

        // Drift
        vec2 applyDrift(vec2 uv, float progress, float drift) {
          float d = drift * sin(progress * 3.14159) * 0.02;
          return uv + vec2(d * sin(uv.y * 20.0), d * cos(uv.x * 20.0));
        }

        void main() {
          float progress = uProgress;

          // Apply transition mask
          float mask = ${transition}(vUv, progress);

          // Current and next texture coordinates
          vec2 uv1 = applyDrift(vUv, progress, uDrift);
          vec2 uv2 = applyDrift(vUv, progress, uDrift);

          // Sample with aberration
          vec3 color1 = sampleAberration(uTexture1, uv1, progress, uAberration);
          vec3 color2 = sampleAberration(uTexture2, uv2, progress, uAberration);

          // Mix based on transition
          vec3 color = mix(color1, color2, mask * uIntensity);

          // Overlay
          vec3 overlay = vec3(0.01, 0.02, 0.04);
          color = mix(color, overlay, 1.0 - mask) * mask + color * (1.0 - mask);

          gl_FragColor = vec4(color, 1.0);
        }
      `;

      const program = new Program(gl, {
        vertex,
        fragment,
        uniforms: {
          uTexture1: { value: null },
          uTexture2: { value: null },
          uProgress: { value: 0 },
          uIntensity: { value: intensity },
          uAberration: { value: aberration },
          uDrift: { value: drift },
          uResolution: { value: new Vec2() },
          uTime: { value: 0 },
        },
        transparent: true,
      });

      // Fullscreen quad
      const geometry = new Geometry(gl, {
        position: { size: 2, data: new Float32Array([-1, -1, 3, -1, -1, 3]) },
        uv: { size: 2, data: new Float32Array([0, 0, 2, 0, 0, 2]) },
      });
      const mesh = new Mesh(gl, { geometry, program });

      let width = 0;
      let height = 0;

      const resize = () => {
        const container = containerRef.current;
        if (!container) return;
        const rect = container.getBoundingClientRect();
        width = rect.width;
        height = rect.height;
        renderer.setSize(width, height);
        program.uniforms.uResolution.value.set(width, height);
      };

      let lastTime = performance.now();
      const render = (time) => {
        const dt = (time - lastTime) / 1000;
        lastTime = time;

        program.uniforms.uTime.value = time / 1000;

        if (isTransitioning) {
          const elapsed = (time - startTimeRef.current) / 1000;
          const progress = Math.min(elapsed / duration, 1);

          // Easing
          let eased = progress;
          if (ease === "power2.inOut") {
            eased = progress < 0.5
              ? 2 * progress * progress
              : 1 - Math.pow(-2 * progress + 2, 2) / 2;
          } else if (ease === "power3.inOut") {
            eased = progress < 0.5
              ? 4 * progress * progress * progress
              : 1 - Math.pow(-2 * progress + 2, 3) / 2;
          }

          program.uniforms.uProgress.value = eased;

          if (progress >= 1) {
            setIsTransitioning(false);
            setCurrentIndex(targetIndexRef.current);
            progressRef.current = 0;
          }
        }

        renderer.render({ scene: mesh });
        animationRef.current = requestAnimationFrame(render);
      };

      // Go to specific index
      const goTo = (index) => {
        if (isTransitioning || index === currentIndex) return;
        if (index < 0 || index >= items.length) return;

        const texs = texturesRef.current;
        if (texs.length < 2) return;

        program.uniforms.uTexture1.value = texs[currentIndex % texs.length];
        program.uniforms.uTexture2.value = texs[index % texs.length];

        targetIndexRef.current = index;
        startTimeRef.current = performance.now();
        setIsTransitioning(true);
      };

      const goNext = () => goTo((currentIndex + 1) % items.length);
      const goPrev = () => goTo((currentIndex - 1 + items.length) % items.length);

      // Autoplay
      const startAutoplay = () => {
        if (autoplayTimerRef.current) clearInterval(autoplayTimerRef.current);
        if (autoplay && items.length > 1) {
          autoplayTimerRef.current = setInterval(() => {
            goNext();
          }, (autoplayDelay + duration) * 1000);
        }
      };

      const stopAutoplay = () => {
        if (autoplayTimerRef.current) clearInterval(autoplayTimerRef.current);
      };

      // Setup
      resize();
      program.uniforms.uTexture1.value = texturesRef.current[0] || null;
      program.uniforms.uTexture2.value = texturesRef.current[1] || null;
      requestAnimationFrame(render);

      const container = containerRef.current;
      if (container) {
        container.addEventListener("mouseenter", stopAutoplay);
        container.addEventListener("mouseleave", startAutoplay);
      }

      const ro = new ResizeObserver(resize);
      ro.observe(container);

      // Expose controls
      window.__morphSliderControls = { goTo, goNext, goPrev, resize };

      return () => {
        if (animationRef.current) cancelAnimationFrame(animationRef.current);
        stopAutoplay();
        if (container) {
          container.removeEventListener("mouseenter", stopAutoplay);
          container.removeEventListener("mouseleave", startAutoplay);
        }
        ro.disconnect();
        renderer.dispose();
        program.remove();
        geometry.remove();
        mesh.remove();
        texturesRef.current.forEach(t => t && t.dispose && t.dispose());
        delete window.__morphSliderControls;
      };
    }).catch(() => {
      // ogl not available
    });
  }, [webglSupported, reducedMotion, items, transition, intensity, aberration, drift, duration, ease, currentIndex, isTransitioning, autoplay, autoplayDelay]);

  const goTo = (index) => {
    if (window.__morphSliderControls) {
      window.__morphSliderControls.goTo(index);
    }
  };

  const goNext = () => {
    if (window.__morphSliderControls) {
      window.__morphSliderControls.goNext();
    }
  };

  const goPrev = () => {
    if (window.__morphSliderControls) {
      window.__morphSliderControls.goPrev();
    }
  };

  return (
    <div
      ref={containerRef}
      className={`morphslider ${className}`}
      style={{
        position: "relative",
        width: "100%",
        height: "500px",
        overflow: "hidden",
        borderRadius: radius,
        background: overlayColor,
      }}
    >
      <canvas
        ref={canvasRef}
        style={{
          position: "absolute",
          inset: 0,
          width: "100%",
          height: "100%",
          pointerEvents: "none",
          zIndex: 1,
        }}
      />

      {showCaptions && (
        <div
          style={{
            position: "absolute",
            bottom: 24,
            left: 24,
            right: 24,
            zIndex: 5,
            display: "flex",
            alignItems: "center",
            justifyContent: "space-between",
            pointerEvents: "none",
          }}
        >
          <div style={{
            color: "#dbe7ec",
            fontFamily: '"IBM Plex Mono", ui-monospace, monospace',
            fontSize: "0.75rem",
            fontWeight: 600,
            letterSpacing: "0.12em",
            textTransform: "uppercase",
            background: "rgba(7, 11, 16, 0.8)",
            padding: "8px 16px",
            borderRadius: 9999,
            border: "1px solid rgba(72, 215, 194, 0.3)",
            backdropFilter: "blur(8px)",
          }}>
            {items[currentIndex]?.caption || `Slide ${currentIndex + 1}`}
          </div>

          {showIndicators && (
            <div style={{ display: "flex", gap: 8 }}>
              {items.map((_, i) => (
                <button
                  key={i}
                  onClick={() => goTo(i)}
                  style={{
                    width: 10,
                    height: 10,
                    borderRadius: 50,
                    border: "none",
                    background: i === currentIndex ? "var(--cyan)" : "rgba(148, 168, 180, 0.4)",
                    cursor: "pointer",
                    transition: "background 0.3s ease, transform 0.3s ease",
                    transform: i === currentIndex ? "scale(1.2)" : "scale(1)",
                  }}
                  aria-label={`Go to slide ${i + 1}`}
                  aria-current={i === currentIndex ? "true" : undefined}
                />
              ))}
            </div>
          )}
        </div>
      )}

      {showControls && (
        <>
          <button
            onClick={goPrev}
            style={{
              position: "absolute",
              left: 20,
              top: "50%",
              transform: "translateY(-50%)",
              zIndex: 10,
              width: 48,
              height: 48,
              borderRadius: 50,
              border: "1px solid rgba(72, 215, 194, 0.3)",
              background: "rgba(7, 11, 16, 0.8)",
              color: "var(--cyan)",
              cursor: "pointer",
              display: "flex",
              alignItems: "center",
              justifyContent: "center",
              fontSize: "1.5rem",
              backdropFilter: "blur(8px)",
              transition: "all 0.2s ease",
            }}
            onMouseOver={(e) => e.target.style.background = "rgba(72, 215, 194, 0.2)"}
            onMouseOut={(e) => e.target.style.background = "rgba(7, 11, 16, 0.8)"}
            aria-label="Previous slide"
          >
            ‹
          </button>
          <button
            onClick={goNext}
            style={{
              position: "absolute",
              right: 20,
              top: "50%",
              transform: "translateY(-50%)",
              zIndex: 10,
              width: 48,
              height: 48,
              borderRadius: 50,
              border: "1px solid rgba(72, 215, 194, 0.3)",
              background: "rgba(7, 11, 16, 0.8)",
              color: "var(--cyan)",
              cursor: "pointer",
              display: "flex",
              alignItems: "center",
              justifyContent: "center",
              fontSize: "1.5rem",
              backdropFilter: "blur(8px)",
              transition: "all 0.2s ease",
            }}
            onMouseOver={(e) => e.target.style.background = "rgba(72, 215, 194, 0.2)"}
            onMouseOut={(e) => e.target.style.background = "rgba(7, 11, 16, 0.8)"}
            aria-label="Next slide"
          >
            ›
          </button>
        </>
      )}
    </div>
  );
}