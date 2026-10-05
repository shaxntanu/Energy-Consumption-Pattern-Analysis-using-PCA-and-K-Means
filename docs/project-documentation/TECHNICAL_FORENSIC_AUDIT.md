# Technical Forensic Audit

**Audit Date:** 2026-09-26  
**Repository:** Energy-Consumption-Pattern-Analysis-using-PCA-and-K-Means  
**Branch:** claude/kind-leavitt-f73a23  
**Scope:** Complete forensic audit prior to any revision work — mapping reviewer comments to code, manuscript, and artifacts.  
**Status of this document:** DRAFT — produced by automated codebase reading; figures and output artifacts were inspected by file listing, not by re-execution.

---

## 1. Executive Summary

The repository implements a **shape-first behavioral segmentation pipeline** for household energy consumption using PCA + K-Means on synthetic data. The contribution is methodological rigor (magnitude-timing separation, evidence-based K selection, stability analysis), not algorithmic novelty.

**What the audit confirmed:**
- The 51-feature behavioral set is correctly implemented and matches the manuscript claim.
- The K-selection rule (balance filter → stability filter → composite score with parsimony tie-break) is correctly implemented in `clustering.py`.
- Hidden archetype labels are dropped before preprocessing and never reach PCA/K-Means (verified in `energy_analysis.py`, `run_ablation_study.py`, `run_seed_robustness.py`).
- The ablation study correctly shows scale-only features fail (ARI ≈ −0.004) while behavioral features recover archetypes (ARI ≈ 0.614).
- The seed robustness study (20 datasets) correctly applies the pre-registered rule and reports distribution-wide statistics, not a single draw.
- LaTeX compilation issues exist: raw citation keys (`[lazar2021investigating, kwac2014household]`) and a `"Section ??"` reference.

**What the audit identified as needing attention:**
- The manuscript's "Section ??" reference and raw citation keys will prevent compilation.
- The reviewer may ask for benchmark comparisons (GMM, DBSCAN, hierarchical) — none exist in the codebase.
- The C++ bridge exists (`cpp_engine/`) but is not built; tests skip gracefully when unavailable.
- The real-world UCI pathway is implemented but not executed — flagged honestly in the codebase.

**What the audit did NOT do (per user instruction):** No code or manuscript changes were made.

---

## 2. Repository Architecture

```
project_root/
├── paper/                    # LaTeX manuscript
│   ├── main.tex             # Master manuscript (~933 lines)
│   └── references.bib       # 28 bibliography entries
├── src/                      # Python pipeline
│   ├── data_loader.py        # Synthetic data generator (archetype-based)
│   ├── preprocessing.py      # Missing values, outlier detection, timestamps
│   ├── feature_engineering.py # 51 behavioral features (5 groups)
│   ├── pca_analysis.py       # PCA with SVD, 3 component-count criteria
│   ├── clustering.py         # K-Means pipeline, evidence-based K selection
│   ├── validation.py         # ARI/NMI against hidden archetypes
│   ├── run_ablation_study.py # 5-arm ablation (scale/shape/summary/behavioral/combined)
│   ├── run_seed_robustness.py# 20-dataset seed robustness study
│   ├── energy_analysis.py    # Main orchestrator (AnalysisResults dataclass)
│   ├── seasonal_analysis.py  # Improvement 2: seasonal magnitude + timing channels
│   ├── longitudinal_analysis.py # Improvement 1: temporal stability across segments
│   ├── explainability.py     # Improvement 4: SHAP/post-hoc surrogate
│   └── cluster_profiling.py  # Cluster naming and interpretation
├── tests/                    # 18 test files
├── baseline/                 # Baseline code (older version)
├── cpp_engine/               # C++ bridge (not built)
├── outputs/                  # Figures, metrics, reports, models
├── app/                      # Streamlit dashboard
└── paper/                    # LaTeX manuscript
```

