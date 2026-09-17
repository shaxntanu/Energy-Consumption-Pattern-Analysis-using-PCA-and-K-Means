import fs from "node:fs/promises";
import path from "node:path";
import { pathToFileURL } from "node:url";
import { Presentation, PresentationFile } from "@oai/artifact-tool";

const workspaceDir = process.cwd();
const SKILL_DIR = "C:/Users/Shantanu/.codex/plugins/cache/openai-primary-runtime/presentations/26.909.61513/skills/presentations";
const TMP_DIR = path.join(workspaceDir, ".codex-build", "ppt-export");
const FINAL_PPTX = path.join(workspaceDir, "exports", "Energy_Consumption_Pattern_Analysis_PCA_KMeans.pptx");
const RUNTIME_PYTHON = "C:/Users/Shantanu/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/python.exe";
const { resolvePresentationFont, finalizePresentation } = await import(
  pathToFileURL(path.join(SKILL_DIR, "container_tools", "artifact_tool_utils.mjs")).href,
);

await fs.mkdir(TMP_DIR, { recursive: true });
await fs.mkdir(path.dirname(FINAL_PPTX), { recursive: true });

const family = resolvePresentationFont();
const ppt = Presentation.create({ slideSize: { width: 1280, height: 720 } });

const C = {
  bg: "#000000", panel: "#111827", line: "#263244", ink: "#F8FAFC",
  mist: "#D4DCE8", slate: "#8A93A6", blue: "#6C8CFF", cyan: "#3BC9DE",
  green: "#4FD1A5", amber: "#F5A524", violet: "#B085F5", red: "#FF6B6B",
};

function addText(slide, value, position, style = {}) {
  const shape = slide.shapes.add({
    geometry: "textbox", position, fill: "none", line: { fill: "none", width: 0 },
  });
  shape.text = value;
  shape.text.style = { typeface: family, fontSize: 18, color: C.mist, autoFit: "shrinkText", ...style };
  return shape;
}

function addCard(slide, position, accent = null) {
  const card = slide.shapes.add({
    geometry: "roundRect", position,
    fill: { color: C.panel }, line: { fill: accent ?? C.line, width: accent ? 2 : 1 },
  });
  return card;
}

async function addFigure(slide, filename, position, alt) {
  const bytes = await fs.readFile(path.join(workspaceDir, "dark_mode_plots", "figures", filename));
  slide.images.add({ blob: bytes, contentType: "image/png", alt, fit: "contain", position });
}

function chrome(slide, number, label, source) {
  slide.background.fill = C.bg;
  addText(slide, label.toUpperCase(), { left: 58, top: 28, width: 850, height: 23 }, {
    fontSize: 12, color: C.cyan, bold: true, characterSpacing: 1,
  });
  addText(slide, `SUNEE   /   ${String(number).padStart(2, "0")}`, { left: 1040, top: 29, width: 180, height: 22 }, {
    fontSize: 11, color: C.slate, bold: true, alignment: "right", characterSpacing: 0,
  });
  const rule = slide.shapes.add({
    geometry: "rect", position: { left: 58, top: 677, width: 1164, height: 1 }, fill: { color: C.line }, line: { fill: "none", width: 0 },
  });
  addText(slide, source, { left: 58, top: 686, width: 1040, height: 18 }, { fontSize: 9, color: C.slate });
  slide.speakerNotes.textFrame.setText(source);
  return rule;
}

function title(slide, text) {
  addText(slide, text, { left: 58, top: 66, width: 1110, height: 92 }, {
    fontSize: 38, color: C.ink, bold: true, typeface: family, autoFit: "shrinkText",
  });
}

function addTable(slide, values, position, widths, highlights = []) {
  const table = slide.tables.add({ rows: values.length, columns: values[0].length, values, ...position, columnWidths: widths });
  table.styleOptions = { headerRow: true, bandedRows: true };
  table.borders.assign({ style: "solid", fill: C.line, width: 1 });
  table.cells.block({ row: 0, column: 0, rowCount: 1, columnCount: values[0].length }).assign({
    fill: C.panel, textStyle: { typeface: family, fontSize: 13, color: C.ink, bold: true },
  });
  table.cells.block({ row: 1, column: 0, rowCount: values.length - 1, columnCount: values[0].length }).assign({
    fill: "#090F1A", textStyle: { typeface: family, fontSize: 12, color: C.mist },
  });
  highlights.forEach(({ row, col, color = C.green }) => {
    table.getCell(row, col).text.style = { typeface: family, fontSize: 12, color, bold: true };
  });
  return table;
}

