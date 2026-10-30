import { mkdirSync, readFileSync, writeFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";
import * as k from "../anatomy-vendor/iso-kit.mjs";

const HERE = dirname(fileURLToPath(import.meta.url));
const ROOT = join(HERE, "..", "..", "..");
const OUT = join(ROOT, "docs", "assets");
const WIDTH = 1280;
const HEIGHT = 720;
const DECK_Z = 10;
const PLATE = { x: 0, y: 0, w: 286, d: 136, r: 9 };
const CARD = { x: 26, y: 56, w: 30, d: 20, z: 13.2 };
const STOPS = [28, 78, 112, 160, 207, 226];
const STAGES = [
  "INPUT · 200 / 365D",
  "FEATURES · 51",
  "SCALE · Z-SCORE",
  "PCA · 10 / 95.05%",
  "K SWEEP · 2–10 / K=4",
  "PROFILES · 4 OUTPUTS",
];

const source = readFileSync(join(ROOT, "outputs", "metrics", "cluster_load_shapes.csv"), "utf8");
const rows = source.trim().split(/\r?\n/).slice(1)
  .map((line) => line.split(",").map(Number))
  .filter((row) => row.length === 25 && Number.isInteger(row[0]) && row[0] >= 0 && row[0] < 4);
if (rows.length !== 4 || rows.some((row) => row.length !== 25 || row.some((value) => !Number.isFinite(value)))) {
  throw new Error("Expected four saved 24-hour cluster mean profiles.");
}
const profileMax = Math.max(...rows.flatMap((row) => row.slice(1)));
const fitPoints = [
  ...k.boxCorners(PLATE, -16, DECK_Z),
  ...k.boxCorners({ x: 104, y: 36, w: 12, d: 57, r: 2 }, 18, 38),
  ...k.boxCorners({ x: 146, y: 42, w: 28, d: 44, r: 4 }, 10, 32),
  ...k.boxCorners({ x: 197, y: 12, w: 22, d: 22, r: 4 }, 10, 24),
  ...k.boxCorners({ x: 243, y: 9, w: 36, d: 110, r: 2 }, 10, 18),
];
const P = k.fitProjection(fitPoints, WIDTH, HEIGHT, { pad: 34, azimuth: 46 });
const at = (point) => k.iso(point, P);
const L = (path, style) => k.lineSvg(path, style);
const D = (points, style) => k.dotsSvg(points, style);
const byDepth = (points) => [...points].sort(
  (a, b) => k.depthOf([a[0], a[1], 0], P) - k.depthOf([b[0], b[1], 0], P),
);
let solidCount = 0;
const solid = (paths, style) => {
  solidCount += 1;
  return k.solidSvg(paths, style);
};
const slab = (plan, z, h, tone = "mid", bevel = 0.55) =>
  solid(k.slabOf(plan, z, h, P, 4, bevel), { tone, crease: "lo" });
const cylinder = (x, y, r, z, h, tone = "mid", steps = 24) =>
  solid(k.cylinder(x, y, r, z, h, P, steps), { tone, crease: "lo" });
const outline = (plan, z, tone = "faint") => L(k.planOutline(k.insetPlan(plan, 1.5), z, P), { tone });
const screwPoints = (points) => {
  const rings = points.map(([x, y, z = DECK_Z]) => k.ring(x, y, 1.3, z, P, 12)).join("");
  return L(rings, { tone: "lo" }) + D(points.map(([x, y, z = DECK_Z]) => at([x, y, z])), { size: 0.42, tone: "hi" });
};

function foundation() {
  const out = ['<path class="iso-halo" d="' + k.haloOf(PLATE, -16, 12, P) + '"/>'];
  for (const [x, y] of byDepth(k.corners(PLATE, 18))) {
    out.push(cylinder(x, y, 6.3, -16, 2, "lo", 24));
    out.push(cylinder(x, y, 4.8, -14, 4, "mid", 24));
  }
  out.push(slab(PLATE, 0, DECK_Z, "mid", 1.4));
  out.push(outline(PLATE, DECK_Z, "lo"));
  const screws = k.corners(PLATE, 10).map(([x, y]) => [x, y, DECK_Z]);
  out.push(screwPoints(screws));
  return out.join("");
}

function radialSpokes(cx, cy, inner, outer, count, z, every = 2) {
  const major = [];
  const minor = [];
  for (let index = 0; index < count; index += 1) {
    const angle = -Math.PI / 2 + (index / count) * Math.PI * 2;
    const sx = Math.sin(angle);
    const sy = -Math.cos(angle);
    const path = k.lineOnTop(
      [cx + sx * inner, cy + sy * inner],
      [cx + sx * outer, cy + sy * outer],
      z,
      P,
    );
    (index % every === 0 ? major : minor).push(path);
  }
  return L(minor.join(""), { tone: "lo" }) + L(major.join(""), { tone: "hi" });
}

function inputAndTrack() {
  const out = [];
  const inputPad = { x: 15, y: 43, w: 40, d: 40, r: 4 };
  out.push(slab(inputPad, DECK_Z, 2, "lo", 0.7));
  out.push(outline(inputPad, DECK_Z + 2));
  for (const y of [47, 81]) {
    out.push(slab({ x: 18, y, w: 216, d: 4, r: 1 }, DECK_Z, 3, "mid", 0.4));
    out.push(D([at([24, y + 2, DECK_Z + 3]), at([228, y + 2, DECK_Z + 3])], { size: 0.42, tone: "lo" }));
  }
  for (const x of [20, 226]) {
    for (const y of [45, 79]) {
      out.push(slab({ x, y, w: 4, d: 8, r: 1 }, DECK_Z + 1, 5, "mid", 0.5));
      out.push(D([at([x + 2, y + 4, DECK_Z + 6])], { size: 0.45, tone: "hi" }));
    }
  }
  out.push(cylinder(29, 63, 8, DECK_Z + 1, 3, "hi", 32));
  out.push(L(k.knurl(29, 63, 8, DECK_Z + 1, DECK_Z + 4, 32, P), { tone: "lo" }));
  out.push(L(k.sideArc(29, 63, 8, DECK_Z + 1.4, P, 24), { tone: "lo" }));
  out.push(L(k.sideArc(29, 63, 8, DECK_Z + 3.6, P, 24), { tone: "lo" }));
  out.push(cylinder(40, 50, 4.4, DECK_Z + 2, 4, "mid", 24));
  out.push(cylinder(40, 78, 4.4, DECK_Z + 2, 4, "mid", 24));
  const guide = { x: 49, y: 50, w: 7, d: 28, r: 1.2 };
  out.push(slab(guide, DECK_Z + 1, 1.2, "hi", 0.3));
  out.push(outline(guide, DECK_Z + 2.2, "faint"));
  return out.join("");
}

function featureComb() {
  const out = [];
  for (const y of [39, 83]) {
    out.push(slab({ x: 106, y, w: 7, d: 7, r: 1.5 }, DECK_Z, 26, "mid", 0.8));
    out.push(cylinder(109.5, y + 3.5, 4.5, 34, 3, "lo", 20));
  }
  const beam = { x: 104, y: 36, w: 12, d: 57, r: 2 };
  const lower = { x: 104, y: 36, w: 12, d: 57, r: 2 };
  out.push(slab(beam, 34, 4, "hi", 0.65));
  out.push(slab(lower, 18, 2, "mid", 0.4));
  out.push(outline(beam, 38, "faint"));
  const teeth = [];
  for (let index = 0; index < 51; index += 1) {
    const y = 38 + (index / 50) * 53;
    const top = at([110, y, 38]);
    const end = at([110, y, 20]);
    teeth.push("M" + top[0].toFixed(2) + " " + top[1].toFixed(2) + "L" + end[0].toFixed(2) + " " + end[1].toFixed(2));
  }
  out.push(L(k.lineOnTop([110, 36], [110, 93], 38, P), { tone: "faint" }));
  out.push(L(k.lineOnTop([110, 36], [110, 93], 20, P), { tone: "faint" }));
  out.push(L(teeth.join(""), { tone: "lo", width: 0.45 }));
  out.push(D([at([106, 39, 38]), at([114, 39, 38]), at([106, 90, 38]), at([114, 90, 38])], { size: 0.45, tone: "lo" }));
  return out.join("");
}

function scaleRollers() {
  const out = [];
  const bed = { x: 67, y: 44, w: 18, d: 40, r: 3 };
  out.push(slab(bed, DECK_Z, 2, "lo", 0.6));
  for (const y of [52, 76]) {
    out.push(slab({ x: 70, y: y - 5, w: 12, d: 5, r: 1.5 }, DECK_Z + 2, 4, "mid", 0.45));
    out.push(cylinder(76, y, 5, DECK_Z + 5, 6, "hi", 32));
    out.push(L(k.knurl(76, y, 5, DECK_Z + 5, DECK_Z + 11, 24, P), { tone: "lo" }));
    out.push(L(k.sideArc(76, y, 5, DECK_Z + 5.4, P, 20), { tone: "lo" }));
    out.push(L(k.sideArc(76, y, 5, DECK_Z + 10.6, P, 20), { tone: "lo" }));
  }
  out.push(cylinder(75, 31, 7.6, DECK_Z + 1, 3, "mid", 32));
  out.push(L(k.ring(75, 31, 6.2, DECK_Z + 4, P, 32), { tone: "lo" }));
  const zero = at([75, 31, DECK_Z + 4.2]);
  out.push(L(k.lineOnTop([75, 31], [75, 36], DECK_Z + 4.2, P), { tone: "hi", width: 0.8 }));
  out.push(D([zero, at([75, 36, DECK_Z + 4.2])], { size: 0.6, tone: "hi" }));
  return out.join("");
}

function pcaDial() {
  const out = [];
  const pedestal = { x: 146, y: 42, w: 28, d: 44, r: 4 };
  out.push(slab(pedestal, DECK_Z, 4, "lo", 0.8));
  for (const y of [49, 79]) {
    out.push(cylinder(160, y, 4.3, DECK_Z + 4, 8, "mid", 24));
    out.push(L(k.sideArc(160, y, 4.3, DECK_Z + 10, P, 20), { tone: "lo" }));
  }
  out.push(cylinder(160, 64, 17, 22, 6, "hi", 56));
  out.push(cylinder(160, 64, 14.5, 28, 1.4, "mid", 56));
  out.push(L(k.ring(160, 64, 15.7, 29.4, P, 56), { tone: "lo" }));
  out.push(L(k.ring(160, 64, 10.5, 29.4, P, 56), { tone: "faint" }));
  out.push(radialSpokes(160, 64, 10.5, 15.7, 10, 29.4, 2));
  out.push(cylinder(160, 64, 2.2, 29.5, 2.2, "mid", 24));
  out.push(L(k.lineOnTop([160, 64], [169.5, 64], 31.8, P), { tone: "hi", width: 0.9 }));
  out.push(D([at([160, 64, 31.8]), at([169.5, 64, 31.8])], { size: 0.7, tone: "hi" }));
  const nameplate = { x: 151, y: 43, w: 18, d: 5, r: 1 };
  out.push(slab(nameplate, DECK_Z + 4, 0.8, "mid", 0.25));
  out.push(k.faceTextSvg(k.topMatrix([160, 45.5], DECK_Z + 4.8, P, "x"), "PCA", { size: 2, tone: "lo", anchor: "middle" }));
  return out.join("");
}

function kSelector() {
  const out = [];
  const stand = { x: 193, y: 9, w: 30, d: 28, r: 4 };
  out.push(slab(stand, DECK_Z, 2, "lo", 0.7));
  out.push(cylinder(208, 23, 11, DECK_Z + 2, 4, "hi", 40));
  out.push(cylinder(208, 23, 8.7, DECK_Z + 6, 1.2, "mid", 40));
  out.push(L(k.ring(208, 23, 9.5, DECK_Z + 7.2, P, 40), { tone: "lo" }));
  out.push(L(k.ring(208, 23, 5, DECK_Z + 7.2, P, 40), { tone: "faint" }));
  out.push(radialSpokes(208, 23, 5, 9.5, 9, DECK_Z + 7.2, 3));
  out.push(cylinder(208, 23, 1.8, DECK_Z + 7.3, 3, "mid", 20));
  const angle = (-Math.PI / 2) + (2 * Math.PI * (4 - 2)) / 9;
  const end = [208 + Math.cos(angle) * 6.8, 23 + Math.sin(angle) * 6.8];
  out.push(L(k.lineOnTop([208, 23], end, DECK_Z + 10.4, P), { tone: "lit", width: 1.1 }));
  out.push(D([at([208, 23, DECK_Z + 10.4]), at([end[0], end[1], DECK_Z + 10.4])], { size: 0.7, tone: "lit" }));
  return out.join("");
}

function profilePath(x, y, z, width, depth, values) {
  const points = values.map((value, index) => [
    x + 1.5 + (index / (values.length - 1)) * (width - 3),
    y + 2 + (value / profileMax) * (depth - 4),
  ]);
  return points.slice(0, -1).map((point, index) =>
    k.lineOnTop(point, points[index + 1], z, P),
  ).join("");
}

function outputTrays() {
  const out = [];
  rows.forEach((row, index) => {
    const x = 243;
    const y = 9 + index * 29;
    const tray = { x, y, w: 36, d: 23, r: 2 };
    out.push(slab(tray, DECK_Z, 2, "lo", 0.5));
    out.push(slab({ x, y: y + 20, w: 36, d: 3, r: 1 }, DECK_Z + 2, 3, "mid", 0.5));
    out.push(slab({ x, y, w: 3, d: 20, r: 1 }, DECK_Z + 2, 2.6, "mid", 0.4));
    out.push(slab({ x: x + 33, y, w: 3, d: 20, r: 1 }, DECK_Z + 2, 2.6, "mid", 0.4));
    const card = { x: x + 4, y: y + 2, w: 24, d: 16, r: 1 };
    out.push(slab(card, DECK_Z + 2, 0.8, "hi", 0.3));
    out.push(outline(card, DECK_Z + 2.8, "faint"));
    out.push(L(profilePath(card.x, card.y, DECK_Z + 2.9, card.w, card.d, row.slice(1)), { tone: "hi", width: 0.65 }));
    out.push(cylinder(x + 31, y + 11, 1.8, DECK_Z + 2, 2.1, "hi", 16));
    out.push(L(k.ring(x + 31, y + 11, 2.5, DECK_Z + 4.1, P, 16), { tone: "lo" }));
  });
  return out.join("");
}

function travellingCard() {
  const plan = { x: CARD.x, y: CARD.y, w: CARD.w, d: CARD.d, r: 1.8 };
  const out = [
    slab(plan, CARD.z, 1.1, "hi", 0.35),
    outline(plan, CARD.z + 1.1, "lo"),
  ];
  const hours = [];
  for (let hour = 0; hour < 24; hour += 1) {
    const x = CARD.x + 2.8 + (hour / 23) * (CARD.w - 5.6);
    hours.push(at([x, CARD.y + CARD.d / 2, CARD.z + 1.2]));
  }
  out.push(D(hours, { size: 0.42, tone: "lo" }));
  return '<g data-part="profile-carrier" transform="translate(0 0)">' + out.join("") + "</g>";
}

const svgBody = [
  '<rect width="' + WIDTH + '" height="' + HEIGHT + '" fill="#151E22"/>',
  foundation(),
  inputAndTrack(),
  featureComb(),
  scaleRollers(),
  pcaDial(),
  kSelector(),
  outputTrays(),
  travellingCard(),
].join("");

if (solidCount < 40 || solidCount > 80) {
  throw new Error("Figure size check failed: " + solidCount + " solids (expected 40–80).");
}

const rawSvg = k.figureSvg({
  width: WIDTH,
  height: HEIGHT,
  label: "A dark isometric energy-pattern analyzer: hourly profile cards pass through a 51-feature comb, z-score rollers and a 10-component PCA dial; a K selector chooses four output trays with the saved 24-hour cluster mean profiles.",
  body: svgBody,
  standalone: "dark",
});
const unit0 = at([0, 0, 0]);
const unit1 = at([1, 0, 0]);
const pxPerUnit = [unit1[0] - unit0[0], unit1[1] - unit0[1]];
const stageScreenX = STOPS.map((x) => at([x + CARD.w / 2, CARD.y, CARD.z])[0]);
const paletteVars = [
  ".iso{--anatomy-page:#0F1519;--anatomy-card:#151E22;--anatomy-text:#A7B6B2;--anatomy-strong:#E8EFED;--anatomy-muted:#778985;",
  "--anatomy-paper:#151E22;--anatomy-face:#1B272A;--anatomy-top:#243236;--anatomy-shade-0:#10171A;--anatomy-shade-1:#151E22;--anatomy-shade-2:#202C2F;--anatomy-shade-3:#2B393C;",
  "--anatomy-lit-top:#25413E;--anatomy-lit-shade:#1A302E;--anatomy-hi:#B7C4C1;--anatomy-mid:#758985;--anatomy-lo:#4A5E62;--anatomy-faint:#34484C;--anatomy-lit:#55B7AA;",
  "--anatomy-halo:#060B0D;--anatomy-halo-opacity:.86;--anatomy-dot:#D2DEDB;}",
].join("");
const pageCss = [
  paletteVars,
  "html{color-scheme:dark}body{background:#0F1519;color:#A7B6B2}.iso-page{width:min(1280px,100% - 32px);margin:48px auto 84px}",
  ".iso-plate{background:#151E22;box-shadow:0 0 0 1px #2B393C;padding:54px 24px 52px}.iso-figure{margin:26px 0 34px}",
  ".iso-plate-corner[data-corner=title]{color:#E8EFED}.iso-plate-corner[data-corner=fig],.iso-plate-corner[data-corner=readout]{color:#A7B6B2}",
  ".iso-caption{max-width:1020px;color:#A7B6B2}.iso-keys{color:#A7B6B2}.iso-plate-corner{font-size:11px}",
  "@media(max-width:560px){.iso-page{width:100%;margin:20px auto 48px}.iso-plate{padding:48px 10px 68px}.iso-plate-corner{font-size:8.5px}.iso-plate-corner[data-corner=hint]{bottom:17px}.iso-plate-corner[data-corner=readout]{max-width:54%;white-space:normal;text-align:right;line-height:1.3}}",
].join("");
const interactiveSvg = rawSvg.replace("</style>", paletteVars + "</style>");
const standaloneFrame = [
  '<rect x="10" y="10" width="1260" height="700" fill="none" stroke="#2B393C" stroke-width="1"/>',
  '<path d="M24 58H1256M24 662H1256" fill="none" stroke="#2B393C" stroke-width="1"/>',
  '<g fill="#A7B6B2" font-family="ui-monospace, SFMono-Regular, Consolas, monospace" font-size="11" letter-spacing="1">',
  '<text x="32" y="42">FIG 01</text>',
  '<text x="1248" y="42" text-anchor="end" fill="#E8EFED">ENERGY-PATTERN ANALYZER</text>',
  '<text x="32" y="694">← / → OR HOVER TO FOLLOW ONE PROFILE</text>',
  '<text x="1248" y="694" text-anchor="end">INPUT · 200 / 365D</text>',
  '</g>',
].join("");
const svg = interactiveSvg.replace("</svg>", standaloneFrame + "</svg>");
const liveScript = [
  "const stage=document.querySelector('.iso-stage');",
  "const svg=stage.querySelector('svg');",
  "const carrier=svg.querySelector('[data-part=profile-carrier]');",
  "const readout=document.querySelector('[data-readout]');",
  "const stops=" + JSON.stringify(STOPS) + ";",
  "const labels=" + JSON.stringify(STAGES) + ";",
  "const screenX=" + JSON.stringify(stageScreenX) + ";",
  "const ux=" + JSON.stringify(pxPerUnit[0]) + ",uy=" + JSON.stringify(pxPerUnit[1]) + ";",
  "const baseX=" + CARD.x + ",reduced=matchMedia('(prefers-reduced-motion: reduce)');",
  "let current=stops[0],targetIndex=0,last=0,clock=0,visible=false,userUntil=0,frame=0;",
  "const clamp=(n,a,b)=>Math.max(a,Math.min(b,n));",
  "const setTarget=(i)=>{targetIndex=clamp(i,0,stops.length-1);userUntil=performance.now()+6500;if(reduced.matches)current=stops[targetIndex];run();};",
  "const updateReadout=()=>{readout.textContent=labels[targetIndex];stage.setAttribute('aria-valuenow',String(targetIndex));stage.setAttribute('aria-valuetext',labels[targetIndex]);};",
  "function tick(now){frame=0;if(!visible)return;const dt=last?Math.min(64,now-last):16;last=now;if(!reduced.matches&&now>userUntil){clock+=dt;if(clock>2300){clock=0;targetIndex=(targetIndex+1)%stops.length;updateReadout();}}const target=stops[targetIndex];current+=reduced.matches?0:(target-current)*(1-Math.exp(-dt/420));if(Math.abs(target-current)<.04)current=target;const dx=(current-baseX)*ux,dy=(current-baseX)*uy;carrier.setAttribute('transform','translate('+dx.toFixed(2)+' '+dy.toFixed(2)+')');if(Math.abs(target-current)>.04||!reduced.matches)run();}",
  "function run(){if(visible&&!frame)frame=requestAnimationFrame(tick);}",
  "stage.addEventListener('pointermove',(event)=>{const rect=svg.getBoundingClientRect();const x=(event.clientX-rect.left)/rect.width*svg.viewBox.baseVal.width;let best=0;for(let i=1;i<screenX.length;i++)if(Math.abs(screenX[i]-x)<Math.abs(screenX[best]-x))best=i;if(best!==targetIndex)setTarget(best);});",
  "stage.addEventListener('pointerdown',()=>stage.focus({preventScroll:true}));",
  "stage.addEventListener('keydown',(event)=>{if(event.key==='ArrowRight'||event.key==='ArrowDown'){event.preventDefault();setTarget(targetIndex+1);}else if(event.key==='ArrowLeft'||event.key==='ArrowUp'){event.preventDefault();setTarget(targetIndex-1);}else if(event.key==='Home'){event.preventDefault();setTarget(0);}else if(event.key==='End'){event.preventDefault();setTarget(stops.length-1);}});",
  "new IntersectionObserver((entries)=>{visible=entries[entries.length-1].isIntersecting;if(visible)run();else{cancelAnimationFrame(frame);frame=0;last=0;}},{rootMargin:'120px 0px'}).observe(stage);",
  "if(reduced.matches){userUntil=Number.POSITIVE_INFINITY;current=stops[0];}updateReadout();",
].join("\n");
const figBody = k.plateHtml({
  fig: "FIG 01",
  title: "Energy-pattern analyzer",
  hint: "← / → or hover to follow one profile",
  readout: STAGES[0],
  keys: [
    { mark: "raised", label: "Profile strip and feature comb" },
    { mark: "lit", label: "Selected K in the candidate sweep" },
    { mark: "flat", label: "Four trays contain saved cluster means" },
  ],
  caption: "Reference synthetic run: 200 consumers × 365 days → 51 standardized features → 10 PCs retaining 95.05% variance → K=4 selected from candidates 2–10. Output traces are the saved normalized 24-hour cluster means. Synthetic labels are held out until post-fit validation. The moving strip is an explanatory stage marker; it does not run the model.",
  body: '<div class="iso-stage" tabindex="0" role="slider" aria-label="Interactive walkthrough of the synthetic PCA and K-Means pipeline" aria-valuemin="0" aria-valuemax="5" aria-valuenow="0" aria-valuetext="' + STAGES[0] + '">' + interactiveSvg + "</div>",
});
const html = k.pageHtml({
  title: "Energy-pattern analyzer",
  theme: "dark",
  body: figBody,
  script: liveScript,
  width: 1280,
}).replace("</style>", pageCss + "</style>");

mkdirSync(OUT, { recursive: true });
writeFileSync(join(OUT, "research-method-instrument.svg"), svg, "utf8");
writeFileSync(join(OUT, "research-method-instrument.html"), html, "utf8");
console.log("Wrote research-method-instrument.svg and research-method-instrument.html");
console.log("Figure solids:", solidCount, "| saved cluster profiles:", rows.length, "| theme: dark");
