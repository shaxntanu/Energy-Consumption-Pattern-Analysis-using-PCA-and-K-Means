# AI Integration Instructions — Prompt UI Enhancements

This document contains exact code snippets and usage instructions for adding the listed UI components to the project.

Sections:
- ParticleText (replace main heading)
- GlowCursor (custom cursor)
- LogoLoop (technology scroller)
- DriftWall (graph gallery)
- MorphSlider (graph animation slider beside title)

---

## 1) ParticleText — Replace main heading

Install the component (exact command):

```
npx shadcn@latest add @react-bits/ParticleText-TS-TW
```

Import and usage (exact code):

```jsx
import ParticleText from './ParticleText';

<div style={{ width: '100%', height: 360, background: '#09090f' }}>
 <ParticleText
 text="Future Interfaces"
 particleSize={2.2}
 density={4}
 color="#f8fafc"
 highlightColor="#8b5cf6"
 scatter={190}
 gatherDuration={1600}
 stagger={420}
 pointerRepel={42}
 repelRadius={120}
 idleDrift={0.8}
 trigger="mount"
 fontSize="clamp(3.5rem, 13vw, 9rem)"
 fontWeight={800}
 fontFamily="inherit"
 glow
 />
</div>
```

Instruction: Replace the project's main heading that currently reads:

```
Energy use is a pattern, not just a number.
```

with the ParticleText component above. Place it in the header or hero section where the H1 is rendered. Adjust container height or fontSize prop as needed for layout.

---

## 2) GlowCursor — Custom cursor

Install the component (exact command):

```
npx shadcn@latest add @react-bits/GlowCursor-JS-CSS
```

Import and usage (exact code):

```jsx
import GlowCursor from './GlowCursor';

<div style={{ position: 'relative', width: '100%', height: '500px', background: '#050610' }}>
 <GlowCursor
 color="#67E8F9"
 secondaryColor="#A78BFA"
 trailLength={40}
 trailWidth={8}
 trailTaper={0.8}
 followSpeed={0.16}
 glowIntensity={1.9}
 glowSpread={1.2}
 hotspot={0.65}
 brightness={1.25}
 opacity={1}
 pulseSpeed={1.1}
 noiseStrength={0.035}
 idleFade
 idleTimeout={700}
 fadeDuration={900}
 blendMode="screen"
 >
 {/* Your content here */}
 </GlowCursor>
</div>
```

Instruction: Wrap the app's main content or hero area with GlowCursor to apply the custom cursor within that area. If desired site-wide, place at a high level (e.g., in _app.tsx or root layout) but ensure it doesn't conflict with other global pointer handlers.

---

## 3) LogoLoop — Tech stack scroller (place at end)

Install the component (exact command):

```
npx shadcn@latest add @react-bits/LogoLoop-JS-CSS
```

Import and usage (exact code):

```jsx
import LogoLoop from './LogoLoop';
import { SiReact, SiNextdotjs, SiTypescript, SiTailwindcss } from 'react-icons/si';

const techLogos = [
 { node: <SiReact />, title: "React", href: "https://react.dev" },
 { node: <SiNextdotjs />, title: "Next.js", href: "https://nextjs.org" },
 { node: <SiTypescript />, title: "TypeScript", href: "https://www.typescriptlang.org" },
 { node: <SiTailwindcss />, title: "Tailwind CSS", href: "https://tailwindcss.com" },
];

// Alternative with image sources
const imageLogos = [
 { src: "/logos/company1.png", alt: "Company 1", href: "https://company1.com" },
 { src: "/logos/company2.png", alt: "Company 2", href: "https://company2.com" },
 { src: "/logos/company3.png", alt: "Company 3", href: "https://company3.com" },
];

function App() {
 return (
 <div style={{ height: '200px', position: 'relative', overflow: 'hidden'}}>
 {/* Basic horizontal loop */}
 <LogoLoop
 logos={techLogos}
 speed={100}
 direction="left"
 logoHeight={60}
 gap={60}
 hoverSpeed={0}
 scaleOnHover
 fadeOut
 fadeOutColor="#ffffff"
 ariaLabel="Technology partners"
 />
 
 {/* Vertical loop with deceleration on hover */}
 <LogoLoop
 logos={techLogos}
 useCustomRender={false}
/>
 </div>
 );
}
```

Instruction: Place this scroller near the end of the page to show the tech stack used in the project. Use `techLogos` or `imageLogos` depending on whether you prefer icon-based or image-based logos.