// 1. Cover
{
  const slide = ppt.slides.add();
  slide.background.fill = C.bg;
  addText(slide, "ENERGY CONSUMPTION PATTERN ANALYSIS", { left: 72, top: 62, width: 600, height: 24 }, { fontSize: 13, color: C.cyan, bold: true, characterSpacing: 1 });
  addText(slide, "Grouped by when a home uses power, not how much.", { left: 72, top: 146, width: 925, height: 185 }, { fontSize: 52, color: C.ink, bold: true });
  addText(slide, "A shape-first clustering pipeline for residential energy: 200 synthetic consumers, four hidden archetypes, and one real weather feed.", { left: 76, top: 355, width: 820, height: 68 }, { fontSize: 21, color: C.mist });
  addText(slide, "200 consumers  •  365 days  •  1,752,000 records  •  51 features  •  K = 4", { left: 76, top: 499, width: 930, height: 32 }, { fontSize: 15, color: C.green, bold: true });
  addText(slide, "Flagship config 99c7a6631340d301", { left: 76, top: 548, width: 430, height: 26 }, { fontSize: 13, color: C.slate });
  await addFigure(slide, "hourly_patterns.png", { left: 882, top: 145, width: 310, height: 352 }, "Normalized cluster load profiles");
  slide.speakerNotes.textFrame.setText("Source: presentation/index.html; flagship results in web/public/data/*.json.");
}

// 2. Premise
{
  const slide = ppt.slides.add(); chrome(slide, 2, "01 / Why shape", "Source: conceptual premise in presentation/index.html; real profiles in web/public/data/profiles.json"); title(slide, "Two homes can share a bill and share nothing else.");
  addCard(slide, { left: 58, top: 180, width: 430, height: 380 }, C.cyan);
  addText(slide, "Same daily total", { left: 94, top: 220, width: 320, height: 34 }, { fontSize: 25, color: C.cyan, bold: true });
  addText(slide, "A bill compresses 24 hours into one number. It cannot distinguish a morning peak from an evening peak.", { left: 94, top: 278, width: 335, height: 118 }, { fontSize: 23, color: C.mist });
  addText(slide, "The model therefore groups households by the normalized shape of a day, not by raw consumption.", { left: 94, top: 440, width: 335, height: 75 }, { fontSize: 17, color: C.green, bold: true });
  await addFigure(slide, "hourly_patterns.png", { left: 530, top: 176, width: 650, height: 392 }, "Matplotlib plot of normalized 24-hour cluster profiles");
}

// 3. Timing descriptors
{
  const slide = ppt.slides.add(); chrome(slide, 3, "01 / Why shape", "Source: web/public/data/profiles.json; presentation/index.html slide 3"); title(slide, "Timing tells a utility what magnitude alone cannot.");
  addTable(slide, [
    ["Feature", "Population", "Midday", "Flat", "Evening", "Evening + weekend"],
    ["Evening share", "0.29", "0.24", "0.26", "0.40", "0.36"],
    ["Peak-to-average", "1.58", "1.63", "1.31", "1.88", "1.59"],
    ["Weekend ratio", "1.04", "1.06", "0.99", "1.03", "1.14"],
  ], { left: 58, top: 190, width: 1164, height: 265 }, [245, 150, 150, 150, 150, 180], [{ row: 1, col: 4, color: C.violet }, { row: 1, col: 5 }, { row: 2, col: 4, color: C.violet }, { row: 3, col: 5 }]);
  addText(slide, "The evening cluster spends 40% of its day in the 18:00–24:00 window. The flat cluster spends about 26%, even when total consumption overlaps.", { left: 80, top: 510, width: 1070, height: 55 }, { fontSize: 20, color: C.mist });
}