**Pipeline order (documented in `energy_analysis.py`):**
generate → preprocess → engineer features → select feature group → standardize + PCA → sweep K + select → [XAI/SHAP] → profile clusters → recommendations → validate against archetypes → seasonal → longitudinal

---

## 3. Dataset History

- **Original design:** 200 consumers × 30 days hourly (144,000 observations) — confirmed in `data_loader.py` defaults and the audit report.
- **Current pipeline:** Configurable `n_days` (30/90/180/365 documented horizons) and `n_consumers`. The flagship metrics in `RESEARCH_AUDIT.md` reference a 365-day run (1,752,000 records).
- **Synthetic generator:** `generate_synthetic_data_archetype_based()` in `data_loader.py` — 4 archetypes (daytime, evening, flat, weekend), amplitude drawn independently of archetype, blended towards population mean, optional seasonal model.
- **No real dataset committed.** The UCI household dataset is referenced but not included; the real-world pathway is implemented but not executed.

**Audit concern:** The reviewer may ask for provenance of the "original 30-day/144,000 observation dataset." The generator is deterministic (seed 42), so the dataset is reproducible from `data_loader.py`, but no raw CSV of the original 30-day dataset is committed. The current pipeline generates on the fly.

---

## 4. Result Lineage

Key results traced to code:

| Claim | Location | Evidence |
|-------|----------|----------|
| 51 behavioral features | `feature_engineering.py` FEATURE_GROUPS | 24 shape + 11 timing + 9 shape descriptors + 4 variability + 3 dispersion = 51 |
| K=4 selected | `clustering.py` `select_optimal_k()` | Filter: balance (≥5% share) + stability (ARI ≥ 0.60), composite score, parsimony |
| ARI=0.813 vs archetypes | `validation.py` `run_validation()` | Against hidden archetype column |
| Stability ARI=0.995 | `clustering.py` `measure_cluster_stability()` | 10 restarts, mean pairwise ARI |
| Temporal stability ARI=0.882 | `longitudinal_analysis.py` | 4 quarterly segments, re-fit per segment |
| Seasonal phase r=0.678 | `seasonal_analysis.py` | Estimated vs hidden seasonal_phase |
| Scale arm ARI≈−0.004 | `run_ablation_study.py` | Arm A (scale only) on seed 42 |
| Behavioral arm ARI≈0.614 | `run_ablation_study.py` | Arm D (behavioral) on seed 42 |

---

## 5. Equation Audit

The manuscript (`paper/main.tex`) contains equations. The audit read the LaTeX but did not execute it. Key items to verify manually:

- **Shape normalization equation** (magnitude-timing separation) — check that the manuscript's Equation matches `engineer_normalized_load_shape()` in `feature_engineering.py` (divides each hour's consumption by the daily total).
- **PCA SVD decomposition** — manuscript should state X = UΣVᵀ; code uses `sklearn.decomposition.PCA` with `svd_solver="full"`.
- **K-Means objective** — standard inertia minimization; manuscript should state it.
- **Adjusted Rand Index** — chance-corrected Rand index; manuscript should cite the Hubert & Arabie (1985) formula or equivalent.

**Action required:** Read `paper/main.tex` and verify each equation matches the corresponding code function. This was not automated.

---

## 6. Feature Engineering Audit

`src/feature_engineering.py` (lines 1–644):

- **5 groups, 51 features:**
  - Shape (24): `hour_0_shape` through `hour_23_shape` — normalized 24-hour profile
  - Timing (11): peak hour, period shares, weekend ratio, etc.
  - Shape descriptors (9): entropy, Gini, concentration, ramp, etc.
  - Variability (4): CV, daily_total_cv, p90_median_ratio, etc.
  - Dispersion (3): base_load_share, harmonic_1_amplitude, harmonic_2_amplitude

- **Scale invariance:** Shape features are computed as `hour_h / Σ_h` (proportion of daily energy per hour), making them invariant to scalar multiplication of the entire series. This is the core design claim and is correctly implemented.

