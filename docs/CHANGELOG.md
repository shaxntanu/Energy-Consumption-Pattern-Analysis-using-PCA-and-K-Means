# Change Log: Remediation Fixes

One entry per material fix. Baseline artifacts remain under `baseline/`.

---

### 1. Shared temporal shape (magnitude-only latent structure)
- **Problem:** All consumers shared one 24h / weekend pattern; base load drove separation.
- **Old behavior:** Single `time_factor` × per-consumer base consumption.
- **New behavior:** Four archetypes with amplitude, peak-timing, shape, weekend modifiers, noise.
- **Why changed:** Clustering must recover *how* consumers use energy, not only *how much*.
- **Evidence:** `src/data_loader.py`; `outputs/reports/dataset_validation_report.md`; archetype variation/overlap figures.
- **Files:** `src/data_loader.py`, `src/validate_dataset.py`
- **Tests:** Dataset validation script; feature shape tests.
- **Result:** Hidden archetypes exist; labels never fed to K-Means.

### 2. weekend_ratio semantics
- **Problem:** `mean(is_weekend)` ≈ record fraction (~0.267 for all clusters).
- **Old:** Boolean mean in aggregation.
- **New:** `weekend_mean_energy / weekday_mean_energy`.
- **Why:** Need energy behavior, not calendar composition.
- **Evidence:** Baseline profiles all ~0.267; unit test expects 0.25 vs 3.0 on toy panel.
- **Files:** `src/feature_engineering.py`
- **Tests:** `tests/test_features.py::test_weekend_ratio_is_energy_based`
- **Result:** Weekend ratios now differ across consumers/clusters.

### 3. Electrical / temperature consistency
- **Problem:** Current derived as energy rescale; temperature from row index.
- **New:** Physically coherent generation where retained; temperature from timestamp; electrical vars excluded from primary behavioral set.
- **Why:** Avoid duplicated scale and fake exogenous structure.
- **Files:** `src/data_loader.py`, `src/feature_engineering.py`
- **Result:** Primary experiment uses behavioral features.

### 4. Cross-consumer imputation leakage
- **Problem:** Global `ffill().bfill()` across entire table.
- **New:** Sort by `(consumer_id, timestamp)`; within-consumer fill.
- **Why:** Panel safety.
- **Evidence:** Shuffle leakage test.
- **Files:** `src/preprocessing.py`
- **Tests:** `tests/test_preprocessing.py`
- **Result:** No cross-consumer sentinel leakage after shuffle.

### 5. Blind outlier deletion of peaks
- **Problem:** Global IQR removed legitimate peaks.
- **New:** Detect/log by default; `remove_outliers_flag=False`; configurable ranges.
- **Files:** `src/preprocessing.py`
- **Result:** Behavioral extremes preserved in default pipeline.

### 6. Scale/shape feature mixing
- **Problem:** Magnitude dominated distance.
- **New:** `behavioral` / `scale` / `combined` feature sets; primary = behavioral.
- **Files:** `src/feature_engineering.py`, `src/run_ablation_study.py`
- **Evidence:** Ablation report.
- **Result:** Objective shifted to pattern segmentation; scale ablation documents the alternative.

### 7. Hard-coded K preference (3 to 6)
- **Problem:** Heuristic could override best silhouette at K=2.
- **New:** Multi-metric consensus + optional ARI stability; no preferred range.
- **Files:** `src/clustering.py`
- **Tests:** `tests/test_clustering.py::test_select_optimal_k_no_hardcoded_preference`
- **Result:** If K=2 wins metrics, K=2 is kept.

### 8. Generic recommendations
- **Problem:** Same smart-meter/renewables text on every cluster.
- **New:** Evidence-triggered recommendation engine with observation / metric / baseline / action.
- **Files:** `src/recommendation_engine.py`
- **Evidence:** `outputs/reports/recommendations_report.md`
- **Result:** Recommendations differ by measured triggers.

### 9. Dashboard recomputation / stale state / positional K lookup
- **Problem:** Pages refit PCA; insights used fixed 6-PC PCA; `silhouette[k-2]`; stale session labels.
- **New:** Single `AnalysisResults`; config-hash invalidation; `silhouette_for_k(k)` dict lookup.
- **Files:** `app/app.py`, `src/energy_analysis.py`
- **Tests:** `tests/test_dashboard_consistency.py`
- **Result:** Displayed K/labels/metrics match the fitted object.

### 10. Unpinned dependencies / missing dirs / no metadata
- **Problem:** Reload risk; clean runs failed on missing folders.
- **New:** Exact pins; `ensure_output_dirs`; `models/analysis_metadata.json`; pytest suite.
- **Files:** `requirements.txt`, `src/energy_analysis.py`, `tests/*`
- **Tests:** `tests/test_artifacts.py`
- **Result:** Clean env install + `pytest` green; artifacts reload under pinned sklearn.