// 4. Dataset
{
  const slide = ppt.slides.add(); chrome(slide, 4, "02 / Dataset", "Source: RESULTS.md; docs/verification.md; models/analysis_metadata.json"); title(slide, "200 consumers, four hidden rhythms, one real weather feed.");
  addTable(slide, [["Dataset property", "Flagship value"], ["Consumers", "200"], ["Days", "365 across four seasons"], ["Hourly records", "1,752,000"], ["Hidden archetypes", "4"], ["Behavioural features", "51"], ["Config hash", "99c7a6631340d301"]], { left: 58, top: 180, width: 490, height: 400 }, [250, 240], [{ row: 1, col: 1 }, { row: 2, col: 1 }, { row: 3, col: 1 }, { row: 4, col: 1 }, { row: 5, col: 1 }]);
  addCard(slide, { left: 590, top: 180, width: 632, height: 400 }, C.blue);
  addText(slide, "Zephyr weather provenance", { left: 625, top: 218, width: 450, height: 32 }, { fontSize: 24, color: C.cyan, bold: true });
  addText(slide, "Hourly weather comes from the recorded Zephyr Station feed. The simulation includes seasonal amplitude and timing shifts without letting the hidden synthetic truth enter the model.", { left: 625, top: 270, width: 525, height: 100 }, { fontSize: 19, color: C.mist });
  addText(slide, "Real-world adapter", { left: 625, top: 420, width: 400, height: 30 }, { fontSize: 24, color: C.green, bold: true });
  addText(slide, "The separate Case A pathway processes 24 audited meters with the same ingestion report format and only internal metrics.", { left: 625, top: 470, width: 525, height: 65 }, { fontSize: 19, color: C.mist });
}

// 5. Pipeline
{
  const slide = ppt.slides.add(); chrome(slide, 5, "03 / Method", "Source: presentation/index.html slide 5; README.md methodology"); title(slide, "One deterministic path from meter to validated cluster.");
  const steps = ["Generate panel", "Validate + preprocess", "Engineer 51 features", "Standardize + PCA", "Select K = 4", "Profile + explain", "Validate + export"];
  steps.forEach((step, i) => {
    const left = 55 + i * 166;
    addCard(slide, { left, top: 275, width: 142, height: 124 }, [C.cyan, C.blue, C.violet, C.amber, C.green][i % 5]);
    addText(slide, String(i + 1).padStart(2, "0"), { left: left + 18, top: 294, width: 44, height: 22 }, { fontSize: 13, color: C.slate, bold: true });
    addText(slide, step, { left: left + 18, top: 330, width: 106, height: 44 }, { fontSize: 17, color: C.ink, bold: true });
    if (i < steps.length - 1) addText(slide, "→", { left: left + 144, top: 319, width: 26, height: 30 }, { fontSize: 22, color: C.slate, alignment: "center" });
  });
  addText(slide, "Leakage boundary: archetype and seasonal-phase labels are removed before preprocessing. They return only for independent validation.", { left: 80, top: 490, width: 1120, height: 52 }, { fontSize: 21, color: C.mist, alignment: "center" });
}

// 6. Leakage
{
  const slide = ppt.slides.add(); chrome(slide, 6, "03 / Method", "Source: README.md section 5; presentation/index.html slide 6"); title(slide, "The answer key never reaches the model.");
  addCard(slide, { left: 60, top: 190, width: 525, height: 340 }, C.red);
  addText(slide, "Excluded before analysis", { left: 95, top: 225, width: 390, height: 34 }, { fontSize: 25, color: C.red, bold: true });
  addText(slide, "Hidden archetype\nSeasonal phase\nSynthetic generation details", { left: 95, top: 286, width: 355, height: 160 }, { fontSize: 25, color: C.mist, bold: true });
  addCard(slide, { left: 650, top: 190, width: 525, height: 340 }, C.green);
  addText(slide, "Used by the model", { left: 685, top: 225, width: 390, height: 34 }, { fontSize: 25, color: C.green, bold: true });
  addText(slide, "Hourly energy profiles\nSeason label\n51 behavioural features", { left: 685, top: 286, width: 355, height: 160 }, { fontSize: 25, color: C.mist, bold: true });
  addText(slide, "Validation compares recovered groups with hidden archetypes only after clustering finishes.", { left: 170, top: 580, width: 940, height: 35 }, { fontSize: 20, color: C.slate, alignment: "center" });
}