---

## 4) DriftWall — Results graph gallery (Matplotlib gallery presentation)

Install the component (exact command):

```
npx shadcn@latest add @react-bits/DriftWall-JS-CSS
```

Import and usage (exact code):

```jsx
import DriftWall from './DriftWall';

const items = [
 { image: 'https://picsum.photos/id/1015/600/400', title: 'Peaks', href: 'https://example.com/one' },
 { image: 'https://picsum.photos/id/1025/600/400', title: 'Pup', href: 'https://example.com/two' },
 { image: 'https://picsum.photos/id/1039/600/400', title: 'Falls', href: 'https://example.com/three' },
];

<div style={{ height: 600 }}>
 <DriftWall
 items={items}
 columns={5}
 tileWidth={200}
 tileHeight={132}
 gap={18}
 tilt={16}
 turn={-14}
 perspective={1200}
 depth={120}
 speed={42}
 direction="up"
 variance={0.45}
 parallax={0.6}
 lift={64}
 fade={0.6}
 dim={0.55}
 overlayColor="#060010"
 radius={14}
 roll={0}
 pauseOnHover={false}
 grayscale={false}
/>
</div>
```

Instruction: Use this section to present Matplotlib or other generated graphs screenshots. Create items array with image URLs pointing to generated graph images (hosted locally in /public or from a CDN). The gallery makes a visually engaging results section.

---

## 5) MorphSlider — Graph animations beside main title

Install the component (exact command):

```
npx shadcn@latest add @react-bits/MorphSlider-JS-CSS
```

Import and usage (exact code):

```jsx
import MorphSlider from './MorphSlider'

const items = [
 { image: 'https://images.unsplash.com/photo-1782977389500-dd7adad33ebe?q=80&w=1600&auto=format&fit=crop', caption: 'One' },
 { image: 'https://images.unsplash.com/photo-1781499455083-6ccc3beb20cd?q=80&w=1600&auto=format&fit=crop', caption: 'Two' },
 { image: 'https://images.unsplash.com/photo-1776394254711-4a0d7345269a?q=80&w=1600&auto=format&fit=crop', caption: 'Three' }
]

<div style={{ height: '500px', position: 'relative' }}>
 <MorphSlider
 items={items}
 transition="melt"
 intensity={0.55}
 aberration={0.35}
 drift={0.4}
 autoplay={false}
 overlayColor="#05060a"
 duration={1.1}
 ease="power2.inOut"
 scale={2.4}
 autoplayDelay={4}
 loop
 radius={16}
 showCaptions
 showControls
 showIndicators
/>
</div>
```

Instruction: Place the MorphSlider beside the hero/main title area (e.g., two-column layout: left = ParticleText heading, right = MorphSlider). Adjust height/scale and duration props to match hero proportions and desired motion.

---

## Integration notes & tips

- Each `npx shadcn@latest add ...` command is the exact installer invocation the project expects; run these in the project root.
- Import paths assume the component files land at the suggested relative path (e.g., `./ParticleText`). If the installer places them elsewhere, update imports accordingly.
- For server-side rendering (Next.js): confirm each component supports SSR; if not, wrap with dynamic import with `ssr: false`.

Example Next.js dynamic import for a client-only component:

```jsx
import dynamic from 'next/dynamic';
const ParticleText = dynamic(() => import('./ParticleText'), { ssr: false });
```

- Host generated Matplotlib images in `/public/results/` and reference them in the `DriftWall` items array: `{ image: '/results/graph1.png', title: 'Graph 1', href: '/results/graph1' }`.
- If applying GlowCursor site-wide, test keyboard accessibility and focus outlines for a11y; make sure cursor wrapper does not disable pointer events unintentionally.
- Adjust colors and glow intensities for dark/light themes as needed.

---

## Example placement in a typical Hero (React/Next) layout

```jsx
// HeroSection.jsx
import ParticleText from './ParticleText';
import MorphSlider from './MorphSlider';

export default function HeroSection() {
 return (
 <section style={{ display: 'flex', alignItems: 'center', gap: 24 }}>
   <div style={{ flex: 1 }}>
     <ParticleText text="Future Interfaces" /* props as above */ />
   </div>

   <aside style={{ width: 600 }}>
     <MorphSlider items={items} /* props as above */ />
   </aside>
 </section>
 );
}
```

---

If any path or installer places the components in a different folder, update the import paths accordingly. This file contains the exact code blocks provided, ready to paste into your project files.

End of document.
