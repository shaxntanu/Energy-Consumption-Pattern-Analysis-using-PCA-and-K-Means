import assert from "node:assert/strict";
import test from "node:test";
import { fileURLToPath } from "node:url";
import { loadStudyData, profileAt, summarizeProfile } from "./model.mjs";

const ROOT = fileURLToPath(new URL("../../../", import.meta.url));
const study = loadStudyData(ROOT);

test("the saved study has 24 ordered hours and conserves daily energy", () => {
  assert.equal(study.profiles.baseline_kw.length, 24);
  const energy = study.profiles.baseline_kw.reduce((sum, value) => sum + value, 0);
  for (const scenario of ["target", "comparator"]) {
    const profile = profileAt(study, scenario, 10);
    assert.equal(profile.length, 24);
    assert.ok(Math.abs(profile.reduce((sum, value) => sum + value, 0) - energy) < 1e-6);
  }
});

test("zero intensity is the baseline and ten percent reproduces the stored endpoints", () => {
  assert.deepEqual(profileAt(study, "target", 0), study.profiles.baseline_kw);
  assert.deepEqual(profileAt(study, "comparator", 0), study.profiles.baseline_kw);
  assert.deepEqual(profileAt(study, "target", 10), study.profiles.target_cluster_kw);
  assert.deepEqual(profileAt(study, "comparator", 10), study.profiles.equal_energy_comparator_kw);
});

test("the target readout reproduces the saved peak and evening reduction", () => {
  const profile = profileAt(study, "target", 10);
  const summary = summarizeProfile(study, profile, "target", 10);
  assert.equal(summary.peakHour, 16);
  assert.ok(Math.abs(summary.peakKw - 185212.52010800786) < 1e-6);
  assert.ok(Math.abs(summary.eveningPeakReductionPercent - 5.64) < 0.005);
  assert.ok(Math.abs(summary.shiftedKwhPerAverageDay - 39610.397) < 0.001);
});

test("invalid controls fail instead of silently changing the model", () => {
  assert.throws(() => profileAt(study, "unknown", 5), /Unknown scenario/);
  assert.throws(() => profileAt(study, "target", -0.1), RangeError);
  assert.throws(() => profileAt(study, "target", 10.1), RangeError);
});