// 7. Features
{
  const slide = ppt.slides.add(); chrome(slide, 7, "03 / Method", "Source: README.md section 6; outputs/metrics/pca_loadings.csv"); title(slide, "51 features, not one of them is size.");
  addCard(slide, { left: 58, top: 190, width: 300, height: 290 }, C.cyan);
  addText(slide, "24", { left: 94, top: 224, width: 150, height: 70 }, { fontSize: 54, color: C.cyan, bold: true });
  addText(slide, "hourly shape bins", { left: 94, top: 305, width: 200, height: 32 }, { fontSize: 22, color: C.ink, bold: true });
  addText(slide, "Daily load curve divided by its own mean", { left: 94, top: 360, width: 210, height: 65 }, { fontSize: 16, color: C.mist });
  addCard(slide, { left: 400, top: 190, width: 300, height: 290 }, C.violet);
  addText(slide, "27", { left: 436, top: 224, width: 150, height: 70 }, { fontSize: 54, color: C.violet, bold: true });
  addText(slide, "summary descriptors", { left: 436, top: 305, width: 230, height: 32 }, { fontSize: 22, color: C.ink, bold: true });
  addText(slide, "Timing, spikiness, weekend behaviour, dispersion", { left: 436, top: 360, width: 220, height: 65 }, { fontSize: 16, color: C.mist });
  await addFigure(slide, "component_loadings.png", { left: 748, top: 178, width: 455, height: 330 }, "Matplotlib heatmap of PCA component loadings");
  addText(slide, "Scale diagnostics remain separate from the 51 behavioural features used for clustering.", { left: 80, top: 552, width: 1100, height: 30 }, { fontSize: 18, color: C.slate, alignment: "center" });
}

// 8. PCA loading chart
{
  const slide = ppt.slides.add(); chrome(slide, 8, "03 / Method", "Source: web/public/data/pca.json; dark_mode_plots/figures/component_loadings.png"); title(slide, "51 correlated numbers collapse into 10 that matter.");
  await addFigure(slide, "component_loadings.png", { left: 58, top: 168, width: 650, height: 430 }, "Matplotlib heatmap of PCA component loadings");
  addCard(slide, { left: 750, top: 190, width: 445, height: 360 }, C.blue);
  addText(slide, "What the first components capture", { left: 785, top: 220, width: 350, height: 34 }, { fontSize: 22, color: C.cyan, bold: true });
  addText(slide, "PC1  Peak concentration and ramp\nPC2  Night versus afternoon use\nPC3  Morning shape\nPC4  Evening timing\nPC5  Weekend and fine-scale variation", { left: 785, top: 285, width: 355, height: 190 }, { fontSize: 19, color: C.mist });
}

// 9. Explained variance
{
  const slide = ppt.slides.add(); chrome(slide, 9, "03 / Method", "Source: web/public/data/pca.json; dark_mode_plots/figures/explained_variance.png"); title(slide, "10 components hold 95.05 percent of the variance.");
  await addFigure(slide, "explained_variance.png", { left: 70, top: 175, width: 710, height: 395 }, "Matplotlib explained variance curve");
  addCard(slide, { left: 830, top: 205, width: 325, height: 290 }, C.green);
  addText(slide, "95.05%", { left: 870, top: 245, width: 250, height: 70 }, { fontSize: 46, color: C.green, bold: true, alignment: "center" });
  addText(slide, "variance retained\nwith 10 PCA components", { left: 875, top: 335, width: 240, height: 72 }, { fontSize: 21, color: C.ink, bold: true, alignment: "center" });
  addText(slide, "Kaiser and scree comparisons both indicate 7 components, but the variance threshold drives the pipeline.", { left: 840, top: 525, width: 305, height: 65 }, { fontSize: 16, color: C.slate, alignment: "center" });
}

// 10. K selection
{
  const slide = ppt.slides.add(); chrome(slide, 10, "03 / Method", "Source: web/public/data/clustering.json; dark_mode_plots/figures/k_selection_metrics.png"); title(slide, "K is picked by a rule fixed in advance, not by eye.");
  await addFigure(slide, "k_selection_metrics.png", { left: 55, top: 170, width: 650, height: 420 }, "Matplotlib K-selection metrics chart");
  addCard(slide, { left: 755, top: 190, width: 430, height: 360 }, C.amber);
  addText(slide, "Composite selection rule", { left: 795, top: 220, width: 320, height: 34 }, { fontSize: 24, color: C.amber, bold: true });
  addText(slide, "1. Score silhouette, Calinski–Harabasz, and inverted Davies–Bouldin\n\n2. Average normalized scores\n\n3. Apply a 5% parsimony tolerance band\n\n4. Select the smallest eligible K", { left: 795, top: 280, width: 330, height: 220 }, { fontSize: 18, color: C.mist });
}

