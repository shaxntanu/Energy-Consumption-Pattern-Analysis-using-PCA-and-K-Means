import fs from "node:fs/promises";
import path from "node:path";
import { pathToFileURL } from "node:url";
import { Presentation, PresentationFile } from "@oai/artifact-tool";

const workspaceDir = process.cwd();
const SKILL_DIR = "C:/Users/Shantanu/.codex/plugins/cache/openai-primary-runtime/presentations/26.909.61513/skills/presentations";
const TMP_DIR = path.join(workspaceDir, ".codex-build", "exact-ppt");
const FINAL_PPTX = path.join(workspaceDir, "exports", "Energy_Consumption_PCA_KMeans_Final_v7.pptx");
const RUNTIME_PYTHON = "C:/Users/Shantanu/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/python.exe";
const { finalizePresentation } = await import(pathToFileURL(path.join(SKILL_DIR, "container_tools", "artifact_tool_utils.mjs")).href);
await fs.mkdir(TMP_DIR, { recursive: true });
await fs.mkdir(path.dirname(FINAL_PPTX), { recursive: true });

const presentation = Presentation.create({ slideSize: { width: 1280, height: 720 } });
for (let number = 1; number <= 20; number += 1) {
  const slide = presentation.slides.add();
  slide.background.fill = "#000000";
  const image = await fs.readFile(path.join(workspaceDir, ".codex-build", "html-slide-captures", `slide-${String(number).padStart(2, "0")}.png`));
  slide.images.add({ blob: image, contentType: "image/png", alt: `Exact HTML presentation slide ${number}`, fit: "contain", position: { left: 0, top: 0, width: 1280, height: 720 } });
  slide.speakerNotes.textFrame.setText(`Exact visual export of presentation/index.html, slide ${number}.`);
}
const candidatePath = path.join(TMP_DIR, "candidate.pptx");
await (await PresentationFile.exportPptx(presentation)).save(candidatePath);
const result = await finalizePresentation({
  explicitTotalSlideCount: 20,
  requiredNativeTableOwnerSlides: [],
  workspaceDir,
  candidatePath,
  finalPath: FINAL_PPTX,
  pythonExecutable: RUNTIME_PYTHON,
  integrityValidatorPath: path.join(SKILL_DIR, "container_tools", "inspect_presentation_package_integrity.py"),
  layoutValidatorPath: path.join(SKILL_DIR, "container_tools", "inspect_presentation_layout_geometry.py"),
  layoutArgs: ["--expected-slide-size-emu", "12192000,6858000"],
  verifyArtifactToolImport: true,
  receiptPath: path.join(TMP_DIR, "validation-final-v7.json"),
});
console.log(JSON.stringify({ final: FINAL_PPTX, result }, null, 2));
