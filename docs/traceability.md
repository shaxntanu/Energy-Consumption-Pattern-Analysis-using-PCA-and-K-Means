# Requirements traceability

Statuses are evidence-based. “Partially verified” means there is code and/or saved output, but the complete behavior is conditional, experimental, or not covered by an automated assertion. Test results for the current checkout are recorded in [the repository audit](REPOSITORY_AUDIT.md).

| Requirement | Objective | Design / implementation | Verification | Evidence | Status |
|---|---|---|---|---|---|
| FR-01: seeded synthetic panel | O-1 | `src/data_loader.py` | Generator and pipeline tests | `tests/test_preprocessing.py`; research sidecars | Partially verified |
| FR-02: consumer-safe preprocessing | O-1 | `src/preprocessing.py` | Preprocessing tests | `tests/test_preprocessing.py` | Partially verified |
| FR-03: scale-invariant behavioral features | O-2 | `src/feature_engineering.py` | Feature contract tests | `tests/test_features.py` | Partially verified |
| FR-04: PCA and variance reporting | O-3 | `src/pca_analysis.py` | PCA tests | `tests/test_pca.py` | Partially verified |
| FR-05: K sweep and selection trace | O-3 | `src/clustering.py` | Selection edge-case tests | `tests/test_clustering.py` | Partially verified |
| FR-06: synthetic-only label validation | O-1, O-4 | `src/energy_analysis.py`; `src/validation.py` | Pipeline and artifact tests | `tests/test_artifacts.py`; `outputs/metrics/archetype_recovery.csv` | Partially verified |
| FR-07: stable web artifact export | O-5 | `src/export_artifacts.py` | Artifact and dashboard consistency tests | `tests/test_artifacts.py`; `tests/test_dashboard_consistency.py` | Partially verified |
| FR-08: interactive simulator | O-6 | `streamlit_app.py`; `src/dashboard_*.py` | Streamlit app smoke tests | `tests/test_app_smoke.py`; `tests/test_ui_components.py` | Partially verified |
| FR-09: measured-data studies | O-4 | `research/run_uci_load_diagrams_validation.py`; `research/run_london_household_validation.py` | Reproduction scripts and saved sidecars; not a full-data regression suite | `outputs/reports/real_world_uci_load_diagrams_2012.md`; `outputs/reports/london_household_validation_2013.md` | Partially verified |
| FR-10: optional C++ backend | O-7 | `cpp_engine/`; `src/cpp_bridge.py` | Conditional bridge tests | `tests/test_cpp_bridge.py`; run-specific benchmark required | Partially verified |
| Web artifact rendering | O-5, O-6 | `web/src/`; `web/public/data/` | Node tests and production build | `web/package.json`; `web/vercel.json` | Partially verified |
| CI permissions and paper artifact | O-6 | `.github/workflows/` | Workflow inspection; hosted run required | `.github/workflows/ci.yml`; `.github/workflows/build-paper-pdf.yml` | Partially verified |