// 11. Silhouette trade-off
{
  const slide = ppt.slides.add(); chrome(slide, 11, "03 / Method", "Source: web/public/data/clustering.json; dark_mode_plots/figures/silhouette_scores.png"); title(slide, "Silhouette peaks at K = 5; the rule says K = 4.");
  await addFigure(slide, "silhouette_scores.png", { left: 58, top: 173, width: 680, height: 400 }, "Matplotlib silhouette score chart");
  addCard(slide, { left: 790, top: 205, width: 350, height: 275 }, C.green);
  addText(slide, "K = 4", { left: 830, top: 245, width: 270, height: 62 }, { fontSize: 46, color: C.green, bold: true, alignment: "center" });
  addText(slide, "selected by the composite rule\nSilhouette: 0.3283\nStability ARI: 0.9947", { left: 830, top: 335, width: 270, height: 86 }, { fontSize: 19, color: C.mist, alignment: "center" });
  addText(slide, "K = 5 achieves the highest standalone silhouette (0.3352) but loses the broader evidence test.", { left: 770, top: 525, width: 400, height: 48 }, { fontSize: 17, color: C.slate, alignment: "center" });
}

// 12. Profiles
{
  const slide = ppt.slides.add(); chrome(slide, 12, "04 / Results", "Source: web/public/data/profiles.json; dark_mode_plots/figures/hourly_patterns.png"); title(slide, "Four rhythms of a day.");
  await addFigure(slide, "hourly_patterns.png", { left: 55, top: 170, width: 735, height: 420 }, "Matplotlib 24-hour normalized load profiles by cluster");
  addCard(slide, { left: 835, top: 190, width: 350, height: 360 }, C.cyan);
  addText(slide, "Recovered profiles", { left: 875, top: 220, width: 250, height: 32 }, { fontSize: 24, color: C.cyan, bold: true });
  addText(slide, "0  Midday\n1  Flat\n2  Evening\n3  Evening + weekend", { left: 875, top: 290, width: 250, height: 150 }, { fontSize: 24, color: C.ink, bold: true });
  addText(slide, "Cluster sizes: 39, 52, 47, and 62 consumers", { left: 875, top: 470, width: 250, height: 40 }, { fontSize: 16, color: C.slate });
}

// 13. Recovery
{
  const slide = ppt.slides.add(); chrome(slide, 13, "04 / Results", "Source: web/public/data/validation.json; dark_mode_plots/figures/archetype_recovery.png and archetype_crosstab.png"); title(slide, "Recovery peaks exactly where the rule landed.");
  await addFigure(slide, "archetype_recovery.png", { left: 55, top: 180, width: 560, height: 350 }, "Matplotlib ARI and NMI recovery by K");
  await addFigure(slide, "archetype_crosstab.png", { left: 630, top: 180, width: 560, height: 350 }, "Matplotlib crosstab of recovered clusters and hidden archetypes");
  addText(slide, "At K = 4: ARI 0.813 and NMI 0.833. The independent recovery check agrees with the fixed selection rule.", { left: 120, top: 565, width: 1040, height: 34 }, { fontSize: 20, color: C.green, bold: true, alignment: "center" });
}

// 14. SHAP
{
  const slide = ppt.slides.add(); chrome(slide, 14, "04 / Results", "Source: web/public/data/explainability.json; dark_mode_plots/figures/shap_cluster_importance.png"); title(slide, "SHAP says which hours separate the groups.");
  await addFigure(slide, "shap_cluster_importance.png", { left: 55, top: 175, width: 690, height: 400 }, "Matplotlib SHAP feature importance per cluster");
  addCard(slide, { left: 795, top: 208, width: 350, height: 285 }, C.violet);
  addText(slide, "Post-hoc explanation", { left: 835, top: 242, width: 280, height: 32 }, { fontSize: 24, color: C.violet, bold: true });
  addText(slide, "A 98.5% surrogate predicts the cluster labels. SHAP ranks the features that best reproduce the partition, without claiming causality.", { left: 835, top: 310, width: 260, height: 120 }, { fontSize: 19, color: C.mist });
}

