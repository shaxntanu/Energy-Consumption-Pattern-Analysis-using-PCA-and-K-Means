import { mkdirSync, readFileSync, writeFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";
import * as K from "../kit/iso-kit.mjs";
import { kitScript } from "../scripts/inline-kit.mjs";
import { loadStudyData, profileAt, summarizeProfile } from "./model.mjs";

const HERE = dirname(fileURLToPath(import.meta.url));
const ROOT = fileURLToPath(new URL("../../../", import.meta.url));
const OUT = join(ROOT, "web", "public", "research");
const STUDY = loadStudyData(ROOT);

const WIDTH = 900;
const HEIGHT = 500;
const BASE = { x: -27, y: -40, w: 244, d: 104, r: 5 };
const BASE_BOTTOM = -1;
const BASE_TOP = 4;
const FOOT_BOTTOM = -7;
const X0 = 0;
const HOURS = 24;
const STEP = 8.45;
const BAR_W = 4.15;
const BAR_D = 5.5;
const BAR_MAX_H = 31;
const BAR_MAX_KW = 190_000;
const BAR_ROWS = Object.freeze({ baseline: -15, scenario: 5 });
const DIAL = Object.freeze({ x: -15, y: 43, r: 8.2, z: BASE_TOP + 1.2 });
const DIAL_FROM = -3 * Math.PI / 4;
const DIAL_SPAN = 3 * Math.PI / 2;

const xAt = (hour) => X0 + hour * STEP;
const barHeight = (kw) => Math.max(0.15, kw / BAR_MAX_KW * BAR_MAX_H);
const barPlan = (hour, y) => ({ x: xAt(hour), y, w: BAR_W, d: BAR_D, r: 0.7 });
const maxProfileHeight = Math.max(
  ...Object.values(STUDY.profiles).flat().map(barHeight),
);

const projectionPoints = [
  ...K.boxCorners(BASE, FOOT_BOTTOM, BASE_TOP),
  ...Array.from({ length: HOURS }, (_, hour) => [
    ...K.boxCorners(barPlan(hour, BAR_ROWS.baseline), BASE_TOP, BASE_TOP + maxProfileHeight),
    ...K.boxCorners(barPlan(hour, BAR_ROWS.scenario), BASE_TOP, BASE_TOP + maxProfileHeight),
  ]).flat(),
  ...K.boxCorners({ x: DIAL.x - DIAL.r, y: DIAL.y - DIAL.r, w: DIAL.r * 2, d: DIAL.r * 2 }, BASE_TOP, DIAL.z + 3),
];
const P = K.fitProjection(projectionPoints, WIDTH, HEIGHT, {
  pad: 42,
  azimuth: 43,
  elevation: 31,
});

const solid = (paths, tone = "mid", options = {}) => K.solidSvg(paths, {
  tone,
  crease: "lo",
  ...options,
});
const line = (path, tone = "lo", options = {}) => K.lineSvg(path, { tone, ...options });
const dots = (points, tone = "mid", size = 0.55) => K.dotsSvg(points, { tone, size });
const byDepth = (items) => [...items].sort((left, right) =>
  K.depthOf(left.at, P) - K.depthOf(right.at, P));

function barSvg(hour, y, kw, active) {
  const shape = K.slabOf(barPlan(hour, y), BASE_TOP, barHeight(kw), P, 4, 0.45);
  return solid(shape, active ? "hi" : "mid", {
    className: active ? "scenario-bar" : "baseline-bar",
    lit: active,
  });
}

function plateAndParts(profile, scenario) {
  const items = [];
  const add = (at, svg) => items.push({ at, svg });

  const halo = `<path class="iso-halo" d="${K.haloOf(BASE, BASE_BOTTOM, BASE_TOP - BASE_BOTTOM, P)}"/>`;
  const feet = K.corners(BASE, 11).map(([x, y]) => ({
    at: [x, y, BASE_BOTTOM],
    svg: [
      solid(K.cylinder(x, y, 4.1, FOOT_BOTTOM, BASE_BOTTOM - FOOT_BOTTOM, P, 24), "lo"),
      solid(K.cylinder(x, y, 2.5, FOOT_BOTTOM, 1.5, P, 24), "mid"),
    ].join(""),
  }));
  items.push(...feet);
  add([0, 0, BASE_BOTTOM], solid(K.slabOf(BASE, BASE_BOTTOM, BASE_TOP - BASE_BOTTOM, P, 8, 1.2), "mid"));
  add([0, 0, BASE_TOP], line(K.planOutline(K.insetPlan(BASE, 5), BASE_TOP, P, 8), "lo"));

  const cornerScrews = K.corners(BASE, 8);
  add([0, 0, BASE_TOP + 0.1], line(cornerScrews.map(([x, y]) => K.ring(x, y, 2, BASE_TOP + 0.1, P, 16)).join(""), "lo"));
  add([0, 0, BASE_TOP + 0.1], dots(cornerScrews.map(([x, y]) => K.iso([x, y, BASE_TOP + 0.1], P)), "lo", 0.5));
  for (const [x, y] of cornerScrews) {
    add([x, y, BASE_TOP], solid(K.cylinder(x, y, 1.25, BASE_TOP, 0.7, P, 16), "lo"));
  }

  const tracks = [
    { x: X0 - 2, y: BAR_ROWS.baseline - 2, w: xAt(HOURS - 1) + BAR_W - X0 + 4, d: 2, r: 0.7 },
    { x: X0 - 2, y: BAR_ROWS.scenario - 2, w: xAt(HOURS - 1) + BAR_W - X0 + 4, d: 2, r: 0.7 },
  ];
  for (const [index, track] of tracks.entries()) {
    add([track.x, track.y, BASE_TOP], solid(K.slabOf(track, BASE_TOP, 1.5, P, 4, 0.4), index ? "hi" : "lo"));
    add([track.x, track.y, BASE_TOP + 1.5], line(K.planOutline(K.insetPlan(track, 0.5), BASE_TOP + 1.5, P, 4), "faint"));
  }

  for (let hour = 0; hour < HOURS; hour++) {
    add([xAt(hour), BAR_ROWS.baseline, BASE_TOP], barSvg(hour, BAR_ROWS.baseline, profileAt(STUDY, "target", 0)[hour], false));
    add([xAt(hour), BAR_ROWS.scenario, BASE_TOP], `<g data-live-bar="${hour}">${barSvg(hour, BAR_ROWS.scenario, profile[hour], true)}</g>`);
  }

  // The ruler indexes the 24 local-clock hours; major marks land every six hours.
  const ruler = { x: X0 - 2, y: 19, w: xAt(HOURS - 1) - X0 + 4, d: 4, r: 0.7 };
  add([ruler.x, ruler.y, BASE_TOP], solid(K.slabOf(ruler, BASE_TOP, 0.8, P, 4, 0.25), "lo", { crease: "none" }));
  const ticks = K.topTicks(X0, xAt(HOURS - 1), STEP, 6, ruler.y + 1, BASE_TOP + 0.8, [1.3, 2.8], P);
  add([ruler.x, ruler.y, BASE_TOP + 0.8], line(ticks.minor, "faint"));
  add([ruler.x, ruler.y, BASE_TOP + 0.8], line(ticks.major, "mid"));

  // Window bands meet at 17:00: destination [12,17), then evening source [17,21).
  const windows = [
    { plan: { x: xAt(12), y: 34, w: 5 * STEP, d: 6, r: 0.8 }, tone: "lo" },
    { plan: { x: xAt(17), y: 34, w: 4 * STEP, d: 6, r: 0.8 }, tone: "mid" },
  ];
  for (const window of windows) {
    add([window.plan.x, window.plan.y, BASE_TOP], solid(K.slabOf(window.plan, BASE_TOP, 0.85, P, 4, 0.25), window.tone, { crease: "none" }));
    add([window.plan.x, window.plan.y, BASE_TOP + 0.85], line(K.planOutline(K.insetPlan(window.plan, 0.5), BASE_TOP + 0.85, P, 4), "faint"));
  }

  // A small physical dial tracks the assumed 0–10% scenario intensity.
  const dialHousing = { x: DIAL.x - 10, y: DIAL.y - 10, w: 20, d: 20, r: 2.5 };
  add([dialHousing.x, dialHousing.y, BASE_TOP], solid(K.slabOf(dialHousing, BASE_TOP, 1.2, P, 5, 0.35), "lo"));
  add([DIAL.x, DIAL.y, DIAL.z], solid(K.cylinder(DIAL.x, DIAL.y, DIAL.r, DIAL.z - 1.2, 2.4, P, 48, 0.35), "hi"));
  add([DIAL.x, DIAL.y, DIAL.z + 1.2], line(K.ring(DIAL.x, DIAL.y, DIAL.r - 1.2, DIAL.z + 1.2, P, 48), "lo"));
  const dialTicks = K.radialTicks(DIAL.x, DIAL.y, DIAL.r - 0.5, 11, 5, DIAL.z + 1.25, [1.2, 2], P, DIAL_FROM, DIAL_SPAN);
  add([DIAL.x, DIAL.y, DIAL.z + 1.25], line(dialTicks.minor, "faint"));
  add([DIAL.x, DIAL.y, DIAL.z + 1.25], line(dialTicks.major, "mid"));
  const pointerAngle = DIAL_FROM + DIAL_SPAN;
  const pointer = K.lineOnTop(
    [DIAL.x, DIAL.y],
    [DIAL.x + Math.sin(pointerAngle) * (DIAL.r - 2.6), DIAL.y - Math.cos(pointerAngle) * (DIAL.r - 2.6)],
    DIAL.z + 1.35,
    P,
  );
  add([DIAL.x, DIAL.y, DIAL.z + 1.35], `<g id="flex-pointer">${line(pointer, "lit", { free: "end" })}</g>`);
  add([DIAL.x, DIAL.y, DIAL.z + 1.4], dots([K.iso([DIAL.x, DIAL.y, DIAL.z + 1.4], P)], "hi", 0.8));

  // A guarded end-stop and capped pins make the two rows read as a real fixture.
  for (const y of [BAR_ROWS.baseline - 1.5, BAR_ROWS.scenario - 1.5]) {
    for (const x of [X0 - 4, xAt(HOURS - 1) + BAR_W + 1.5]) {
      const stop = { x, y, w: 2.8, d: BAR_D + 3, r: 0.8 };
      add([x, y, BASE_TOP], solid(K.slabOf(stop, BASE_TOP, 3.5, P, 4, 0.4), "mid"));
      add([x + stop.w / 2, y + stop.d / 2, BASE_TOP + 3.5], dots([K.iso([x + stop.w / 2, y + stop.d / 2, BASE_TOP + 3.5], P)], "hi", 0.45));
    }
  }

  // A guarded tally window sits at the front edge, apart from the hourly bars.
  const tally = { x: xAt(HOURS - 1) + 6, y: 35, w: 13, d: 15, r: 1.8 };
  add([tally.x, tally.y, BASE_TOP], solid(K.slabOf(tally, BASE_TOP, 1.4, P, 5, 0.35), "mid"));
  const inset = K.insetPlan(tally, 2);
  add([tally.x, tally.y, BASE_TOP + 1.4], solid(K.slabOf(inset, BASE_TOP + 1.4, 0.5, P, 4, 0.15), "lo", { crease: "none" }));
  add([tally.x, tally.y, BASE_TOP + 1.9], line(K.planOutline(K.insetPlan(tally, 2), BASE_TOP + 1.9, P, 4), "faint"));

  return halo + byDepth(items).map((item) => item.svg).join("");
}

function scene(profile, scenario, fraction) {
  const label = `Isometric hourly load-shifting test rig for the ${scenario} scenario. Two rows of 24 bars show the observed and scenario hourly demand for the saved 2012 UCI sample of 104 clients. The dial tracks the assumed shift intensity from zero to ten percent. The destination is 12:00–17:00 and the source is 17:00–21:00. This is a conceptual illustration of a software scenario, not physical equipment or observed participant response.`;
  return K.figureSvg({ width: WIDTH, height: HEIGHT, label, body: plateAndParts(profile, scenario), standalone: "dark" });
}

const currentScenario = "target";
const initialPercent = 10;
const initialProfile = profileAt(STUDY, currentScenario, initialPercent);
const initialSummary = summarizeProfile(STUDY, initialProfile, "target", initialPercent);
const DATA = {
  baseline: STUDY.profiles.baseline_kw,
  scenarios: {
    target: STUDY.profiles.target_cluster_kw,
    comparator: STUDY.profiles.equal_energy_comparator_kw,
  },
  shiftedKwh: {
    target: STUDY.metrics.target_evening_heavy_cluster.energy_shifted_kwh_per_average_day,
    comparator: STUDY.metrics.equal_energy_non_target_comparator.energy_shifted_kwh_per_average_day,
  },
  baselineEveningPeakKw: STUDY.metrics.observed_baseline.evening_peak_kw,
  baselinePeakKw: STUDY.metrics.observed_baseline.aggregate_peak_kw,
  clients: STUDY.analysis.analyzed_clients,
  targetCluster: STUDY.analysis.target_cluster,
  targetClusterSize: STUDY.analysis.target_cluster_size,
  maxFlexPercent: 10,
  sourceHours: [17, 21],
  destinationHours: [12, 17],
  projection: P,
  geometry: { baseTop: BASE_TOP, rows: BAR_ROWS, x0: X0, step: STEP, barW: BAR_W, barD: BAR_D, barMaxH: BAR_MAX_H, barMaxKw: BAR_MAX_KW, dial: DIAL, dialFrom: DIAL_FROM, dialSpan: DIAL_SPAN },
};
const DATA_SCRIPT = JSON.stringify(DATA).replaceAll("<", "\\u003c");

function controlsHtml() {
  return `<div class="rig-controls">
    <fieldset class="scenario-choice">
      <legend>Profile shown in the front row</legend>
      <div class="scenario-options">
        <button type="button" data-scenario="baseline" aria-pressed="false">Observed baseline</button>
        <button type="button" data-scenario="target" aria-pressed="true">Shift evening-heavy cluster</button>
        <button type="button" data-scenario="comparator" aria-pressed="false">Equal-energy comparison</button>
      </div>
    </fieldset>
    <div class="flex-row">
      <label for="flex-range">Assumed shift intensity <output id="flex-value">10%</output></label>
      <input id="flex-range" type="range" min="0" max="10" step="0.1" value="10" aria-label="Assumed scenario intensity, from zero to ten percent of the reference shift">
      <button id="tour-toggle" type="button" aria-pressed="true">Pause motion</button>
    </div>
    <p class="control-note">The range scales the saved 10% reference scenario linearly. In the equal-energy comparison, the shifted kWh are held to match the target case.</p>
  </div>`;
}

function metricsHtml(summary) {
  return `<div class="rig-metrics" aria-live="polite" aria-atomic="true">
    <div><span>Whole-day peak</span><strong id="peak-value">${(summary.peakKw / 1000).toFixed(2)} MW · ${String(summary.peakHour).padStart(2, "0")}:00</strong></div>
    <div><span>Evening peak change</span><strong id="evening-value">−${Math.abs(summary.eveningPeakReductionPercent).toFixed(2)}%</strong></div>
    <div><span>Energy shifted</span><strong id="shift-value">${(summary.shiftedKwhPerAverageDay / 1000).toFixed(2)} MWh / avg day</strong></div>
    <div><span>Daily total</span><strong id="energy-value">Preserved by construction</strong></div>
  </div>`;
}

const figure = scene(initialProfile, "target cluster", initialPercent);
const plate = K.plateHtml({
  fig: "FIG 01 · UCI 2012",
  title: "Load-shift test bench",
  hint: "Use the controls · motion pauses when touched",
  readout: `${(initialSummary.peakKw / 1000).toFixed(1)} MW @ ${String(initialSummary.peakHour).padStart(2, "0")}`,
  keys: [
    { mark: "raised", label: "Observed hourly demand · saved UCI sample" },
    { mark: "lit", label: "Scenario hourly demand · assumption-driven" },
  ],
  caption: "A conceptual instrument for a software counterfactual, not a physical control device. The source band is 17:00–21:00; the destination band is 12:00–17:00. Each bar is an exact saved average-hour demand value for all 104 analyzed UCI clients in 2012.",
  body: `${controlsHtml()}<div class="iso-stage" id="rig-stage">${figure}</div>${metricsHtml(initialSummary)}<p class="scope-note">UCI identifies anonymized points/clients, not confirmed households. No participant response, flexibility, causal effect, bill saving, or actual peak reduction was measured. The slider replays the stored profile arithmetic and does not re-fit the clustering.</p>`,
});

const styles = `<style>
.iso-page{margin:28px auto 52px}
.iso-plate{padding:54px 24px 44px;background:#101010;box-shadow:0 0 0 1px #3a3a3f}
.rig-controls{display:grid;gap:15px;margin:0 auto 14px;max-width:820px}
.scenario-choice{min-width:0;margin:0;padding:0;border:0}
.scenario-choice legend,.flex-row label{display:flex;align-items:center;justify-content:space-between;gap:12px;margin:0 0 8px;color:#a3a3a3;font:11px/1.4 var(--anatomy-mono);letter-spacing:.045em;text-transform:uppercase}
.scenario-options{display:flex;flex-wrap:wrap;gap:7px}
.scenario-options button,#tour-toggle{min-height:36px;padding:7px 11px;border:1px solid #393939;border-radius:3px;background:#151515;color:#aaa;font:11px/1.2 var(--anatomy-mono);cursor:pointer}
.scenario-options button[aria-pressed="true"],#tour-toggle[aria-pressed="true"]{border-color:#aaa;background:#202020;color:#fff}
.scenario-options button:focus-visible,#tour-toggle:focus-visible,input:focus-visible{outline:2px solid #fff;outline-offset:2px}
.flex-row{display:grid;grid-template-columns:1fr auto;align-items:center;gap:4px 14px}
.flex-row label{grid-column:1 / -1;margin:0}
.flex-row output{color:#fff;font-variant-numeric:tabular-nums}
.flex-row input{width:100%;margin:0;accent-color:#eee}
#tour-toggle{grid-column:2;grid-row:2;min-width:110px}
.control-note,.scope-note{margin:0;color:#777;font:12px/1.55 ui-sans-serif,system-ui,sans-serif}
.control-note{max-width:72ch}
.iso-stage{overflow:hidden;border:1px solid #292929;background:#0d0d0d}
.iso-stage .iso-svg{width:100%;height:auto}
.iso-svg .baseline-bar>.iso-fill{fill:#202020}
.iso-svg .baseline-bar>.iso-top{fill:#3a3a3a}
.iso-svg .baseline-bar>.iso-shade{fill:#292929}
.iso-svg .scenario-bar>.iso-fill{fill:#303030}
.iso-svg .scenario-bar>.iso-top{fill:#898989}
.iso-svg .scenario-bar>.iso-shade{fill:#555}
.iso-svg .scenario-bar>.iso-edge{stroke:#fff}
.rig-metrics{display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:8px;margin:14px 0 10px}
.rig-metrics>div{min-width:0;padding:10px 11px;border:1px solid #2b2b2b;background:#141414}
.rig-metrics span,.rig-metrics strong{display:block}
.rig-metrics span{margin-bottom:5px;color:#777;font:9px/1.4 var(--anatomy-mono);letter-spacing:.04em;text-transform:uppercase}
.rig-metrics strong{color:#eee;font:12px/1.4 var(--anatomy-mono);font-variant-numeric:tabular-nums}
.scope-note{margin-top:12px;max-width:84ch}
@media(max-width:680px){.iso-page{width:min(100% - 18px,940px);margin:16px auto 28px}.iso-plate{padding:52px 9px 35px}.rig-controls{gap:12px}.scenario-options{display:grid;grid-template-columns:1fr}.scenario-options button{text-align:left}.rig-metrics{grid-template-columns:repeat(2,minmax(0,1fr))}.rig-metrics strong{font-size:10px}.iso-plate-corners{inset:15px 12px}.iso-plate-corner{font-size:9px}.iso-plate-corner[data-corner="hint"]{max-width:55%;white-space:normal;bottom:14px}.iso-plate-corner[data-corner="readout"]{max-width:43%;white-space:normal;text-align:right;bottom:14px}}
@media(prefers-reduced-motion:reduce){*{scroll-behavior:auto!important;animation:none!important;transition:none!important}}
</style>`;

const live = `
const DATA = ${DATA_SCRIPT};
const stage = document.querySelector("#rig-stage");
const svg = stage.querySelector("svg");
const range = document.querySelector("#flex-range");
const flexValue = document.querySelector("#flex-value");
const scenarioButtons = [...document.querySelectorAll("[data-scenario]")];
const readout = document.querySelector("[data-readout]");
const tourButton = document.querySelector("#tour-toggle");
const reduced = matchMedia("(prefers-reduced-motion: reduce)");
const profileGroups = [...svg.querySelectorAll("[data-live-bar]")];
const pointer = svg.querySelector("#flex-pointer .iso-line");
const G = DATA.geometry;
const P = DATA.projection;
let scenario = "target";
let percent = ${initialPercent};
let displayedPercent = percent;
let lastFrame = 0;
let tourClock = 8;
let touring = !reduced.matches;
let visible = false;
let frame = 0;

const lerp = (a,b,t) => a + (b-a)*t;
const clamp = (v,a,b) => Math.min(b,Math.max(a,v));
const ease = (t) => 1 - Math.pow(1 - t, 3);
const fmt = (n,d=2) => new Intl.NumberFormat("en-US",{minimumFractionDigits:d,maximumFractionDigits:d}).format(n);
const currentProfile = (p) => scenario==="baseline"?DATA.baseline:DATA.baseline.map((base,i)=>base+(DATA.scenarios[scenario][i]-base)*(p/DATA.maxFlexPercent));
const summarize = (values,p) => {
  const peak = Math.max(...values), peakHour = values.indexOf(peak);
  const evening = Math.max(...values.slice(DATA.sourceHours[0],DATA.sourceHours[1]));
  const reduction = 100*(DATA.baselineEveningPeakKw-evening)/DATA.baselineEveningPeakKw;
  return {peak,peakHour,evening,reduction,shifted:scenario==="baseline"?0:DATA.shiftedKwh[scenario]*p/DATA.maxFlexPercent};
};
const barMarkup = (hour,value) => solidSvg(slabOf({x:G.x0+hour*G.step,y:G.rows.scenario,w:G.barW,d:G.barD,r:.7},G.baseTop,Math.max(.15,value/G.barMaxKw*G.barMaxH),P,4,.45),{tone:"hi",crease:"lo",lit:true});
function redraw(p){
  const values=currentProfile(p);
  for(let hour=0;hour<values.length;hour++) profileGroups[hour].innerHTML=barMarkup(hour,values[hour]);
  const angle=G.dialFrom+(p/DATA.maxFlexPercent)*G.dialSpan;
  const end=[G.dial.x+Math.sin(angle)*(G.dial.r-2.6),G.dial.y-Math.cos(angle)*(G.dial.r-2.6)];
  pointer.setAttribute("d",lineOnTop([G.dial.x,G.dial.y],end,G.dial.z+1.35,P));
  const m=summarize(values,p);
  flexValue.value=p.toFixed(1)+"%";
  flexValue.textContent=p.toFixed(1)+"%";
  readout.textContent=fmt(m.peak/1000,1)+" MW @ "+String(m.peakHour).padStart(2,"0");
  document.querySelector("#peak-value").textContent=fmt(m.peak/1000)+" MW · "+String(m.peakHour).padStart(2,"0")+":00";
  document.querySelector("#evening-value").textContent=(m.reduction>=0?"−":"+")+Math.abs(m.reduction).toFixed(2)+"%";
  document.querySelector("#shift-value").textContent=fmt(m.shifted/1000)+" MWh / avg day";
  document.querySelector("#energy-value").textContent="Preserved by construction";
  stage.setAttribute("aria-label",scenario+" scenario at "+p.toFixed(1)+" percent intensity. Whole-day peak "+fmt(m.peak/1000)+" megawatts at "+String(m.peakHour).padStart(2,"0")+" hundred hours; evening peak change "+Math.abs(m.reduction).toFixed(2)+" percent.");
}
function tick(now){
  const dt=lastFrame?Math.min((now-lastFrame)/1000,1/30):1/60; lastFrame=now;
  if(touring&&!reduced.matches){tourClock+=dt;percent=(1-Math.cos(tourClock*2*Math.PI/16))*DATA.maxFlexPercent/2;range.value=percent.toFixed(1);}
  const blend=reduced.matches?1:1-Math.exp(-dt/.24);
  displayedPercent=lerp(displayedPercent,percent,blend);
  if(Math.abs(displayedPercent-percent)<.015)displayedPercent=percent;
  redraw(displayedPercent);
  const active=touring||Math.abs(displayedPercent-percent)>.015;
  frame=visible&&active?requestAnimationFrame(tick):0;
}
function run(){if(!frame&&visible){lastFrame=0;frame=requestAnimationFrame(tick);}}
function pauseForInput(){touring=false;range.value=percent.toFixed(1);tourButton.textContent="Replay motion";tourButton.setAttribute("aria-pressed","false");run();}
function selectScenario(next){
  pauseForInput(); scenario=next;
  for(const button of scenarioButtons){const selected=button.dataset.scenario===scenario;button.setAttribute("aria-pressed",String(selected));}
  if(scenario==="baseline"){percent=0;range.disabled=true;range.setAttribute("aria-disabled","true");}
  else{range.disabled=false;range.setAttribute("aria-disabled","false");}
  run();
}
for(const button of scenarioButtons)button.addEventListener("click",()=>selectScenario(button.dataset.scenario));
range.addEventListener("input",()=>{pauseForInput();percent=Number(range.value);run();});
tourButton.addEventListener("click",()=>{
  touring=tourButton.getAttribute("aria-pressed")!=="true"&&!reduced.matches;
  if(touring&&scenario==="baseline"){scenario="target";for(const button of scenarioButtons)button.setAttribute("aria-pressed",String(button.dataset.scenario===scenario));range.disabled=false;}
  tourButton.textContent=touring?"Pause motion":"Replay motion";
  tourButton.setAttribute("aria-pressed",String(touring));run();
});
new IntersectionObserver((entries)=>{visible=entries[entries.length-1].isIntersecting;if(visible)run();else{cancelAnimationFrame(frame);frame=0;}},{rootMargin:"120px 0px"}).observe(stage);
reduced.addEventListener("change",()=>{if(reduced.matches){touring=false;tourButton.textContent="Replay motion";tourButton.setAttribute("aria-pressed","false");displayedPercent=percent;redraw(percent);}else run();});
redraw(percent);
`;

const html = K.pageHtml({
  title: "Load-shift test bench · Energy Consumption Pattern Analysis",
  theme: "dark",
  width: 940,
  body: styles + plate,
  script: kitScript() + live,
});

const staticSvg = scene(
  profileAt(STUDY, "target", 10),
  "target cluster",
  10,
);

mkdirSync(OUT, { recursive: true });
mkdirSync(join(ROOT, "docs", "assets"), { recursive: true });
writeFileSync(join(OUT, "load-shift-test-rig.html"), html, "utf8");
writeFileSync(join(OUT, "load-shift-test-rig.svg"), staticSvg, "utf8");
writeFileSync(join(ROOT, "docs", "assets", "load-shift-test-rig.svg"), staticSvg, "utf8");
console.log(`Built Anatomy load-shift figure from ${STUDY.analysis.analyzed_clients} UCI clients: ${join(OUT, "load-shift-test-rig.html")}`);