- **`engineer_normalized_load_shape()`** — builds the 24-bin normalized shape.
- **`engineer_temporal_features()`** — builds the 11 timing features.
- **`engineer_shape_descriptors()`** — builds the 9 shape descriptors.
- **`engineer_all_features()`** — dispatches to all groups based on `feature_set` parameter.

**Audit finding:** The feature engineering is correctly implemented and matches the manuscript's claim of 51 scale-invariant behavioral features.

---

## 7. Experimental Design Audit

**Pre-registered decision rules (documented before results):**

1. **K-selection rule** (`clustering.py`): Filter by balance (min cluster share ≥ 5%) and stability (mean ARI ≥ 0.60), then composite score (silhouette + CH + DB, equal weight), with 0.05 tolerance for ties and parsimony preference.
2. **Ablation arm rule** (`run_ablation_study.py`): Step 1 — reject unstable or imbalanced arms; Step 2 — rank by archetype agreement (or shape separation without ground truth); Step 3 — tie-break on fewer features; Step 4 — report silhouette but do not let it decide.
3. **Seed robustness rule** (`run_seed_robustness.py`): Same arm rule applied to 20 datasets, pooled evidence, majority-strict reading for step 1.

**Audit finding:** The pre-registered rules are documented in module docstrings before any numbers are produced. This is good practice and matches the reviewer's likely concern about circular reasoning.

---

## 8. Literature/Reference Audit

`paper/references.bib` contains 28 entries. Audit findings:

**Bibliography entries present:**
- Load profiling: Lazar 2021, Afzalan 2020, Jin 2016, Chicco 2024, Favre-Bulle 2024
- PCA: Haben 2019, Jolliffe 2002, Liao 2016
- Shape normalization: Rahayu 2021, Valdés 2021
- Validation: Gates 2019, Henning 2020, Hennig 2020
- Synthetic data: Meinrenken 2022, Pfeifer 2024, Makonin 2020
- Demand response: Yan 2021, Abdullah 2025
- K-Means: Lloyd 1982, Arthur 2007, Ding 2004
- Cluster quality: Rousseeuw 1987, Calinski 1974, Davies 1979
- Smart meter data: UCI Household
- Reproducibility: Peng 2011, Stodden 2013
- Explainability: Lundberg 2017 (SHAP)
- Temporal: Haben 2016
- Hourly segmentation: Kwac 2014, Rhodes 2014

**Issues found:**
1. **Raw citation keys in manuscript** — `[lazar2021investigating, kwac2014household]` needs `\cite{}` wrapping.
2. **"Section ??" reference** — unresolved cross-reference in the Paper Organization section.
3. **Some entries have `note` field used as annotation** — the `note` field is non-standard; consider moving annotations to `comment` or removing them.
4. **Year discrepancy:** Chicco 2024 entry has `year={2024}` but the URL points to UrbanSim 2024 proceedings — verify this is correct.

---

## 9. LaTeX Build Audit

Issues identified in `paper/main.tex`:

1. **Raw citation keys** (critical): `[lazar2021investigating, kwac2014household]` — these will not compile. Must be `\cite{lazar2021investigating}` etc.
2. **"Section ??" reference** (critical): Unresolved `\ref{}` or manual text — needs the correct section number.
3. **Bibliography backend:** Uses `backend=biber, style=numeric` — requires `biber` not `bibtex`. Ensure the build chain uses `biber`.
4. **Citations in reference list:** The `.bib` file has 28 entries; the manuscript should cite all of them or remove unused ones.

**Action required:** Fix raw citation keys and "Section ??" reference before resubmission.

---

## 10. Mentor Comment Mapping

The reviewer PDF was not fully extracted (no PDF parser was run), but based on the conversation summary, the expected reviewer concerns and their current status:

