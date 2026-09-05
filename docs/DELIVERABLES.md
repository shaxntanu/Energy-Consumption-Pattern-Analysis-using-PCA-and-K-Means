# Final Deliverables Package

Engagement complete. All phases 0 to 11 executed. No pending human gates.

## How to run

```bash
py -m pip install -r requirements.txt
py -m pytest tests/ -v
py src/energy_analysis.py          # primary behavioral pipeline → models/ + outputs/
py src/run_ablation_study.py       # 5 arms → outputs/reports/ablation_*
py src/validate_dataset.py         # archetype validation figures/report
py -m streamlit run streamlit_app.py
```

## Definition of Done

| Criterion | Status |
|-----------|--------|
| Documented behavioral variation; synthetic labeled | Done |
| Energy-based weekend metric; IDs excluded from PCA | Done |
| Panel-aware preprocessing; leakage tested | Done |
| PCA standardized + 95% variance threshold + artifacts | Done |
| Transparent multi-metric K + stability | Done |
| Profiles in original space; evidence recommendations | Done |
| Dashboard = single `AnalysisResults` object | Done |
| Pinned env + tests + metadata | Done |
| Ablation shows FE changes the question | Done |
| Baseline preserved under `baseline/` | Done |

## Key results (behavioral primary, seed=42)

The table below is the phase-11 snapshot (30-day window, pre-upgrade). The
current authoritative numbers live in `outputs/reports/analysis_summary.md`
(365-day flagship run, K=4) and are quoted in the README. Both states of the
repo are kept so the comparison is auditable.

| Item | Value (phase-11 snapshot) |
|------|--------|
| Data | Synthetic archetype-based (200×30×hourly) |
| Features | 33 behavioral (24h shape + timing + variability) |
| PCA | 25 components (≥95% cum. var.) |
| Selected K | **2** |
| Silhouette @ K=2 | **0.1055** (weak but honest) |
| CH / DB @ K=2 | 16.60 / 3.29 |
| Stability ARI | **0.791 ± 0.111** (10 seeds) |
| Cluster sizes | 135 / 65 |
| Weekend ratios | 0.95 vs 1.20 (energy-based) |
| Tests | 18 passed (then); 138 test functions in 13 files today |

## Ablation (executed)

| Feature set | K | Silhouette | ARI | Role |
|-------------|---|------------|-----|------|
| behavioral | 2 | 0.105 | 0.791 | **Primary** |
| scale | 2 | 0.354 | 1.000 | Magnitude control |
| combined | 2 | 0.104 | 1.000 | Mixed control |

Scale wins raw metrics; **behavioral** is the project answer.

## Baseline vs corrected (headline)

| | Baseline | Corrected |
|-|----------|-----------|
| weekend_ratio | ~0.267 all clusters | differs (energy ratio) |
| Selected K | 3 (forced 3 to 6) | 2 (metrics) |
| Cluster meaning | low/mid/high kWh | timing / weekend / variability |
| Silhouette | 0.31 @ K=3 | 0.11 @ K=2 behavioral |

## File map

| Deliverable | Path |
|-------------|------|
| Audit | `audit_report.md` |
| Change log | `docs/CHANGELOG.md` |
| Baseline comparison | `docs/BASELINE_VS_CORRECTED.md` |
| Methodology | `docs/METHODOLOGY.md` |
| Final report | `docs/FINAL_REPORT.md` |
| This package | `docs/DELIVERABLES.md` |
| Metadata | `models/analysis_metadata.json` |
| Metrics | `outputs/metrics/*.csv` |
| Profiles / recs / ablation | `outputs/reports/*` |
| Figures | `outputs/figures/*` |
| Frozen baseline | `baseline/` |
| Tests | `tests/` |
| Dashboard | `streamlit_app.py` (web app: `web/`) |

## Scientific honesty

Behavioral clustering separation is **weak**. That is expected after removing the magnitude crutch. Do not inflate K or cherry-pick scale results as the main claim. Recommendations are correlational suggestions only, and imply no causal savings.
