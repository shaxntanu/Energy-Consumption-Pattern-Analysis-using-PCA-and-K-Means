# Results

Exact numbers from the two verified runs of the PCA + K-Means energy-clustering
pipeline. Run 1 is a quick 30-day sanity check; Run 2 is the one-year flagship
whose outputs the web app (`web/`), the Streamlit dashboard, and the generated
reports quote.

Every number below comes from one of three sources, quoted verbatim:

- the run logs (user-verified runs of `py run_module.py energy_analysis`),
- the run's own artifacts (`models/analysis_metadata.json`,
  `outputs/metrics/*.json`, `web/public/data/*.json`, contract_version 1.0.0).

The pipeline never invents numbers: when a step cannot run at a horizon it
writes `available: false` with a reason.

---

## 1. The two runs at a glance

| Metric | Run 1 (30 days) | Run 2 (365 days) |
| --- | --- | --- |
| Config hash | `6896387297178841` | `99c7a6631340d301` |
| Consumers × days | 200 × 30 | 200 × 365 |
| Hourly records | 144,000 | 1,752,000 |
| Window | 2024-01-01 to 2024-01-30 (January, winter only) | 2024-01-01 to 2024-12-30 (all four seasons) |
| Behavioural features | 51 | 51 |
| PCA components retained | 14 | 10 |
| PCA cumulative variance | 0.9546571551695007 | 0.9504940204193212 |
| Selected K | 3 | 4 |
| Silhouette at selected K | 0.31341719198840434 | 0.3282866716821562 |
| Cluster sizes | 55 / 86 / 59 | 39 / 52 / 47 / 62 |
| Stability ARI (10 seed re-runs) | 0.9910880350432792 | 0.9946825377900362 |
| ARI vs hidden archetypes | 0.5851806573404174 | 0.812671365105634 |
| NMI vs hidden archetypes | n/a (log reports ARI) | 0.8284123219399838 |
| Explainability method | shap | shap |
| Surrogate cv balanced accuracy | 0.9905228758169935 | 0.9845833333333334 |
| Recommendations emitted | 8 | 11 |
| Seasonal model | skipped by design (one season present) | amplitude 0.202, phase r 0.678, agreement 0.885 |
| Longitudinal stability | not run (< 180 days) | mean ARI 0.8817 across 4 quarters |

---

## 2. How a run is defined

`config_hash` identifies the exact trial: the random seed, consumer count, day
count, and every model parameter. The same hash regenerates the same synthetic
population and the same analysis, which is why the web app can quote the
flagship run (`99c7a6631340d301`) as a reproducible demo.

Pipeline order: synthetic data → preprocessing → 51 behavioural features →
standardize → PCA (0.95 variance threshold) → K-Means over K = 2..10 with a
composite selection rule → stability re-runs → validation against the hidden
archetypes (ARI / NMI) → profiling → recommendations → explainability (SHAP on
a post-hoc surrogate) → seasonal model → longitudinal stability.

---

## 3. Run 1: 30-day verification run (config `6896387297178841`)

### Data
- 200 consumers × 30 days × 24 hours = **144,000** hourly records.
- The window is a single January month, so every day falls in winter.

### PCA
- Components retained: **14**.
- Cumulative variance: **0.9546571551695007** (95.5%).

### K selection and clusters
- Selected K: **3** (wins the same composite rule used in Run 2).
- Silhouette at K = 3: **0.31341719198840434**.
- Cluster sizes: **55 / 86 / 59** (sum 200).

### Stability and validation
- Stability ARI across 10 seed re-runs: **0.9910880350432792**.
- ARI vs the hidden archetypes: **0.5851806573404174** (modest; at one month
  the archetypes are less distinguishable than over a full year).

### Explainability
- Method: **shap** (TreeExplainer on a post-hoc surrogate forest).
- Surrogate 5-fold balanced accuracy: **0.9905228758169935**.