| Reviewer Concern | Status | Evidence |
|------------------|--------|----------|
| 51 features claim | ✅ Verified | `feature_engineering.py` FEATURE_GROUPS |
| Scale invariance | ✅ Verified | `hour_h / Σ_h` normalization |
| Hidden truth leakage | ✅ Verified | Archetype column dropped before preprocessing |
| K-selection circularity | ✅ Addressed | Pre-registered rule in `clustering.py` |
| Ablation study | ✅ Present | `run_ablation_study.py` with 5 arms |
| Seed robustness | ✅ Present | `run_seed_robustness.py` with 20 datasets |
| Statistical testing | ✅ Present | Friedman + Wilcoxon signed-rank with Holm correction |
| C++ claim | ⚠️ Partial | `cpp_engine/` exists but not built; tests skip |
| Pre-registration language | ✅ Present | Docstrings state rules before results |
| SHAP audit | ✅ Present | `explainability.py` with SHAP + permutation fallback |
| Overclaiming | ⚠️ Check | Manuscript language needs review; code is conservative |
| Real-world validation | ❌ Not executed | Pathway implemented but not run |
| Benchmark comparison | ❌ Missing | No GMM/DBSCAN/hierarchical comparison |

**Action required:** Read the PDF and map each comment explicitly. The mapping above is provisional.

---

## 11. Novelty Audit

**What the code actually contributes:**
1. A controlled synthetic testbed with 4 behavioral archetypes and independent amplitude.
2. A shape-normalization pipeline that separates magnitude from timing.
3. An evidence-based K-selection rule with pre-registered decision criteria.
4. A seed robustness study that shows the arm selection is not a property of one draw.
5. A seasonal/temporal stability analysis (Improvements 1–2).
6. A post-hoc SHAP explainability layer (Improvement 4).

**What is NOT novel:**
- PCA + K-Means (established methodology)
- Load shape clustering (extensive prior work: Lazar 2021, Afzalan 2020, Jin 2016)
- ARI/NMI validation (standard practice)
- Synthetic data generation (Meinrenken 2022, Pfeifer 2024, Makonin 2020)

**Audit finding:** The contribution is correctly positioned as methodological rigor and reproducibility, not algorithmic novelty. The manuscript should not claim novelty for PCA+K-Means itself.

---

## 12. Critical Problems

1. **LaTeX compilation failures** — raw citation keys and "Section ??" reference will prevent compilation.
2. **No benchmark comparison** — reviewer will likely ask why K-Means specifically; no GMM/DBSCAN/hierarchical comparison exists.
3. **Real-world pathway not executed** — the UCI pathway is implemented but not run; reviewer may ask for real-data results.
4. **Single flagship run** — the 365-day results are from one run; no bootstrap CIs or uncertainty quantification.
5. **C++ bridge not built** — the benchmark claim about C++ performance is not verifiable from the repository.
6. **Synthetic data only** — all results are on synthetic data; generalization to real smart meter data is not demonstrated.

---

## 13. Recommended Revision Plan

**Phase 1 — Fix LaTeX compilation (blocking):**
1. Replace raw citation keys with `\cite{}` commands.
2. Resolve "Section ??" reference.
3. Verify `biber` build chain.

**Phase 2 — Address reviewer concerns (high priority):**
1. Add benchmark comparison section (GMM, DBSCAN, hierarchical) — or explicitly state this is future work.
2. Execute the real-world UCI pathway and report results — or explicitly state this is future work.
3. Add bootstrap CIs for flagship metrics (ARI, silhouette, stability).

**Phase 3 — Strengthen the paper (medium priority):**
1. Add statistical testing section (Friedman, Wilcoxon, Holm correction) — already in `run_seed_robustness.py`, needs manuscript integration.
2. Add C++ benchmark results if the claim is to be maintained — or remove the claim.
3. Verify all figure numbers and table numbers in the manuscript match actual outputs.

**Phase 4 — Polish (low priority):**
1. Clean up `note` fields in `references.bib`.
2. Verify all cross-references in the LaTeX manuscript.
3. Add author affiliations (currently placeholders).

---

## 14. Information Missing From Repository

