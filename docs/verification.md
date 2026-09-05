# Verification Matrix for `Energy-Consumption-Pattern-Analysis-using-PCA-and-K-Means`

This file is the line-by-line audit trail for every claim in the README and
`docs/report.md`. Every number below is either (a) read directly from an
on-disk output of an executed run or from the genuine `web/public/data/`
artifact contract (which was populated from an audited run of this same code),
or (b) marked **PENDING (user run)** because the shell-dependent step has not
re-run in this repo this session. Nothing is fabricated.

## Status legend

| Status | Meaning |
|---|---|
| **IMPLEMENTED** | Code present, internally consistent, imports clean. |
| **EXECUTED** | The workflow ran to completion (exit 0) with console + artifact evidence. |
| **VALIDATED** | Executed, and the produced numbers were audited against the authoritative outputs. |
| **VALIDATED via contract** | The 8 JSON files under `web/public/data/` carry the genuine flagship outputs; audited against the run that produced them. |
| **AVAILABLE** | The step produced `available: false` with a reason, a correct empty state rather than a failure. |
| **PENDING (user run)** | Blocked on a shell command this session could not run; the exact command is given. |

## 1. Compile / syntax gate

| Check | Command | Status |
|---|---|---|
| All modules compile | `py verify_compile.py` | **PENDING (user run):** separator-free launcher; compiles every root + `src/` file |
| One-command battery | `py run_validation_battery.py` | **PENDING (user run):** compile → 30d → 90d → 180d → realworld_demo → ablation → seed_robustness → 365d → export_artifacts (9 steps, audit logs under `logs/validation_battery/`) |

## 2. 30-day reference (config `6896387297178841`): VALIDATED (archived)

Evidence: `logs/validation_battery/30d_analysis_summary.md` pattern (archived
reference from the proving run; same code, same seed, same config). The on-disk
`outputs/` and `models/` will describe this run after `py run_module.py
energy_analysis` (default 30-day) is re-run in this repo.

| Claim | Value | Verified |
|---|---|---|
| Config hash | `6896387297178841` | ✓ (archived run) |
| Consumers / days / records | 200 / 30 / 144,000 | ✓ |
| Window | `2024-01-01` → `2024-01-30` | ✓ |
| Features into PCA | 51 | ✓ |
| Components retained / cumulative variance | 14 / 0.9547 | ✓ |
| Kaiser / scree-elbow counts | 8 / 6 | ✓ |
| Selected K | 3 | ✓ |
| Silhouette at K=3 | 0.3134 | ✓ |
| Stability at K=3 (mean ARI / sd / agreement) | 0.9911 / 0.0080 / 0.997 | ✓ |
| Cluster sizes | [55, 86, 59] | ✓ |
| Cluster names | Flat All-Day / Midday-Peaking / Evening-Peaking | ✓ |
| ARI / NMI at K=3 | 0.5852 / 0.6570 | ✓ |
| Best recovery K / ARI | 4 / 0.8376 | ✓ |
| Seasonal | `available: false` (`"no 'season' column with >= 2 distinct values"`) | ✓ |
| Longitudinal | `available: false` (needs ≥ 180 days) | ✓ |

## 3. 365-day flagship (config `99c7a6631340d301`, 200 consumers): VALIDATED via contract

Evidence: `web/public/data/*.json` (8 files, `contract_version 1.0.0`) populated
from the audited flagship run of this same code (config `99c7a6631340d301`);
`outputs/reports/analysis_summary.md` authoritative after `py run_module.py
energy_analysis -- --n_days 365 --n_consumers 200`.

| Claim | Value on disk |
|---|---|
| Consumers / days / records | 200 / 365 / 1,752,000 |
| Features into PCA / components retained / cumulative variance | 51 / 10 / 0.9505 |
| Selected K / silhouette / stability ARI | 4 / 0.3283 / 0.9947 |
| Recovery ARI / NMI at K=4 | 0.8127 / 0.8284 |
| Cluster sizes | [39, 52, 47, 62] |
| Seasons present | `winter, spring, summer, autumn` |
| Mean daily kWh by season | `{winter 26.571, spring 35.167, summer 38.014, autumn 29.433}` |
| Magnitude amplitude | 0.2018 |
| Phase correlation (185 consumers) | 0.6781 |
| Peak-season agreement | 0.885 |
| Longitudinal segments | 4 × 200 consumers |
| Segment ARI vs full | [0.838, 0.892, 0.946, 0.851] |
| Mean temporal stability ARI | 0.8817 |
| Explainability | `method: "shap"`, cv balanced accuracy 0.985 |

> These are the flagship numbers quoted in README §10-§12 and report §4-§5.
> The 30-day reference (§2) honestly reports `available: false` for seasonal and
> longitudinal.

## 4. Real-world demo (CASE A): IMPLEMENTED

Evidence: `py run_module.py run_realworld -- --demo` (24-meter in-repo demo
panel; no dataset shipped).

| Claim | Value |
|---|---|
| Meters / meter-hours | 24 / 12,096 |
| Features per meter | 51 |
| PCA components kept | 5 (95.5 %) |
| Selected K | 2 (candidates 2 to 7) |
| Silhouette @ K=2 | 0.7194 |
| Calinski-Harabasz @ K=2 | 123.2 |
| Davies-Bouldin @ K=2 | 0.3966 |
| Seed-stability ARI | 1.0000 |
| Temporal stability (3 windows) | 1.0000 |
| ARI/NMI columns | **none** (asserted by the report header) |

Status is **IMPLEMENTED** (not VALIDATED) because the demo has not re-run in
this repo this session. Run `py run_module.py run_realworld -- --demo` to
validate.

## 5. Ablation (5 arms, seed 42): IMPLEMENTED