### Recommendations
- **8** recommendations emitted.

### Seasonal and longitudinal
- **Seasonal: skipped, by design.** The season guard requires at least two
  distinct seasons, and the 30-day window contains only winter. The step
  reports `available: false` with its reason instead of inventing an amplitude.
- **Longitudinal: not run.** The longitudinal step needs at least 180 days of
  history.

---

## 4. Run 2: 365-day flagship run (config `99c7a6631340d301`)

This is the run the web app, dashboard, and reports quote.

### Data
- 200 consumers × 365 days × 24 hours = **1,752,000** hourly records.
- Window: 2024-01-01 to 2024-12-30. All four seasons present.
- What the generator injected (from `models/analysis_metadata.json`):
  - seasonal model enabled, **annual amplitude 0.25** (a ±25% swing in mean
    daily totals),
  - **shape shift: 1.0 hour** (the 24-hour profile drifts by season),
  - hemisphere: northern, phase std 20 days, participation 0.9 (90% of
    consumers carry a seasonal phase).

### Features
- **51** behavioural descriptors: 24 hourly shape loads (`hour_0_shape` ..
  `hour_23_shape`) plus 27 aggregates (day-period shares, peak hour
  sin/cos encoding, weekend ratio, base load share, harmonics, Haar details,
  shape entropy/Gini, coefficient of variation, skewness, kurtosis, and more).

### PCA (threshold 0.95 → 10 components)

| Component | Explained variance | Cumulative |
| --- | --- | --- |
| 1 | 0.3393589736304491 | 0.3393589736304491 |
| 2 | 0.2896374894211358 | 0.628996463051585 |
| 3 | 0.1152220857431529 | 0.7442185487947379 |
| 4 | 0.0629754975130199 | 0.8071940463077578 |
| 5 | 0.0441318420899465 | 0.8513258883977044 |
| 6 | 0.0367080347587931 | 0.8880339231564975 |
| 7 | 0.0203657375520792 | 0.9083996607085768 |
| 8 | 0.0173931459042709 | 0.9257928066128476 |
| 9 | 0.012733641753139 | 0.9385264483659868 |
| 10 | 0.0119675720533344 | **0.9504940204193212** |

The first component alone takes 33.9% of the variance; the first two take
62.9%, and ten components cross the 95% line at 0.9504940204193212. What the
leading components mean (top loadings, `pca.json`):

| Component | Reads as | Top loadings |
| --- | --- | --- |
| PC1 | overall peak intensity | profile_ramp +0.92, peak_concentration +0.88, harmonic_2_amplitude +0.88, p90_median_ratio +0.87, coefficient_of_variation +0.87 |
| PC2 | night vs afternoon split | night_day_ratio +0.92, afternoon_share -0.87, hour_0_shape +0.84, hour_14_shape -0.84, hour_13_shape -0.84 |
| PC3 | morning slide | hour_7_shape +0.87, hour_8_shape +0.87, hour_6_shape +0.74, morning_share +0.74, hour_9_shape +0.58 |
| PC4 | early-evening detail | hour_17_shape +0.56, hour_18_shape +0.54, hour_6_shape +0.50, hour_5_shape +0.47, hour_23_shape -0.43 |
| PC5 | weekend and fat tails | haar_detail_l3 +0.54, weekend_ratio -0.51, kurtosis -0.38, skewness -0.38, weekend_cv_ratio -0.37 |

### K sweep (K = 2..10)

Selection rules: minimum cluster share 0.05, minimum stability ARI 0.6,
tolerance 0.05 on the composite score. After the balance and stability filters
the candidates were K = 2, 3, 4, 5, 6.