// 15. Seasonality
{
  const slide = ppt.slides.add(); chrome(slide, 15, "04 / Results", "Source: web/public/data/seasonal.json; dark_mode_plots seasonal figures"); title(slide, "A 25 percent seasonal swing, the same four groups underneath.");
  await addFigure(slide, "seasonal_mean_shape_by_season.png", { left: 55, top: 180, width: 560, height: 350 }, "Matplotlib seasonal mean load-shape plot");
  await addFigure(slide, "seasonal_daily_energy_and_peak_hour.png", { left: 640, top: 180, width: 560, height: 350 }, "Matplotlib seasonal energy and peak-hour plot");
  addText(slide, "Seasonality changes energy magnitude and timing, while the recovered shape groups remain visible across the year.", { left: 100, top: 565, width: 1080, height: 35 }, { fontSize: 20, color: C.mist, alignment: "center" });
}

// 16. Longitudinal
{
  const slide = ppt.slides.add(); chrome(slide, 16, "04 / Results", "Source: web/public/data/longitudinal.json; dark_mode_plots/figures/longitudinal_cluster_stability.png"); title(slide, "Mean agreement 0.88 across four quarters.");
  await addFigure(slide, "longitudinal_cluster_stability.png", { left: 65, top: 175, width: 690, height: 405 }, "Matplotlib longitudinal cluster stability chart");
  addCard(slide, { left: 820, top: 210, width: 315, height: 275 }, C.green);
  addText(slide, "0.882", { left: 855, top: 245, width: 245, height: 65 }, { fontSize: 47, color: C.green, bold: true, alignment: "center" });
  addText(slide, "mean quarterly ARI\nversus the full-year partition", { left: 865, top: 335, width: 225, height: 62 }, { fontSize: 19, color: C.ink, bold: true, alignment: "center" });
}

// 17. SDG
{
  const slide = ppt.slides.add(); chrome(slide, 17, "04 / Results", "Source: README.md section 22.5; presentation/index.html slide 17"); title(slide, "Five UN Sustainable Development Goals, ranked by directness.");
  const sdgs = [
    ["SDG 7", "Affordable and Clean Energy", "Primary", C.green],
    ["SDG 9", "Industry and Innovation", "Supported", C.cyan],
    ["SDG 12", "Responsible Consumption", "Supported", C.blue],
    ["SDG 11", "Sustainable Cities", "Indirect", C.violet],
    ["SDG 13", "Climate Action", "Indirect", C.amber],
  ];
  sdgs.forEach(([code, name, tier, color], i) => {
    const y = 180 + i * 77;
    addCard(slide, { left: 85, top: y, width: 1090, height: 58 }, color);
    addText(slide, code, { left: 110, top: y + 15, width: 90, height: 24 }, { fontSize: 19, color, bold: true });
    addText(slide, name, { left: 230, top: y + 15, width: 540, height: 24 }, { fontSize: 19, color: C.ink, bold: true });
    addText(slide, tier, { left: 900, top: y + 15, width: 230, height: 24 }, { fontSize: 18, color: C.mist, alignment: "right" });
  });
}

// 18. Delivery and benchmark
{
  const slide = ppt.slides.add(); chrome(slide, 18, "05 / Delivery", "Source: web/public/data/benchmark.json; README.md C++ engine section"); title(slide, "Same method, two apps, one optional native kernel.");
  addCard(slide, { left: 58, top: 180, width: 410, height: 375 }, C.blue);
  addText(slide, "Delivery", { left: 95, top: 215, width: 220, height: 30 }, { fontSize: 25, color: C.cyan, bold: true });
  addText(slide, "Streamlit dashboard\nMidnight canvas\n\nVercel explorer\nContract-driven UI\n\nOptional C++ kernel\nSame analysis contracts", { left: 95, top: 275, width: 280, height: 225 }, { fontSize: 20, color: C.mist });
  addTable(slide, [["Stage", "Flagship", "Medium", "Wide"], ["K-Means", "5.60×", "6.45×", "—"], ["PCA", "0.66×", "0.77×", "0.29×"], ["End to end", "1.32×", "—", "—"]], { left: 520, top: 195, width: 665, height: 245 }, [215, 150, 150, 150], [{ row: 1, col: 1 }, { row: 1, col: 2 }, { row: 3, col: 1 }]);
  addText(slide, "C++ accelerates K-Means on these shapes. Python and scikit-learn remain the scientific reference; the deck reports slower PCA results too.", { left: 540, top: 490, width: 610, height: 55 }, { fontSize: 18, color: C.slate, alignment: "center" });
}

