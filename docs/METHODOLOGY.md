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

- Evaluate **K = 2…10**.
- Metrics per K: inertia, silhouette, Calinski-Harabasz, Davies-Bouldin.
- Selection: multi-metric top-3 vote consensus, with **no hard-coded 3 to 6 preference**.
- Stability: multi-seed Adjusted Rand Index when enabled.
- Persist the exact fitted `KMeans` used for all downstream numbers.
- K→metric display uses **dictionary lookup** (`silhouette_by_k[k]`), never `scores[k-2]`.

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

| Exp | Features | Purpose |
|-----|----------|---------|
| A | Scale | Magnitude-dominated baseline |
| B | Behavioral | Primary scientific experiment |
| C | Combined | Interaction check |

Higher silhouette on scale does **not** override the behavioral objective; it demonstrates why feature choice changes the analytical question.