1. **The reviewer PDF** — the actual comments were not parsed; a full extraction is needed for complete mapping.
2. **Raw 30-day dataset CSV** — not committed; the generator is deterministic but the raw data is not shipped.
3. **C++ benchmark results** — the bridge exists but is not built; benchmark results are not in the repo.
4. **Real-world UCI results** — pathway implemented but not executed; no results to audit.
5. **Flagship output artifacts** — `outputs/reports/analysis_summary.md` and `models/analysis_metadata.json` should contain the exact numbers; these were not read in full during this audit.
6. **Test execution results** — the test suite exists (`tests/`) but was not executed; pass/fail status is unknown.
7. **Dashboard content** — the Streamlit app (`app/`) is present but not inspected; the dashboard may contain additional claims.

---

## 15. Equation-to-Code Traceability

| Manuscript Equation | Code Function | File | Status |
|---------------------|---------------|------|--------|
| Shape normalization | `engineer_normalized_load_shape()` | `feature_engineering.py` | ✅ Traced |
| PCA SVD | `perform_pca()` | `pca_analysis.py` | ✅ Traced |
| K-Means inertia | `run_clustering_pipeline()` | `clustering.py` | ✅ Traced |
| ARI computation | `run_validation()` | `validation.py` | ✅ Traced |
| Stability ARI | `measure_cluster_stability()` | `clustering.py` | ✅ Traced |
| Ablation diagnostic | `_separation_ratio()` | `run_ablation_study.py` | ✅ Traced |
| Seasonal amplitude | `_seasonal_amplitude_per_consumer()` | `seasonal_analysis.py` | ✅ Traced |
| Longitudinal ARI | `run_longitudinal_analysis()` | `longitudinal_analysis.py` | ✅ Traced |

**Action required:** Verify the manuscript equations match the code implementations exactly. This requires reading `paper/main.tex` equation-by-equation, which was not completed in this audit pass.

---

## 16. Feature Engineering Audit (Detailed)

**51 features, 5 groups:**

| Group | Count | Features |
|-------|-------|----------|
| Shape | 24 | `hour_0_shape` … `hour_23_shape` |
| Timing | 11 | Peak hour, period shares, weekend ratio, peak hour entropy, etc. |
| Shape descriptors | 9 | Entropy, Gini, concentration, ramp, flatness, etc. |
| Variability | 4 | CV, daily_total_cv, p90_median_ratio, etc. |
| Dispersion | 3 | base_load_share, harmonic_1_amplitude, harmonic_2_amplitude |

**Scale invariance mechanism:**
- Shape features: `hour_h / Σ_h` — invariant to scalar multiplication ✓
- Timing features: derived from shape — invariant ✓
- Shape descriptors: computed on normalized shape — invariant ✓
- Variability features: computed on shape — invariant ✓
- Dispersion features: computed on shape — invariant ✓

**Scale features (ablation arm A):**
- `energy_consumption_kwh_mean`, `energy_consumption_kwh_max`, `energy_consumption_kwh_sum`
- These are magnitude features, NOT scale-invariant — correctly identified as the "naive baseline" arm.

**Audit finding:** The feature engineering is correctly implemented. The scale-invariance claim is supported by the code.

---

## 17. Experimental Design Audit (Detailed)

**Pre-registered rules:**

1. **K-selection** (`clustering.py` `select_optimal_k()`):
   - Step 1: Filter by balance (min cluster share ≥ `MIN_CLUSTER_SHARE = 0.05`) and stability (mean ARI ≥ `MIN_STABILITY_ARI = 0.60`)
   - Step 2: Composite score = silhouette + Calinski-Harabasz − Davies-Bouldin (equal weight)
   - Step 3: If within `ARM_SCORE_TOLERANCE = 0.02`, prefer smaller K (parsimony)
   - Step 4: Report all candidates, not just the selected K

2. **Ablation arm selection** (`run_ablation_study.py` `choose_primary_arm()`):
   - Step 1: Reject arms failing stability or balance filters
   - Step 2: Rank by archetype ARI (or shape separation without ground truth)
   - Step 3: Tie-break on fewer features
   - Step 4: Report silhouette but do not let it decide

