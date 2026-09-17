import fs from "node:fs/promises";
import path from "node:path";

const workspace = process.cwd();
const outputDir = path.join(workspace, ".codex-build", "html-slide-captures");
const port = process.env.CDP_PORT ?? "9222";
await fs.mkdir(outputDir, { recursive: true });

async function sleep(ms) { await new Promise((resolve) => setTimeout(resolve, ms)); }
async function remoteTargets() {
  const response = await fetch(`http://127.0.0.1:${port}/json`);
  if (!response.ok) throw new Error(`Chrome remote debugging returned ${response.status}`);
  return response.json();
}

let targets = [];
for (let attempt = 0; attempt < 30; attempt += 1) {
  try {
    targets = await remoteTargets();
    if (targets.length) break;
  } catch { /* Chrome is still starting. */ }
  await sleep(300);
}
const target = targets.find((item) => item.type === "page" && item.url.includes("presentation/index.html"));
if (!target?.webSocketDebuggerUrl) throw new Error("Could not find the HTML presentation page in Chrome.");

const socket = new WebSocket(target.webSocketDebuggerUrl);
await new Promise((resolve, reject) => { socket.addEventListener("open", resolve, { once: true }); socket.addEventListener("error", reject, { once: true }); });
let messageId = 0;
const pending = new Map();
socket.addEventListener("message", (event) => {
  const response = JSON.parse(event.data);
  const resolver = pending.get(response.id);
  if (!resolver) return;
  pending.delete(response.id);
  response.error ? resolver.reject(new Error(response.error.message)) : resolver.resolve(response.result);
});
function cdp(method, params = {}) {
  const id = ++messageId;
  socket.send(JSON.stringify({ id, method, params }));
  return new Promise((resolve, reject) => pending.set(id, { resolve, reject }));
}

await cdp("Emulation.setDeviceMetricsOverride", { width: 1920, height: 1080, deviceScaleFactor: 1, mobile: false });
await sleep(2000);
for (let number = 1; number <= 20; number += 1) {
  const expression = `(() => {
    const n = ${number};
    window.presentation?.goToSlide(n);
    document.querySelectorAll('.slide').forEach((slide) => { slide.style.animation = 'none'; });
    return document.querySelector('.slide.active')?.dataset.slide;
  })()`;
  await cdp("Runtime.evaluate", { expression, awaitPromise: true, returnByValue: true });
  await sleep(850);
  const shot = await cdp("Page.captureScreenshot", { format: "png", captureBeyondViewport: false, fromSurface: true });
  await fs.writeFile(path.join(outputDir, `slide-${String(number).padStart(2, "0")}.png`), Buffer.from(shot.data, "base64"));
}
socket.close();
console.log(outputDir);