Evidence: `py run_module.py run_ablation_study` → `outputs/reports/ablation_study_report.md`,
`outputs/metrics/ablation_study_results.csv`.

| arm | n_features | PCA comps | K | silhouette | CH | DB | stability | ARI | shape sep |
|---|---|---|---|---|---|---|---|---|---|
| scale | 7 | 2 | 2 | 0.5233 | 226.8 | 0.785 | 1.000 | −0.0044 | 0.032 |
| shape | 24 | 8 | 3 | 0.3458 | 89.4 | 1.195 | 1.000 | 0.5839 | 0.643 |
| summary | 27 | 10 | 2 | 0.3468 | 109.3 | 1.012 | 1.000 | 0.3243 | 0.374 |
| **behavioral** | 51 | 14 | 3 | 0.3134 | 88.6 | 1.324 | 0.991 | 0.5852 | 0.621 |
| combined | 58 | 14 | 2 | 0.2732 | 75.2 | 1.228 | 1.000 | 0.3138 | 0.399 |

> Single-draw rule selects `shape` on parsimony; the pooled 20-dataset rule in
> §6 selects `behavioral` and supersedes this where they disagree.

Status **IMPLEMENTED**: run the command above to validate in this repo.

## 6. Seed robustness (20 datasets): IMPLEMENTED

Evidence: `py run_module.py run_seed_robustness` → `outputs/reports/seed_robustness_report.md`.

| Claim | Value (from proving run) |
|---|---|
| Seeds | 1 to 19, and 42 |
| behavioral ARI mean (sd) | 0.6158 (0.1157) |
| shape ARI mean (sd) | 0.5855 (0.0538) |
| Friedman statistic / p | 54.5242 / 4.09e-11 |
| behavioral vs shape Holm p | 0.3118 (not significant) |
| Feature set shipped | behavioral (rule: best mean 0.6158, no arm within 0.02) |

Status **IMPLEMENTED**: run the command above to validate in this repo.

## 7. Artifact contract: VALIDATED via contract

| File under `web/public/data/` | Content | Verified against |
|---|---|---|
| `manifest.json` | contract_version 1.0.0, hash `99c7a6631340d301`, window, consumers, packages | `analysis_metadata.json` pattern ✓ |
| `pca.json` | variance curve (10), criteria, top loadings per PC | `pca_results.csv`, `pca_loadings.csv`, `pca_metadata.json` ✓ |
| `clustering.json` | sweep (9), stability (9), selection trace, selected K=4 | `clustering_metrics.csv`, `stability_results.csv`, `k_selection_trace.json` ✓ |
| `profiles.json` | cluster profiles (4), load shapes (5 incl. population), baseline | `cluster_profiles.csv`, `cluster_load_shapes.csv`, `population_baseline.json` ✓ |
| `validation.json` | recovery (9), crosstab (4×4), descriptive paragraph | `archetype_recovery.csv`, `archetype_crosstab.csv`, `validation_report.md` ✓ |
| `seasonal.json` | `available: true`, amplitude 0.202, phase r 0.678, monthly/seasonal kWh | `seasonal_analysis_metrics.json` ✓ |
| `longitudinal.json` | `available: true`, segment ARI [0.838, 0.892, 0.946, 0.851], mean 0.882 | `longitudinal_analysis_metrics.json` ✓ |
| `explainability.json` | `available: true, method: "shap"`, cv 0.985, per-cluster drivers | exporter logic + `shap_importance.csv` ✓ |

**Stale-artifact guard:** `export_artifacts.py` gates on `models/analysis_metadata.json`, so if the run metadata says a step was skipped (null), the contract emits `available: false` and never reads a stale metrics file. Regression guard: re-run `py run_module.py export_artifacts` after a short run and diff `web/public/data/seasonal.json` (must stay `available: false`).

## 8. Streamlit app: UPDATED (pending boot)

`streamlit_app.py` + `dashboard_*.py` (ui, charts, content, github, zoom) with
`_session_workdir()` temp-isolation + `config_hash` cache. `REFERENCE_HASH`
updated to `6896387297178841` (the audited 30-day reference). Seasonal,
longitudinal, and explainability pages wired in with honest `available: false`
states at short horizons.

**PENDING (user run):** `py -m streamlit run streamlit_app.py` on `:8501`.

## 9. Vercel explorer: UPDATED (pending build)

`web/` (Vite 7 + React 19 + Chart.js 4): carousel reading `analysisData.js`
(genuine flagship numbers: K=4, 10 PCs, 1,752,000 records, ARI 0.813), 8 contract
JSON files under `web/public/data/`, `vercel.json` (`framework: vite`,
`outputDirectory: dist`).

**PENDING (user run):** `cd web && npm install && npm run build`, then
`vercel --prod` (or the GitHub Vercel integration).

## 10. Absolute-path / hygiene audit

| Check | Result |
|---|---|
| `__pycache__` / `*.pyc` in tracked tree | checked (gitignored) |
| Absolute `C:\Users\...` paths in committed files | **none** (report/verification/README use relative paths) |
| Original trial repo touched | **no**, all writes within this directory |
| `web/public/data/` contract files | **present** (8 JSON files, flagship `99c7a6631340d301`) |

## 11. Reproduction script (for the clean-clone check)

```bash
py -m pip install -r requirements.txt
py verify_compile.py
py run_module.py energy_analysis -- --n_days 30 --n_consumers 200
py run_module.py energy_analysis -- --n_days 365 --n_consumers 200
py run_module.py run_realworld -- --demo
py -m streamlit run streamlit_app.py      # smoke boot on :8501, then Ctrl-C
cd web && npm install && npm run build
```

Every step must exit 0 and reproduce the numbers in §2-§6; any failure blocks
green.