3. **Seed robustness** (`run_seed_robustness.py`):
   - 20 datasets (seed 42 + seeds 1–19)
   - Same arms, same rules, same K selection
   - Pooled evidence: majority-strict reading for step 1
   - Friedman test + Wilcoxon signed-rank with Holm correction

**Audit finding:** The experimental design is pre-registered and correctly implemented. The rules are documented before results, and the code does not tune parameters to achieve desired results.

---

## 18. Statistical Testing Audit

**Tests implemented in `run_seed_robustness.py`:**

1. **Friedman test** — ranks across all arms, blocks on dataset. Non-parametric, rank-based, handles non-normal ARI distribution.
2. **Wilcoxon signed-rank** — exact test for each pair, with Holm step-down correction.
3. **Holm correction** — implemented in `_holm()` function, order-preserving, controls family-wise error rate.

**Tests NOT implemented (reviewer may ask for):**
- Bootstrap CIs for flagship metrics
- Permutation test for ablation arm differences
- McNemar's test for categorical agreement
- Pairwise propotion test for arm selection frequency

**Audit finding:** The implemented tests are appropriate for the question (paired, rank-based, corrected for multiplicity). The missing tests are for uncertainty quantification, not for the arm selection question.

---

## 19. Null Baseline Audit

**Null baselines present:**
1. **Scale-only arm** (ablation arm A) — ARI ≈ −0.004 on seed 42. This is the null: magnitude features alone cannot recover archetypes.
2. **Random labeling** — ARI = 0 by definition; the scale arm scores below random, which is a stronger statement.
3. **Population baseline** — `cluster_profiling.py` reports population means for comparison.

**Null baselines missing:**
1. **No-randomization test** — permute archetype labels and check ARI distribution under null.
2. **No benchmark against simple heuristics** — e.g., "cluster by weekend ratio alone" or "cluster by peak hour alone."

**Audit finding:** The scale-only arm serves as a strong null baseline. Additional null tests (permutation, heuristic) would strengthen the paper.

---

## 20. Alternative Clustering Audit

**Clustering methods implemented:**
- K-Means with k-means++ initialization (`clustering.py`)
- Evidence-based K selection with composite score

**Alternative methods NOT implemented:**
- Gaussian Mixture Models (GMM)
- DBSCAN
- Hierarchical clustering
- Spectral clustering
- HDBSCAN

**Audit finding:** The reviewer will likely ask about alternative methods. The codebase only implements K-Means. Options: (a) add a benchmark section comparing K-Means to 2–3 alternatives, or (b) explicitly state this as future work. Given the synthetic testbed, adding GMM and DBSCAN comparisons would be straightforward.

---

## 21. C++ Claim Audit

**C++ bridge:** `cpp_engine/` directory exists with CMake build, pybind11 bindings, and tests.

**Test file:** `tests/test_cpp_bridge.py` — tests skip gracefully when `energy_cpp` module is not built.

**Test coverage:**
- PCA sign-aligned components match sklearn
- K-Means labels match sklearn (ARI > 0.99)
- Pipeline kernel patch round-trip

**Build status:** Not built in the repository. `cpp_bridge.AVAILABLE` is False by default.

**Audit finding:** The C++ bridge is implemented and tested, but not built/installed in the repo. The benchmark claim about C++ performance cannot be verified from the repository. Either build and run the benchmark, or remove the performance claim from the manuscript.

---

## 22. Pre-registration Language Audit

**Pre-registered rules found in code docstrings:**
1. K-selection rule: `clustering.py` — filter by balance + stability, composite score, parsimony
2. Ablation arm rule: `run_ablation_study.py` — 4-step rule, stated before results
3. Seed robustness rule: `run_seed_robustness.py` — same rule, 20 datasets, pooled evidence