// 19. Limitations
{
  const slide = ppt.slides.add(); chrome(slide, 19, "05 / Limitations", "Source: RESULTS.md runs 1 and 2; docs/verification.md"); title(slide, "A 30-day window already broke this rule once.");
  addTable(slide, [["Step", "30 days", "365 days"], ["Selected K", "3", "4"], ["ARI vs archetypes", "0.585", "0.813"], ["Seasonal analysis", "Unavailable", "Amplitude 0.202"], ["Longitudinal analysis", "Not run", "Mean ARI 0.882"]], { left: 58, top: 190, width: 585, height: 310 }, [215, 185, 185], [{ row: 1, col: 2, color: C.amber }, { row: 2, col: 2 }, { row: 4, col: 2 }]);
  addCard(slide, { left: 705, top: 190, width: 480, height: 310 }, C.red);
  addText(slide, "Honesty notes", { left: 745, top: 220, width: 300, height: 32 }, { fontSize: 25, color: C.red, bold: true });
  addText(slide, "Synthetic truth validates the method, not real meters.\n\nSHAP explains the surrogate, not causality.\n\nThe real-data pathway reports only internal metrics.", { left: 745, top: 280, width: 365, height: 180 }, { fontSize: 19, color: C.mist });
}

// 20. Conclusion
{
  const slide = ppt.slides.add(); chrome(slide, 20, "05 / Takeaway", "Source: RESULTS.md sections 4 and 6; presentation/index.html slide 20"); title(slide, "The shape of a day is real, recoverable, and modestly separated.");
  addCard(slide, { left: 70, top: 200, width: 510, height: 250 }, C.green);
  addText(slide, "What was shown", { left: 108, top: 235, width: 300, height: 32 }, { fontSize: 25, color: C.green, bold: true });
  addText(slide, "K = 4 by a fixed rule. ARI 0.813 at the selected K. Four rhythms remain visible through seasonal variation and quarterly re-runs.", { left: 108, top: 295, width: 395, height: 104 }, { fontSize: 21, color: C.mist });
  addCard(slide, { left: 700, top: 200, width: 510, height: 250 }, C.cyan);
  addText(slide, "What was not claimed", { left: 738, top: 235, width: 360, height: 32 }, { fontSize: 25, color: C.cyan, bold: true });
  addText(slide, "Causality, universality, or a production estimate. The separation is modest, the data is synthetic, and short windows change the result.", { left: 738, top: 295, width: 395, height: 104 }, { fontSize: 21, color: C.mist });
  addText(slide, "Reproduce: py run_module.py energy_analysis -- --n_days 365 --n_consumers 200", { left: 120, top: 545, width: 1040, height: 32 }, { fontSize: 18, color: C.slate, alignment: "center" });
}

const candidatePath = path.join(TMP_DIR, "candidate.pptx");
await (await PresentationFile.exportPptx(ppt)).save(candidatePath);

const result = await finalizePresentation({
  explicitTotalSlideCount: 20,
  requiredNativeTableOwnerSlides: [3, 4, 18, 19],
  workspaceDir,
  candidatePath,
  finalPath: FINAL_PPTX,
  pythonExecutable: RUNTIME_PYTHON,
  integrityValidatorPath: path.join(SKILL_DIR, "container_tools", "inspect_presentation_package_integrity.py"),
  layoutValidatorPath: path.join(SKILL_DIR, "container_tools", "inspect_presentation_layout_geometry.py"),
  layoutArgs: ["--expected-slide-size-emu", "12192000,6858000", "--validate-bullet-geometry", "--validate-heading-fit", "--require-native-table-slide", "3", "--require-native-table-slide", "4", "--require-native-table-slide", "18", "--require-native-table-slide", "19"],
  fontPolicy: { basis: "design", families: [family] },
  verifyArtifactToolImport: true,
  receiptPath: path.join(TMP_DIR, "validation.json"),
});

console.log(JSON.stringify({ final: FINAL_PPTX, result }, null, 2));
