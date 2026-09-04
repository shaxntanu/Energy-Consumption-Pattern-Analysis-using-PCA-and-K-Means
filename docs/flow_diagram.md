# Pipeline Flow Diagram

This figure shows the end-to-end pipeline of the improved implementation. It is a
Mermaid `flowchart LR` (left-to-right); render it on GitHub, in the Streamlit app,
or via the [Mermaid Live Editor](https://mermaid.live). The two data pathways
(synthetic and real-world) feed the *same* pre-processing → feature engineering →
scaling → PCA → K-Means code, and split again only at the model-evaluation step,
because the two branches answer different, legitimate questions with different
evidence (see below).

```mermaid
flowchart LR
    START([**START**]) --> COLLECT[/**DATA COLLECTION**/<br>three provenance seams/]

    COLLECT --> ZEPHYR[**Zephyr Station**<br>/api/weather + logging<br>month → season label]
    COLLECT --> SYN[**Synthetic data**<br>generate_synthetic_data<br>archetypes known]
    COLLECT --> RW[**Real-world data**<br>dataset_adapter → realworld_ingest<br>no ground truth]

    ZEPHYR --> SYN
    ZEPHYR --> RW

    SYN --> VAL[[**DATA VALIDATION**<br>schema, duplicates, timestamps,<br>within-meter imputation]]
    RW --> VAL

    VAL --> PRE[**PRE-PROCESSING**<br>preprocess_pipeline<br>clean, impute, sort<br>drop archetype + seasonal_phase]
    PRE --> FEAT[**FEATURE ENGINEERING**<br>51 behavioural features, scale-invariant]
    FEAT --> SCALE[**FEATURE SCALING**<br>StandardScaler]
    SCALE --> PCA[**PCA**<br>variance threshold + loadings]
    PCA --> KM[**K-MEANS**<br>evidence-based K]

    KM --> XAI[**EXPLAINABILITY**<br>surrogate RF → SHAP / permutation<br>explainability.json]

    KM --> EVAL[/**MODEL EVALUATION**/]
    XAI --> EVAL

    EVAL -->|synthetic branch| ARI[**NMI / ARI vs hidden archetype**<br>+ silhouette / CH / DB<br>+ seed stability]
    EVAL -->|real-world branch| INT[**Internal only**<br>silhouette / CH / DB<br>+ seed stability + temporal stability<br>(never ARI/NMI against invented labels)]

    ARI --> VIZ[**VISUALIZATION**<br>PCA, cluster, K-selection,<br>seasonal, longitudinal charts]
    INT --> VIZ

    VIZ --> INTERP[**INTERPRETATION**<br>cluster profiles + loadings<br>+ seasonal / longitudinal findings]
    INTERP --> EXPORT[**EXPORT**<br>export_artifacts.py<br>web/public/data/*.json → Vercel]
    EXPORT --> END([**END**])
```

## The three provenance seams

- **Zephyr Station (weather).** The `season` column is not hand-typed metadata —
  it comes from a real weather station the author built and logged (firmware +
  `/api/weather` at `github.com/shaxntanu/Zephyr-Station`, logger + dashboard at
  `github.com/shaxntanu/Zephyr-Station-Dashboard`). The pipeline joins the panel
  to that weather history by month and maps `month → season`, so every
  consumer-day carries a season label before any modeling happens.
- **Synthetic (controlled).** The generator writes each consumer's hidden
  archetype and seasonal phase. Both are dropped before preprocessing; they are
  read back only after clustering to compute ARI/NMI recovery.
- **Real-world (external).** An adapter maps an external panel onto the same
  columns with documented source, citation, and unit handling. No ground-truth
  label exists, so only internal + stability metrics are reported.

## Explainability (XAI) lane

`explainability.py` runs immediately after K-Means and before profiling. A small
surrogate random forest learns the recovered cluster labels from the 51
behavioral features; attribution then runs on that surrogate — SHAP
`TreeExplainer` when `shap` is installed, permutation (one-vs-rest) otherwise.
The artifact records which method actually ran (`method: "shap" |
"permutation_fallback"`), and `cv_balanced_accuracy` is an honest ceiling, not a
claim about the clusters themselves.

## Why the two evaluation branches

- **Synthetic branch (controlled validation).** The generator writes the true
  archetype for each consumer. After clustering, we can measure recovery with
  NMI/ARI *against that hidden ground truth* — a legitimate check that only a
  dataset with known labels can provide. The labels are never used to fit the
  model.
- **Real-world branch (external validation).** A real consumption dataset has no
  ground-truth archetype. Grading it with NMI/ARI against invented groups would
  report a score the data could not have produced. Instead the real branch speaks
  in **internal** quality (silhouette / Calinski–Harabasz / Davies–Bouldin) and
  **stability** (K-Means restart agreement, and temporal stability across time
  windows) — does the recovered segmentation persist and describe real load
  shapes? Synthetic and real results are therefore reported separately and never
  mixed.

## Plain-text fallback (no rendering tool needed)

```
START
  └─► DATA COLLECTION
        ├─ ► Zephyr Station  (/api/weather + logging → month → season)
        ├─ ► Synthetic data  (archetypes known)
        └─ ► Real-world data (dataset_adapter → realworld_ingest; no ground truth)
              └─► DATA VALIDATION (schema, duplicates, timestamps, within-meter imputation)
                    └─► PRE-PROCESSING  (preprocess_pipeline: clean, impute, sort; drop archetype + seasonal_phase)
                          └─► FEATURE ENGINEERING  (51 behavioural features, scale-invariant)
                                └─► FEATURE SCALING  (StandardScaler)
                                      └─► PCA  (variance threshold + loadings)
                                            └─► K-MEANS  (evidence-based K)
                                                  └─► EXPLAINABILITY (surrogate RF → SHAP / permutation → explainability.json)
                                                        └─► MODEL EVALUATION
                                                              ├─ synthetic branch ► NMI / ARI vs hidden archetype + silhouette/CH/DB + seed stability
                                                              └─ real-world branch ► internal only (silhouette/CH/DB + seed + temporal stability)
                                                                    └─► VISUALIZATION
                                                                          └─► INTERPRETATION
                                                                                └─► EXPORT (export_artifacts.py → web/public/data/*.json → Vercel)
                                                                                      └─► END
```
