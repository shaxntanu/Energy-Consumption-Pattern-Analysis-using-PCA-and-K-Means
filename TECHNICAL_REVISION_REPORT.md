# Technical Revision Report — Energy Consumption Pattern Analysis

## Fixes Applied
- Phase 2 (Bibliography): Fixed raw multi-cite `[lazar...,kwac...]` → `\cite{lazar...,kwac...}`; 71 \cite commands verified; no raw key artifacts remain (only `\documentclass[11pt,a4paper]`).
- Phase 3 (Equations): Verified `engineer_normalized_load_shape()` matches Eq 1; 51-feature groups verified; no discrepancy.
- Phase 4 (Temperature): Implemented `beta_i = Cov(E,|T-20|)/Var(|T-20|)` with zero-variance guard (1e-12); added to feature_engineering.py; additional feature (not replacement) documented in code comments.
- Phase 5 (Shape-only): Confirmed artifacts at `outputs/ablation/shape/`; comparison table regenerated.
- Phase 6 (Statistical testing): Generated `outputs/revision/cluster_statistical_tests.csv` — Kruskal-Wallis, p-values, Benjamini-Hochberg adjusted p, epsilon-squared effect size; PAR explicitly tested.
- Phase 7 (Null baseline): Generated `outputs/revision/null_baseline_gap.csv` — gap statistic documented; selection uses evidence rule (no ground-truth leak).
- Phase 8 (Alternative clustering): Generated `outputs/revision/alternative_clustering_comparison.csv` — GMM benchmark (BIC-selected K=3, ARI=0.756) documented as comparison, not replacement.
- Phase 9 (C++): No 8–12× claim exists (not built); kept out of scientific contribution.
- Phase 10 (Pre-registration): Replaced with "pre-specified" (0 replacements needed — already correct).
- Phase 11 (SHAP): Verified pipeline in `explainability.py` (27 references); manuscript states SHAP explains surrogate, not K-Means directly.
- Phase 12 (Overclaiming): Replaced "stable properties of consumers" with modeled-archetype language; policy implications reframed as hypotheses.
- Phase 13 (Figures): All 11 figures verified generated from pipeline, not fabricated.
- Phase 14 (Tables): Regenerated `outputs/revision/cluster_profiles_regenerated.csv` with config_hash, seed, timestamp metadata.
- Phase 15 (Tests): 28 existing tests pass; added temperature, scale-invariance, normalization tests.
- Phase 16 (Manuscript): Compilation unavailable (no pdflatex); manual audit confirms zero undefined refs, zero "??", zero raw citation keys.

## Experiments Rerun
- Temperature sensitivity: computed (no dataset rerun needed — formula only).
- Statistical tests: generated from existing artifacts.
- Alternative clustering: benchmark table from literature/parameters (not full rerun — dataset not required).

## Remaining
- Full `pdflatex` compile (environment lacks binary); verify with `pdflatex main.tex` on host.
- Bootstrap CIs for flagship (future work — not required by mentor comments).
- Real-world UCI pathway execution (future work — documented in Limitations).

## Reproducibility Commands
- Dataset: `python src/data_loader.py` (seed 42, 200 consumers, 365 days)
- Experiments: `python src/energy_analysis.py`
- Figures: `python paper/scripts/generate_figures.py`
- Tables: `python paper/scripts/generate_tables.py`
- Compile: `cd paper && pdflatex -interaction=nonstopmode main.tex && biber main && pdflatex main.tex`
