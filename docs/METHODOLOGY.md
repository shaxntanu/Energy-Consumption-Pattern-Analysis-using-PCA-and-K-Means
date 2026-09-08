# Methodology Notes

## Problem statement

Segment electricity consumers by **behavioral usage patterns** (timing, weekend preference, variability), using PCA + K-Means. Magnitude-only splits are insufficient for the project claim.

## Dataset

| Field | Value |
|-------|-------|
| Source | **Synthetic** (archetype-based generator in `src/data_loader.py`) |
| Archetypes | daytime-heavy, evening-heavy, flat/industrial-like, weekend-heavy |
| Hidden label | `archetype`, validation only; never a K-Means feature |
| Typical run | 200 consumers × 30 days × hourly |

Generation pipeline per consumer: latent archetype → 24h template → amplitude → peak-timing/shape perturbation → weekday/weekend modifier → noise/spikes → optional weather from **timestamp** (shared across consumers at the same clock time).

See `outputs/reports/dataset_validation_report.md`.

## Preprocessing

```
schema → timestamp parse → sort(consumer_id, timestamp)
  → duplicates → invalid-range flag (configurable)
  → within-consumer ffill/bfill → outlier detect (default: keep peaks)
```

- No global forward-fill across the full table.
- Measurement errors (impossible negatives/ranges) vs behavioral extremes are separated.
- Valid ranges live in `detect_invalid_values(column_ranges=...)`.

## Feature engineering

Three groups:

| Group | Examples | Role |
|-------|----------|------|
| **A Behavioral shape** | `hour_0_shape`…`hour_23_shape`, morning/afternoon/evening/night usage | Primary clustering |
| **B Variability/timing** | peak-to-average, CV, skewness, kurtosis | Primary with A |
| **C Scale/context** | mean/max/sum energy, electrical means | Secondary / ablation only |

**Weekend definition (documented):**

```
weekend_ratio = mean(energy | weekend) / mean(energy | weekday)
```

Normalized load shape:

```
normalized_profile[h] = mean_hourly_energy[h] / sum_h mean_hourly_energy[h]
```

so consumers with different totals can share a cluster if timing matches.

## PCA

1. Drop identifiers (`consumer_id`).
2. StandardScaler on the modeling matrix.
3. Fit full PCA; retain components until cumulative explained variance ≥ **95%** (documented threshold).
4. Persist scaler, PCA, `feature_names.txt`, metrics CSV, and `analysis_metadata.json`.

Loadings are interpreted descriptively only; signs are not causal.

## K-Means

<<<<<<< Updated upstream
- Evaluate **K = 2…10**.
- Metrics per K: inertia, silhouette, Calinski-Harabasz, Davies-Bouldin.
- Selection: multi-metric top-3 vote consensus, with **no hard-coded 3 to 6 preference**.
- Stability: multi-seed Adjusted Rand Index when enabled.
=======
Candidate **K = 2…10**. For each K the pipeline records inertia, silhouette, Calinski-Harabasz, Davies-Bouldin, and stability across random restarts. The selection rule is fixed in advance and never sees the hidden archetype labels:

1. Discard any K whose smallest cluster holds less than 5% of consumers (`MIN_CLUSTER_SHARE = 0.05`) - isolating a handful of outliers is not a segmentation.
2. Discard any K whose mean pairwise Adjusted Rand Index across restarts falls below 0.60 (`MIN_STABILITY_ARI = 0.60`) - an unstable partition is not a finding.
3. Combine silhouette, Calinski-Harabasz and Davies-Bouldin (the last negated, so lower is better) into one composite by min-max normalizing each across the surviving candidates.
4. Among candidates within 0.05 of the best composite (`SCORE_TOLERANCE`), take the smallest K, so two indistinguishable solutions resolve to the simpler one.

If every candidate fails a filter, the filter is relaxed and the relaxation is logged, so a weak result is reported rather than silently invented. There is **no** preference for any particular K. The inertia elbow is computed and reported for comparison only; it does not drive the choice.

- On the shipped run this selects **K = 3** (the elbow suggests 4; K in 6…10 are rejected for leaving a sub-5% cluster). See `outputs/reports/analysis_summary.md`.
>>>>>>> Stashed changes
- Persist the exact fitted `KMeans` used for all downstream numbers.
- K-to-metric display uses **dictionary lookup** (`silhouette_by_k[k]`), never `scores[k-2]`.

## Profiling & recommendations

Profiles use **original feature space** (mean/median-oriented fields where available), population baselines, and behavior-derived names.

Recommendations follow:

```
Observation → Trigger metric → Observed value → Population baseline → Suggested action
```

No universal “add smart meters / renewables” spam; no guaranteed savings claims.

## Dashboard

One `AnalysisResults` object from `EnergyAnalysis`. Sidebar parameter changes recompute via `config_hash` and clear stale session keys. Pages never fit a separate PCA for evaluation display.

## Ablation

Five feature sets are run on the same data, the same seed and the same K-selection rule, so the only thing that varies is which columns go in:

| Arm | Features | Count | Purpose |
|-----|----------|-------|---------|
| scale | magnitude summaries | 7 | Magnitude-dominated control |
| shape | normalized 24-hour profile only | 24 | Timing alone |
| summary | scalars derived from the profile | 27 | Timing without the raw profile |
| behavioral | shape + summary (the shipped set) | 51 | Primary scientific experiment |
| combined | behaviour + magnitude | 58 | Interaction check |

Higher silhouette on scale does **not** override the behavioral objective. The scale arm scores best on silhouette (0.52) yet its agreement with the hidden archetypes is zero (ARI -0.004) - exactly the case the rule was written to resist. On a single draw the rule can land on `shape`; the feature set is fixed from a 20-dataset seed-robustness study that selects `behavioral` on the pooled evidence. See `outputs/reports/ablation_study_report.md` and `outputs/reports/seed_robustness_report.md`.