| K | Silhouette | Calinski–Harabasz | Davies–Bouldin | Composite score | Selected |
| --- | --- | --- | --- | --- | --- |
| 2 | 0.2939437518225455 | 72.99794655833404 | 1.3822966460504686 | 0.0 | no |
| 3 | 0.3304803853115014 | 93.70183384832148 | 1.1957217149422932 | 0.8793882016453002 | no |
| 4 | 0.3282866716821562 | 96.61713813497728 | 1.1691088459670895 | 0.9444015542811052 | **yes** |
| 5 | 0.3351616198820151 | 87.60960036721217 | 1.2022910731297736 | 0.8209956423863121 | no |
| 6 | 0.3238272599743667 | 83.63056709531355 | 1.2326497885903491 | 0.6257102103179557 | no |
| 7 | 0.3163754755774248 | 77.4660341569839 | 1.2093826125596194 | n/a | no |
| 8 | 0.307163232659902 | 72.15634316539739 | 1.2949651245042757 | n/a | no |
| 9 | 0.3111422698892226 | 69.06249696773054 | 1.2014875963732292 | n/a | no |
| 10 | 0.275952781244082 | 65.55485378866058 | 1.317966836217035 | n/a | no |

Composite scores exist only for K = 2..6: K = 7..10 are removed by the balance
filter before scoring (their smallest clusters fall below the 0.05 minimum
share: 0.035, 0.03, 0.025, 0.02).

K = 5 has the highest raw silhouette (0.3351616198820151), but K = 4 wins the
composite score (0.9444015542811052) and is the only candidate within tolerance
of the best score, so **K = 4 is selected**.

### The four clusters

| Cluster | Size | Name | Peak hour | CoV (shape variation) |
| --- | --- | --- | --- | --- |
| 0 | 39 | Midday-Peaking Weekday-Heavy | 13:00 | 0.620288 |
| 1 | 52 | Flat All-Day | 19:00 | 0.302007 |
| 2 | 47 | Evening-Peaking | 20:00 | 0.705483 |
| 3 | 62 | Evening-Peaking Weekend-Heavy | 19:00 | 0.596236 |

Sizes sum to 200 (0.195 / 0.26 / 0.235 / 0.31 of the panel).

### Stability at K = 4 (10 seed re-runs)

- Mean ARI: **0.9946825377900362**
- Std ARI: 0.007081574699310825
- Min ARI: 0.9736152071869171
- Mean label agreement: 0.9979999999999998
- Mean inertia: 3911.265733297244 (std 0.31660704832315845)

The grouping is effectively seed-independent.

### Validation against the hidden archetypes

- ARI at K = 4: **0.812671365105634**
- NMI at K = 4: **0.8284123219399838**
- Best recovery K = 4.

### Explainability (XAI)

- Method: **shap** (TreeExplainer on a post-hoc surrogate random forest; the
  surrogate never feeds back into the clustering).
- Surrogate 5-fold balanced accuracy: **0.9845833333333334** - the honest
  ceiling on how much the features explain the grouping.
- Global mean |SHAP| feature importance:

| Feature | Mean |SHAP| |
| --- | --- |
| hour_13_shape | 0.0306547832019624 |
| harmonic_2_amplitude | 0.028862609318888368 |
| hour_12_shape | 0.027277469175574692 |
| profile_ramp | 0.024374341448414816 |
| peak_concentration | 0.023480336280210342 |
| evening_share | 0.021748385317758388 |

How much of the daily shape a household spends at hour 13 and hour 12, and how
strong its second harmonic (dinner-hour swing) is, separate the clusters more
than any other feature; the afternoon ramp, peak concentration and evening
share follow.

### Recommendations

- **11** recommendations emitted from the cluster profiles.

### Seasonal model (Improvement 2)

The synthetic generator injected a ±25% swing in mean daily totals and a
1-hour timing shift. The seasonal step separates the two channels and scores
both against the hidden truth:

- **Amplitude estimate: 0.20178864227863696** (0.202) against an injected
  0.25. Across all **200** consumers the 68% spread of the per-consumer
  estimates is:
  - q25: **0.1785855522965766**
  - q75: **0.2161481442491843**
