# Explainability Report (Improvement 4: XAI / SHAP)

The clustering itself is unsupervised and has no feature importance. A
small, shallow random forest was therefore fitted AFTER clustering to
predict the recovered cluster labels from the same 51 behavioural features
the pipeline used. Method: **shap**.

- Surrogate: RandomForestClassifier (post-hoc, never feeds back into PCA
  or K-Means)
- Consumers explained: 200, features: 51
- Cross-validated balanced accuracy of the surrogate: 0.983

This accuracy is the honest ceiling on feature-importance claims: if the
surrogate predicts most memberships, the features genuinely carry the
grouping; if it does not, the clusters are driven by structure the
features do not capture and no importance table can manufacture it.

## SHAP (TreeExplainer)

Per cluster, the ten features with the largest mean |SHAP| are listed.
The direction column says whether a HIGHER value of the feature pushes a
consumer INTO the cluster or AWAY from it.

### Cluster 0 (144 consumers)
- `night_share` importance 0.0386 (pushes into)
- `shape_entropy` importance 0.0285 (pushes into)
- `peak_concentration` importance 0.0218 (pushes into)
- `hour_2_shape` importance 0.0214 (pushes into)
- `base_load_share` importance 0.0211 (pushes into)
- `hour_3_shape` importance 0.0204 (pushes into)
- `shape_gini` importance 0.0202 (pushes into)
- `profile_ramp` importance 0.0195 (pushes into)
- `harmonic_1_amplitude` importance 0.0144 (pushes into)
- `hour_4_shape` importance 0.0097 (pushes into)

### Cluster 1 (56 consumers)
- `night_share` importance 0.1049 (pushes into)
- `shape_entropy` importance 0.0922 (pushes into)
- `shape_gini` importance 0.0870 (pushes into)
- `peak_concentration` importance 0.0634 (pushes into)
- `hour_3_shape` importance 0.0526 (pushes into)
- `base_load_share` importance 0.0504 (pushes into)
- `harmonic_1_amplitude` importance 0.0474 (pushes into)
- `hour_2_shape` importance 0.0472 (pushes into)
- `profile_ramp` importance 0.0387 (pushes into)
- `night_day_ratio` importance 0.0269 (pushes into)

## Global picture

The features that separate the clusters most overall:

- `night_share` 0.0572
- `shape_entropy` 0.0463
- `shape_gini` 0.0389
- `peak_concentration` 0.0334
- `hour_3_shape` 0.0294
- `base_load_share` 0.0293
- `hour_2_shape` 0.0286
- `profile_ramp` 0.0249
- `harmonic_1_amplitude` 0.0236
- `night_day_ratio` 0.0138
- `hour_4_shape` 0.0113
- `hour_5_shape` 0.0112
- `hour_1_shape` 0.0095
- `p90_median_ratio` 0.0084
- `coefficient_of_variation` 0.0065

Caveats: this is a post-hoc interpretation of an unsupervised grouping,
not a causal analysis. The features were standardized before the surrogate
was fitted, so importance is comparable across features. SHAP values and
permutation importance are different statistics and must not be compared
against each other; the method key above states which one produced this
report.