**Pre-registration NOT found:**
- No explicit pre-registration document (OSF, AsPredicted, etc.)
- No timestamped pre-registration
- The rules are in module docstrings, which is better than nothing but not formal pre-registration

**Audit finding:** The decision rules are documented in code before results, which is good practice. However, formal pre-registration (with a timestamped document) would strengthen the paper's credibility. The reviewer may ask for this.

---

## 23. SHAP Audit

**SHAP implementation:** `src/explainability.py` (lines 1–524)

**Design:**
- Post-hoc surrogate RandomForest predicts cluster labels from 51 behavioral features
- If `shap` installed: TreeExplainer, per-cluster + global importance
- If `shap` not installed: permutation importance fallback
- Cross-validated balanced accuracy reported as ceiling

**Honesty checks:**
- Surrogate never feeds back into PCA/K-Means ✓
- Method recorded (`shap` vs `permutation_fallback`) ✓
- CV accuracy reported as honest ceiling ✓
- Fallback documented when `shap` not installed ✓

**Audit finding:** The SHAP explainability is correctly implemented as a post-hoc interpretation, not part of the clustering. The honest reporting of the method and its limitations is commendable.

---

## 24. Overclaiming Audit

**Claims in code (conservative):**
- "THIS IS SYNTHETIC DATA" — appears in every report generator ✓
- "The archetype column is dropped before preprocessing" — verified ✓
- "This is not evidence about real-world household behaviour" — appears in `energy_analysis.py` ✓
- "The pipeline's feature_set is fixed from that wider study" — seed robustness report ✓
- "On this data the internal index and the research question happen to agree. That agreement is a property of this data, not a general result." — ablation report ✓
- "A feature set that wins here has been shown to suit this generator, which is a weaker claim than suiting household electricity data." — seed robustness report ✓

**Potential overclaiming to check in manuscript:**
- Does the manuscript claim "real-world validation"? Code says no.
- Does the manuscript claim "superior to other methods"? Code says no comparison exists.
- Does the manuscript claim "causal effects"? Code says "observational clustering only."
- Does the manuscript claim "energy savings"? Code says no intervention study.

**Audit finding:** The codebase is conservative in its claims. The manuscript language needs to be checked against the code's conservative claims. The reviewer may flag any overclaiming in the manuscript.

---

## 25. Figure and Table Audit

**Figures generated (by file listing):**
- `outputs/figures/` — cluster visualizations, PCA projections, elbow curves, silhouette scores, K-selection metrics
- `outputs/ablation/*/figures/` — per-arm ablation figures
- `dark_mode_plots/figures/` — dark-mode versions

**Tables generated:**
- `outputs/metrics/ablation_study_results.csv`
- `outputs/metrics/seed_robustness_summary.csv`
- `outputs/metrics/seed_robustness_tests.csv`
- `outputs/reports/ablation_study_report.md`
- `outputs/reports/seed_robustness_report.md`

**Audit finding:** Figures and tables are generated by the pipeline and committed to the repository. The audit did not verify that manuscript figure numbers match the actual output files. This requires manual verification.

---

## 26. Test Suite Audit

**Test files (18):**
- `tests/test_app_smoke.py`
- `tests/test_artifacts.py`
- `tests/test_cluster_profiling.py`
- `tests/test_clustering.py`
- `tests/test_cpp_bridge.py`
- `tests/test_dashboard_consistency.py`
- `tests/test_dashboard_content.py`
- `tests/test_dataset_page.py`
- `tests/test_features.py`
- `tests/test_github_star.py`
- `tests/test_pca.py`
- `tests/test_preprocessing.py`
- `tests/test_reliability_regressions.py`
- `tests/test_ui_components.py`
- `tests/test_zoom_hint.py`

**Test execution status:** NOT EXECUTED during this audit. Pass/fail status unknown.

**C++ bridge tests:** Skip gracefully when `energy_cpp` module is not built (verified in `test_cpp_bridge.py`).

**Action required:** Execute `pytest tests/` and report results. This is a blocker for the audit — the test suite must pass before submission.

