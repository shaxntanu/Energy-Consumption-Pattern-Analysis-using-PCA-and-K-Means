# Full-year synthetic replication and shape baseline study

- Consumers per run: 200
- Days per run: 365
- Independent generator seeds: 20 (100--119)
- Candidate K values: 2--10; restart runs per K: 8
- Ground-truth archetypes were used only after fitting to calculate ARI/NMI.
- Baselines use fixed K=4 for a like-for-like test; the primary pipeline also reports its selected K.
- 95% bootstrap intervals resample independent data seeds (5,000 draws), not households or hourly rows.

## Mean recovery and internal quality

| Method | ARI (95% CI) | NMI (95% CI) | Silhouette mean | K counts |
|---|---:|---:|---:|---|
| 24 normalized hourly bins; no PCA; K=4 | 0.693 [0.655, 0.732] | 0.719 [0.691, 0.746] | 0.331 | `{"4": 20}` |
| 24 normalized hourly bins; PCA to 95%; K=4 | 0.693 [0.657, 0.729] | 0.718 [0.693, 0.743] | 0.346 | `{"4": 20}` |
| 51 behavioral features; no PCA; K=4 | 0.851 [0.825, 0.875] | 0.846 [0.825, 0.866] | 0.299 | `{"4": 20}` |
| 51 behavioral features; PCA to 95%; K=4 | 0.854 [0.825, 0.880] | 0.848 [0.825, 0.870] | 0.321 | `{"4": 20}` |
| 51 behavioral features; PCA to 95%; K by predeclared rule | 0.778 [0.719, 0.836] | 0.799 [0.756, 0.838] | 0.325 | `{"3": 7, "4": 13}` |

## Paired ARI differences versus the 24-bin no-PCA baseline

Positive values favor the named method in this synthetic experiment.

| Contrast | Mean difference (95% bootstrap CI) |
|---|---:|
| shape_24_pca95 minus shape_24_no_pca | 0.000 [-0.005, 0.006] |
| behavioral_51_no_pca minus shape_24_no_pca | 0.158 [0.122, 0.197] |
| behavioral_51_pca95_k4 minus shape_24_no_pca | 0.161 [0.125, 0.201] |
| behavioral_51_pca95_selected_k minus shape_24_no_pca | 0.085 [0.028, 0.139] |

## Reproducibility and limits

- Raw seed-level metrics: `outputs/research_additions/synthetic_365_seed_runs.csv`
- Summary CSV: `outputs/research_additions/synthetic_365_seed_summary.csv`
- Figure: `outputs/figures/research_additions/synthetic_365_baseline_comparison.png`
- Metadata: `outputs/research_additions/synthetic_365_seed_study.json`
- Results depend on the repository's synthetic generator. They do not establish recovery on measured households.
- Bootstrap intervals summarize seed-to-seed variation under this generator, not population sampling uncertainty.