- **Phase recovery: r = 0.6780669314235555** (0.678) - the estimated seasonal
  phase correlates with the hidden `seasonal_phase`. Positive, and expected to
  be modest rather than near-perfect: the module says so in its own docs.
- **Peak-season agreement: 0.885** on the **185** consumers whose hidden phase
  is known.
- Mean daily kWh by season:

| Season | Mean daily kWh | Peak hour |
| --- | --- | --- |
| winter | 26.571 | 19:00 |
| spring | 35.1668 | 20:00 |
| summer | 38.0142 | 20:00 |
| autumn | 29.433 | 19:00 |

Summer is the highest-mean season (38.0142), winter the lowest (26.571); the
24-hour peak sits late (19:00-20:00) in every season.

### Longitudinal stability (Improvement 1)

Four non-overlapping quarterly windows each re-run the full chain
(scaling → PCA → K selection) independently and are compared with the
full-window partition (permutation-invariant ARI):

| Window | Dates | ARI |
| --- | --- | --- |
| Q1 | 2024-01-01 to 2024-04-01 | 0.837784535882258 |
| Q2 | 2024-04-01 to 2024-07-01 | 0.8923577410330173 |
| Q3 | 2024-07-01 to 2024-09-30 | 0.945638839182731 |
| Q4 | 2024-09-30 to 2024-12-30 | 0.8509767826476764 |

- Mean ARI: **0.8816894746864208** (0.882).

---

## 5. Real-world demo panel (CASE A)

The audited demo panel (24 meters over the real ingestion pathway):
- **24** meters, **12,096** meter-hours, **51** features.
- PCA kept **5** components at **95.5%** variance.
- Selected K = **2**.
- Silhouette **0.7194**, Calinski–Harabasz **123.2**, Davies–Bouldin **0.3966**.
- Seed stability **1.0**, temporal stability **1.0**.

The real branch reports internal quality and stability only. It never reports
ARI/NMI - there are no invented labels to validate against.

---

## 6. Honesty notes

- **Short horizons degrade gracefully.** At 30 days the seasonal step is
  skipped with `available: false` + reason (one season present) and the
  longitudinal step does not run (< 180 days). Neither fabricates numbers.
- **Surrogate accuracy is the ceiling.** The shap values explain a 98.5%
  accurate surrogate of the recovered labels - that says the features carry
  the grouping, not that the grouping is causal.
- **Synthetic by design.** Both runs use the controlled synthetic panel so the
  hidden archetypes, phases, and injected seasonal swing exist to validate
  against. Results demonstrate the method; the real-world pathway is the
  audited adapter in README and `streamlit_app.py`.

---

## 7. Reproducing

From the repository root (Windows, `py` launcher):

```powershell
# Run 1 (30 days)
py run_module.py energy_analysis

# Run 2 (365 days, flagship)
py run_module.py energy_analysis -- --n_days 365 --n_consumers 200
```

Environment used for Run 2 (from `models/analysis_metadata.json`): Python
3.x running pandas 3.0.0, numpy 2.3.5, scikit-learn 1.9.0, scipy 1.18.0,
matplotlib 3.10.8, seaborn 0.13.2, plotly 6.5.2, streamlit 1.62.0,
joblib 1.5.3.

---

## 8. Artifacts

- `models/analysis_metadata.json` - the authoritative run record (config,
  outputs, package versions).
- `outputs/metrics/*.json` - clustering, PCA, validation, explainability,
  seasonal, longitudinal metrics.
- `outputs/reports/analysis_summary.md` - generated narrative report.
- `web/public/data/*.json` - the contract files the web app renders
  (`seasonal.json`, `longitudinal.json`, `explainability.json`, `clusters.json`,
  `pca.json`, `clustering.json`, `profiles.json`, `manifest.json`).
- `web/public/results/dark/*.png` and `outputs/figures/*.png` - the figures,
  including the three seasonal charts shown in the web app's Seasons band.