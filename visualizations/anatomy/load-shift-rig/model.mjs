import { readFileSync } from "node:fs";
import { join } from "node:path";

export const MAX_FLEX_PERCENT = 10;
export const SCENARIOS = Object.freeze({
  target: "target_cluster_kw",
  comparator: "equal_energy_comparator_kw",
});

function parseCsv(text) {
  const [headerLine, ...lines] = text.trim().split(/\r?\n/);
  const headers = headerLine.split(",");
  return lines.map((line) => {
    const values = line.split(",");
    return Object.fromEntries(headers.map((header, index) => [header, values[index]]));
  });
}

export function loadStudyData(root) {
  const csvPath = join(root, "outputs", "research_additions", "demand_response_uci_2012_hourly_profiles.csv");
  const jsonPath = join(root, "outputs", "research_additions", "demand_response_uci_2012.json");
  const rows = parseCsv(readFileSync(csvPath, "utf8"));
  const metadata = JSON.parse(readFileSync(jsonPath, "utf8"));
  const required = ["hour", "baseline_kw", ...Object.values(SCENARIOS)];

  if (rows.length !== 24) {
    throw new Error(`Expected 24 hourly rows, found ${rows.length}.`);
  }
  for (const [index, row] of rows.entries()) {
    if (required.some((column) => row[column] === undefined)) {
      throw new Error(`Hourly profile row ${index} is missing a required column.`);
    }
    if (Number(row.hour) !== index) {
      throw new Error(`Expected hour ${index}, found ${row.hour}.`);
    }
    if (required.slice(1).some((column) => !Number.isFinite(Number(row[column])) || Number(row[column]) < 0)) {
      throw new Error(`Hourly profile row ${index} contains an invalid demand value.`);
    }
  }

  const profiles = Object.fromEntries(required.slice(1).map((column) => [
    column,
    rows.map((row) => Number(row[column])),
  ]));
  const metrics = Object.fromEntries(metadata.scenario_metrics.map((entry) => [entry.scenario, entry]));
  const analysis = metadata.analysis;

  if (analysis.analyzed_clients !== 104 || analysis.evening_hours_local_half_open?.join(",") !== "17,21" || analysis.shift_destination_hours_local_half_open?.join(",") !== "12,17") {
    throw new Error("The saved scenario metadata no longer matches the figure's stated study scope.");
  }
  for (const [profileKey, scenarioKey] of [
    ["baseline_kw", "observed_baseline"],
    [SCENARIOS.target, "target_evening_heavy_cluster"],
    [SCENARIOS.comparator, "equal_energy_non_target_comparator"],
  ]) {
    const observedPeak = Math.max(...profiles[profileKey]);
    const recordedPeak = metrics[scenarioKey]?.aggregate_peak_kw;
    if (!Number.isFinite(recordedPeak) || Math.abs(observedPeak - recordedPeak) > 1e-6) {
      throw new Error(`Hourly profile and recorded peak disagree for ${scenarioKey}.`);
    }
  }

  const baseEnergy = profiles.baseline_kw.reduce((sum, value) => sum + value, 0);
  for (const key of Object.values(SCENARIOS)) {
    const scenarioEnergy = profiles[key].reduce((sum, value) => sum + value, 0);
    if (Math.abs(scenarioEnergy - baseEnergy) > 1e-6) {
      throw new Error(`${key} does not conserve the saved daily aggregate energy.`);
    }
  }

  return { profiles, metrics, analysis, metadata };
}

export function profileAt(study, scenario, flexPercent) {
  if (!(scenario in SCENARIOS)) throw new Error(`Unknown scenario: ${scenario}`);
  if (!Number.isFinite(flexPercent) || flexPercent < 0 || flexPercent > MAX_FLEX_PERCENT) {
    throw new RangeError(`Scenario intensity must be between 0 and ${MAX_FLEX_PERCENT}%.`);
  }
  const end = study.profiles[SCENARIOS[scenario]];
  const share = flexPercent / MAX_FLEX_PERCENT;
  return study.profiles.baseline_kw.map((start, index) => start + (end[index] - start) * share);
}

export function summarizeProfile(study, profile, scenario, flexPercent) {
  const peakKw = Math.max(...profile);
  const peakHour = profile.indexOf(peakKw);
  const eveningPeakKw = Math.max(...profile.slice(17, 21));
  const baselineEveningPeak = study.metrics.observed_baseline.evening_peak_kw;
  const baselineDailyKwh = study.metrics.observed_baseline.aggregate_daily_energy_kwh;
  const dailyKwh = profile.reduce((sum, value) => sum + value, 0);
  const shiftedAtMax = study.metrics[scenario === "target"
    ? "target_evening_heavy_cluster"
    : "equal_energy_non_target_comparator"].energy_shifted_kwh_per_average_day;

  return {
    peakKw,
    peakHour,
    eveningPeakKw,
    eveningPeakReductionPercent: 100 * (baselineEveningPeak - eveningPeakKw) / baselineEveningPeak,
    shiftedKwhPerAverageDay: shiftedAtMax * flexPercent / MAX_FLEX_PERCENT,
    dailyEnergyChangeKwh: dailyKwh - baselineDailyKwh,
  };
}