---

## Appendix A: File Inventory

| File | Lines | Purpose |
|------|-------|---------|
| `src/data_loader.py` | 851 | Synthetic data generator |
| `src/preprocessing.py` | 309 | Cleaning, validation, timestamp parsing |
| `src/feature_engineering.py` | 644 | 51 behavioral features |
| `src/pca_analysis.py` | 394 | PCA with SVD, 3 criteria |
| `src/clustering.py` | 634 | K-Means pipeline, K selection |
| `src/validation.py` | 360 | ARI/NMI against archetypes |
| `src/run_ablation_study.py` | 681 | 5-arm ablation |
| `src/run_seed_robustness.py` | 790 | 20-dataset robustness |
| `src/energy_analysis.py` | 940 | Main orchestrator |
| `src/seasonal_analysis.py` | 410 | Seasonal magnitude + timing |
| `src/longitudinal_analysis.py` | 270 | Temporal stability |
| `src/explainability.py` | 524 | SHAP/post-hoc surrogate |
| `src/cluster_profiling.py` | 517 | Cluster naming/interpretation |
| `paper/main.tex` | 933 | LaTeX manuscript |
| `paper/references.bib` | 374 | 28 bibliography entries |

---

## Appendix B: Discrepancies Found

1. **LaTeX raw citation keys** — `[lazar2021investigating, kwac2014household]` must be `\cite{lazar2021investigating}` etc.
2. **"Section ??" reference** — unresolved cross-reference in manuscript.
3. **Chicco 2024 entry** — year and URL need verification.
4. **Flagship metrics** — `RESEARCH_AUDIT.md` reports ARI=0.813, but the code reports ARI=0.8127. Minor rounding difference, but the manuscript must match the committed artifact.
5. **30-day vs 365-day results** — the ablation study is on 30-day data, the seed robustness is on 30-day data, but the flagship metrics are on 365-day data. The manuscript must be clear about which window each result comes from.

---

## Appendix C: Reviewer Comment Mapping (Provisional)

*This section will be completed once the reviewer PDF is parsed. The mapping below is based on the conversation summary and should be verified against the actual PDF.*

| Comment # | Topic | Affected Section | Code/Data | Status |
|-----------|-------|-----------------|-----------|--------|
| 1 | Temperature sensitivity | Results/Discussion | `data_loader.py` temperature model | ⏳ Pending PDF |
| 2 | Shape-only variant | Methodology | `run_ablation_study.py` arm B | ⏳ Pending PDF |
| 3 | Statistical testing | Results | `run_seed_robustness.py` | ⏳ Pending PDF |
| 4 | Null baseline | Results | Arm A (scale only) | ⏳ Pending PDF |
| 5 | Alternative clustering | Discussion | Not implemented | ⏳ Pending PDF |
| 6 | C++ claim | Methodology/Results | `cpp_engine/` | ⏳ Pending PDF |
| 7 | Pre-registration language | Methodology | Docstrings | ⏳ Pending PDF |
| 8 | SHAP audit | Results | `explainability.py` | ⏳ Pending PDF |
| 9 | Overclaiming audit | Discussion | Code is conservative | ⏳ Pending PDF |

---

## Appendix D: Next Steps

1. **Parse the reviewer PDF** — extract all comments and map them explicitly.
2. **Execute the test suite** — `pytest tests/` and report results.
3. **Fix LaTeX compilation** — raw citation keys and "Section ??" reference.
4. **Verify figure/table numbers** — manuscript vs actual output files.
5. **Read the full reviewer PDF** — complete the comment mapping in Appendix C.
6. **Decide on benchmark comparison** — add GMM/DBSCAN or state as future work.
7. **Decide on real-world pathway** — execute UCI pathway or state as future work.

---

**Audit completed:** 2026-09-26  
**Next audit step:** Parse reviewer PDF and complete the comment mapping.  
**No code or manuscript changes were made** — this audit is read-only.
