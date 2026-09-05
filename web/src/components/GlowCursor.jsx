import { useEffect, useRef, useState } from "react";

/**
 * GlowCursor — WebGL cursor trail using ogl.
 * Adapted from @react-bits/GlowCursor-JS-CSS for this project's theme.
 * Wraps hero or app main content for trail effect.
 */
export default function GlowCursor({
  children,
  color = "#48d7c2",
  secondaryColor = "#b78cff",
  trailLength = 40,
  trailWidth = 8,
  trailTaper = 0.8,
  followSpeed = 0.16,
  glowIntensity = 1.9,
  glowSpread = 1.2,
  hotspot = 0.65,
  brightness = 1.25,
  opacity = 1,
  pulseSpeed = 1.1,
  noiseStrength = 0.035,
  idleFade = true,
  idleTimeout = 700,
  fadeDuration = 900,
  blendMode = "screen",
  className = "",
}) {
  const containerRef = useRef(null);
  const canvasRef = useRef(null);
  const propsRef = useRef({});
  const [webglSupported, setWebglSupported] = useState(true);
  const [reducedMotion, setReducedMotion] = useState(false);

  // Update props ref
  propsRef.current = {
    color,
    secondaryColor,
    trailLength,
    trailWidth,
    trailTaper,
    followSpeed,
    glowIntensity,
    glowSpread,
    hotspot,
    brightness,
    opacity,
    pulseSpeed,
    noiseStrength,
    idleFade,
    idleTimeout,
    fadeDuration,
    blendMode,
  };

  // Hex to RGB
  const hexToRgb = (hex) => {
    const h = hex.replace("#", "");
    const bigint = parseInt(h.length === 3 ? h.split("").map((c) => c + c).join("") : h, 16);
    return { r: (bigint >> 16) & 255, g: (bigint >> 8) & 255, b: bigint & 255 };
  };

  useEffect(() => {
    // Check for WebGL support
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

  // Skip rendering if no WebGL or reduced motion
  if (!webglSupported || reducedMotion) {
    return <div ref={containerRef} className={className}>{children}</div>;
  }

  useEffect(() => {
    const container = containerRef.current;
    const canvas = canvasRef.current;
    if (!container || !canvas) return;

    // Dynamic import ogl
    import("ogl").then(({ Renderer, Program, Mesh, Geometry, Vec2, Vec3 }) => {
      const dpr = Math.min(window.devicePixelRatio || 1, 2);
      const renderer = new Renderer({
        canvas,
        dpr,
        alpha: true,
        premultipliedAlpha: true,
      });

      const gl = renderer.gl;
      gl.enable(gl.BLEND);

      const MAX_POINTS = 200;
      const pointData = new Float32Array(MAX_POINTS * 2);
      const points = [];

      // Shaders
      const VERTEX_SHADER = `
        attribute vec2 position;
        attribute vec2 point;
        uniform vec2 uResolution;
        varying vec2 vPoint;
        varying vec2 vUv;
        void main() {
          vPoint = point;
          vUv = position;
          vec2 clipSpace = (position / uResolution) * 2.0 - 1.0;
          gl_Position = vec4(clipSpace * vec2(1, -1), 0, 1);
          gl_PointSize = 1.0;
        }
      `;

      const FRAGMENT_SHADER = `
        precision highp float;
        uniform vec2 uResolution;
        uniform vec2 uPoints[${MAX_POINTS}];
        uniform int uPointCount;
        uniform vec3 uColor;
        uniform vec3 uSecondaryColor;
        uniform float uTrailWidth;
        uniform float uTaper;
        uniform float uGlowIntensity;
        uniform float uGlowSpread;
        uniform float uHotspot;
        uniform float uBrightness;
        uniform float uOpacity;
        uniform float uPulseSpeed;
        uniform float uNoiseStrength;
        uniform bool uNormalBlend;
        uniform float uTime;
        uniform float uFade;
        varying vec2 vPoint;
        varying vec2 vUv;

        // Hash functions
        float hash11(float p) { return fract(sin(p * 0.1031) * 1031.0); }
        vec2 hash21(float p) { return fract(sin(vec2(p, p * 1.7) * 103.1) * 1031.0); }

        // Film grain
        float filmGrain(vec2 uv, float time) {
          vec2 n = uv * 200.0 + time * 0.1;
          return fract(sin(dot(n, vec2(12.9898, 78.233))) * 43758.5453);
        }

        // sRGB encoding
        vec3 srgb(vec3 c) { return pow(c, vec3(1.0 / 2.2)); }

        void main() {
          float fade = uFade;
          if (fade <= 0.0) discard;

          vec2 center = vPoint;
          float maxDist = 0.0;
          vec3 color = vec3(0.0);

          for (int i = 0; i < ${MAX_POINTS}; i++) {
            if (i >= uPointCount) break;
            vec2 p = uPoints[i];
            float dist = distance(vUv, p);

            // Trail taper
            float t = float(i) / float(uPointCount - 1);
            float width = uTrailWidth * mix(1.0, uTaper, t);

            // Glow falloff
            float glow = smoothstep(width, 0.0, dist);
            glow = pow(glow, uGlowSpread);

            // Color interpolation
            vec3 c = mix(uColor, uSecondaryColor, t);

            // Hotspot at cursor
            if (i == uPointCount - 1) {
              glow *= uHotspot;
            }

            color += c * glow;
            maxDist = max(maxDist, glow);
          }

          // Pulse
          float pulse = 1.0 + sin(uTime * uPulseSpeed) * 0.15;

          // Noise
          float noise = filmGrain(vUv, uTime) * uNoiseStrength;

          color *= uBrightness * pulse * (1.0 + noise);
          color *= fade * uOpacity;

          // Gamma correct
          color = srgb(color);

          if (uNormalBlend) {
            gl_FragColor = vec4(color, fade * uOpacity);
          } else {
            // Additive/screen blend
            gl_FragColor = vec4(color, 1.0);
          }
        }
      `;

      const program = new Program(gl, {
        vertex: VERTEX_SHADER,
        fragment: FRAGMENT_SHADER,
        uniforms: {
          uResolution: { value: new Vec2() },
          uPoints: { value: pointData },
          uPointCount: { value: 0 },
          uColor: { value: new Vec3(...Object.values(hexToRgb(propsRef.current.color))) },
          uSecondaryColor: { value: new Vec3(...Object.values(hexToRgb(propsRef.current.secondaryColor))) },
          uTrailWidth: { value: propsRef.current.trailWidth },
          uTaper: { value: propsRef.current.trailTaper },
          uGlowIntensity: { value: propsRef.current.glowIntensity },
          uGlowSpread: { value: propsRef.current.glowSpread },
          uHotspot: { value: propsRef.current.hotspot },
          uBrightness: { value: propsRef.current.brightness },
          uOpacity: { value: propsRef.current.opacity },
          uPulseSpeed: { value: propsRef.current.pulseSpeed },
          uNoiseStrength: { value: propsRef.current.noiseStrength },
          uNormalBlend: { value: propsRef.current.blendMode === "normal" },
          uTime: { value: 0 },
          uFade: { value: 1 },
        },
        transparent: true,
        depthTest: false,
      });

      // Fullscreen triangle
      const geometry = new Geometry(gl, {
        position: { size: 2, data: new Float32Array([-1, -1, 3, -1, -1, 3]) },
        point: { size: 2, data: new Float32Array([0, 0, 1, 0, 0, 1]) },
      });
      const mesh = new Mesh(gl, { geometry, program });

      let width = 0;
      let height = 0;
      let initialized = false;
      let pointerInside = false;
      let fade = 1;
      let lastPointerTime = performance.now();

      const resize = () => {
        const container = containerRef.current;
        if (!container) return;
        const rect = container.getBoundingClientRect();
        width = rect.width;
        height = rect.height;
        renderer.setSize(width, height);
        program.uniforms.uResolution.value.set(width, height);
      };

      const initializeTrail = () => {
        if (initialized) return;
        const centerX = width / 2;
        const centerY = height / 2;
        for (let i = 0; i < MAX_POINTS; i++) {
          points[i] = { x: centerX, y: centerY };
        }
        initialized = true;
      };

      const updatePointer = (x, y) => {
        if (!initialized) initializeTrail();
        pointerInside = true;
        lastPointerTime = performance.now();

        // Shift points
        for (let i = 0; i < MAX_POINTS - 1; i++) {
          points[i].x = points[i + 1].x;
          points[i].y = points[i + 1].y;
        }
        points[MAX_POINTS - 1] = { x, y };
      };

      const onPointerMove = (e) => {
        const container = containerRef.current;
        if (!container) return;
        const rect = container.getBoundingClientRect();
        const x = clamp(e.clientX - rect.left, 0, width);
        const y = clamp(height - (e.clientY - rect.top), 0, height);
        updatePointer(x, y);
      };

      const onPointerEnter = () => {
        pointerInside = true;
      };

      const onPointerLeave = () => {
        pointerInside = false;
      };

      const clamp = (v, min, max) => Math.max(min, Math.min(max, v));

      let lastTime = performance.now();
      const render = (time) => {
        const dt = (time - lastTime) / 1000;
        lastTime = time;

        const props = propsRef.current;

        // Update uniforms
        program.uniforms.uTime.value = time / 1000;
        program.uniforms.uTrailWidth.value = props.trailWidth;
        program.uniforms.uTaper.value = props.trailTaper;
        program.uniforms.uGlowIntensity.value = props.glowIntensity;
        program.uniforms.uGlowSpread.value = props.glowSpread;
        program.uniforms.uHotspot.value = props.hotspot;
        program.uniforms.uBrightness.value = props.brightness;
        program.uniforms.uOpacity.value = props.opacity;
        program.uniforms.uPulseSpeed.value = props.pulseSpeed;
        program.uniforms.uNoiseStrength.value = props.noiseStrength;
        program.uniforms.uNormalBlend.value = props.blendMode === "normal";

        // Idle fade
        if (props.idleFade) {
          const idleTime = time - lastPointerTime;
          if (idleTime > props.idleTimeout) {
            const fadeProgress = (idleTime - props.idleTimeout) / props.fadeDuration;
            fade = Math.max(0, 1 - clamp(fadeProgress, 0, 1));
          } else {
            fade = 1;
          }
        }
        program.uniforms.uFade.value = fade;

        // Update point data
        const pointCount = Math.min(props.trailLength, MAX_POINTS);
        program.uniforms.uPointCount.value = pointCount;
        for (let i = 0; i < pointCount; i++) {
          const idx = i * 2;
          pointData[idx] = points[i].x;
          pointData[idx + 1] = points[i].y;
        }

        // Easing for trail head
        if (pointCount > 1) {
          const headEase = 0.2;
          const chainEase = 0.12;
          // Could add more sophisticated easing here
        }

        renderer.render({ scene: mesh });
        requestAnimationFrame(render);
      };

      const cleanup = () => {
        renderer.dispose();
        program.remove();
        geometry.remove();
        mesh.remove();
      };

      // Setup
      resize();
      initializeTrail();
      requestAnimationFrame(render);

      const container = containerRef.current;
      if (container) {
        container.addEventListener("pointermove", onPointerMove);
        container.addEventListener("pointerenter", onPointerEnter);
        container.addEventListener("pointerleave", onPointerLeave);
      }

      const ro = new ResizeObserver(resize);
      ro.observe(container);

      return () => {
        cleanup();
        if (container) {
          container.removeEventListener("pointermove", onPointerMove);
          container.removeEventListener("pointerenter", onPointerEnter);
          container.removeEventListener("pointerleave", onPointerLeave);
        }
        ro.disconnect();
      };
    }).catch(() => {
      // ogl not available, skip
    });
  }, [webglSupported, reducedMotion]);

  return (
    <div
      ref={containerRef}
      className={`glow-cursor ${className}`}
      style={{
        position: "relative",
        width: "100%",
        height: "100%",
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
          zIndex: 10,
        }}
      />
      <div style={{ position: "relative", zIndex: 1 }}>{children}</div>
    </div>
  );
}