# Final Report on Energy Consumption Pattern Analysis (PCA + K-Means)

## 1. Problem statement

Unsupervised discovery of consumer groups that differ in **energy-usage patterns** (timing, weekend preference, variability). PCA compresses standardized behavioral features; K-Means assigns clusters. The claim to defend: clusters reflect *how* consumers use energy, not only *how much*.

## 2. Dataset

- **Type:** Synthetic (archetype-based). Labeled in README, metadata, and dashboard.
- **Generator:** `src/data_loader.py` draws daytime, evening, flat and weekend-heavy shapes with continuous within-archetype variation.
- **Hidden ground truth:** `archetype`, validation only; **never** a K-Means feature.
- **Run config:** 200 consumers × 30 days × hourly (144,000 rows).
- **Validation:** `outputs/reports/dataset_validation_report.md` + archetype figures.

## 3. Feature engineering

Primary = **behavioral**:

| Feature | Definition |
|---------|------------|
| `hour_h_shape` | Mean energy at hour *h* / sum of 24 hourly means |
| period usage | Mean energy in morning/afternoon/evening/night bins |
| `weekend_ratio` | `mean(energy\|weekend) / mean(energy\|weekday)` |
| `peak_to_avg_ratio` | max / mean |
| `coefficient_of_variation` | std / mean |
| skewness, kurtosis | series shape |

Scale features used only in ablation.

## 4. Preprocessing

Sort `(consumer_id, timestamp)` → within-consumer fill → configurable invalid ranges → outliers logged, not removed by default. Shuffle leakage test: **pass**.

## 5. PCA

- Drop `consumer_id`; StandardScaler; retain components to **≥95%** cumulative variance.
- This run: **25** components, cumulative variance **0.967**.
- Artifacts: `models/scaler.pkl`, `pca_model.pkl`, `feature_names.txt`, `analysis_metadata.json`.

## 6. Every tested K (behavioral)

| K | Inertia | Silhouette | CH | DB |
|---|---------|------------|----|----|
| 2 | 5889.82 | **0.1055** | **16.60** | 3.291 |
| 3 | 5643.78 | 0.0478 | 12.91 | 3.359 |
| 4 | 5431.22 | 0.0384 | 11.46 | 3.302 |
| 5 | 5266.16 | 0.0411 | 10.34 | 3.179 |
| 6 | 5086.36 | 0.0401 | 9.90 | 2.950 |
| 7 | 4989.16 | 0.0386 | 8.99 | 2.966 |
| 8 | 4910.51 | 0.0341 | 8.23 | 2.895 |
| 9 | 4814.96 | 0.0376 | 7.78 | 2.822 |
| 10 | 4760.85 | 0.0353 | 7.20 | 2.805 |

**Selected K = 2** (multi-metric consensus; no hard-coded 3 to 6 preference).  
**Stability:** mean ARI **0.791 ± 0.111** (10 seeds).

## 7. Final clusters (original feature space)

| Cluster | Name | n | % | Mean kWh | Peak/Avg | CV | Weekend ratio |
|---------|------|---|---|----------|----------|-----|---------------|
| 0 | Afternoon-Peak High-Variability | 135 | 67.5% | 0.0714 | 7.11 | 1.07 | 0.952 |
| 1 | Weekend-Oriented Spiky-Variable | 65 | 32.5% | 0.0767 | 10.64 | 1.32 | **1.196** |

Weekend ratios now **differ** (baseline was ~0.267 for all clusters).

## 8. Recommendations

Evidence-triggered only (`outputs/reports/recommendations_report.md`). Example triggers: elevated peak-to-average and CV. No guaranteed savings / causality claims.

## 9. Ablation conclusion

| Set | Silhouette | ARI | Role |
|-----|------------|-----|------|
| scale | 0.354 | 1.00 | Magnitude control (looks “better”) |
| behavioral | 0.105 | 0.79 | **Primary** |
| combined | 0.104 | 1.00 | Mixed control |

**Feature engineering changed the question** from “who consumes more?” to “how do consumers consume differently?” Primary experiment = behavioral.

## 10. Limitations

1. Synthetic data limits external validity.  
2. Behavioral silhouette **weak (~0.11)**, reported honestly.  
3. Clustering ≠ causation.  
4. Results depend on feature definitions and 95% PCA threshold.  
5. Single synthetic window, so no seasonal claim is made.  
6. Dashboard and offline pipeline share one analysis object (config-hash invalidation).

## 11. Reproducibility

Pinned in `requirements.txt`. Tests: `py -m pytest tests/ -v` → **18 passed**.  
Metadata: `models/analysis_metadata.json`. Baseline frozen: `baseline/`.

## 12. Done

All Definition-of-Done items satisfied. Package index: `docs/DELIVERABLES.md`.
