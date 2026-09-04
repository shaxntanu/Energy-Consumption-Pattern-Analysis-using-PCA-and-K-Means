# Explainability Report (Improvement 4: XAI / SHAP)

The clustering itself is unsupervised and has no feature importance. A
small, shallow random forest was therefore fitted AFTER clustering to
predict the recovered cluster labels from the same 51 behavioural features
the pipeline used. Method: **shap**.

- Surrogate: RandomForestClassifier (post-hoc, never feeds back into PCA
  or K-Means)
- Consumers explained: 200, features: 51
- Cross-validated balanced accuracy of the surrogate: 0.985

This accuracy is the honest ceiling on feature-importance claims: if the
surrogate predicts most memberships, the features genuinely carry the
grouping; if it does not, the clusters are driven by structure the
features do not capture and no importance table can manufacture it.

## SHAP (TreeExplainer)

Per cluster, the ten features with the largest mean |SHAP| are listed.
The direction column says whether a HIGHER value of the feature pushes a
consumer INTO the cluster or AWAY from it.

### Cluster 0 (39 consumers)
- `evening_share` importance 0.0892 (pushes into)
- `hour_12_shape` importance 0.0805 (pushes into)
- `hour_11_shape` importance 0.0472 (pushes into)
- `hour_13_shape` importance 0.0448 (pushes into)
- `hour_20_shape` importance 0.0349 (pushes into)
- `hour_1_shape` importance 0.0324 (pushes into)
- `harmonic_2_amplitude` importance 0.0319 (pushes into)
- `hour_23_shape` importance 0.0236 (pushes into)
- `weekend_ratio` importance 0.0218 (pushes into)
- `hour_21_shape` importance 0.0215 (pushes into)

### Cluster 1 (52 consumers)
- `peak_concentration` importance 0.0864 (pushes into)
- `hour_3_shape` importance 0.0690 (pushes into)
- `shape_entropy` importance 0.0658 (pushes into)
- `p90_median_ratio` importance 0.0613 (pushes into)
- `base_load_share` importance 0.0601 (pushes into)
- `profile_ramp` importance 0.0576 (pushes into)
- `shape_gini` importance 0.0534 (pushes into)
- `hour_4_shape` importance 0.0473 (pushes into)
- `coefficient_of_variation` importance 0.0428 (pushes into)
- `haar_detail_l1` importance 0.0421 (pushes into)

### Cluster 2 (47 consumers)
- `hour_13_shape` importance 0.1124 (pushes into)
- `harmonic_2_amplitude` importance 0.1100 (pushes into)
- `hour_11_shape` importance 0.0589 (pushes into)
- `hour_12_shape` importance 0.0585 (pushes into)
- `profile_ramp` importance 0.0534 (pushes into)
- `hour_14_shape` importance 0.0496 (pushes into)
- `haar_detail_l1` importance 0.0262 (pushes into)
- `hour_20_shape` importance 0.0243 (pushes into)
- `haar_detail_l2` importance 0.0235 (pushes into)
- `peak_concentration` importance 0.0231 (pushes into)

### Cluster 3 (62 consumers)
- `hour_13_shape` importance 0.0492 (pushes into)
- `hour_12_shape` importance 0.0492 (pushes into)
- `harmonic_2_amplitude` importance 0.0417 (pushes into)
- `evening_share` importance 0.0415 (pushes into)
- `profile_ramp` importance 0.0405 (pushes into)
- `hour_11_shape` importance 0.0375 (pushes into)
- `weekend_ratio` importance 0.0262 (pushes into)
- `peak_concentration` importance 0.0249 (pushes into)
- `shape_entropy` importance 0.0216 (pushes into)
- `hour_3_shape` importance 0.0213 (pushes into)

## Global picture

The features that separate the clusters most overall:

- `hour_13_shape` 0.0307
- `harmonic_2_amplitude` 0.0289
- `hour_12_shape` 0.0273
- `profile_ramp` 0.0244
- `peak_concentration` 0.0235
- `evening_share` 0.0217
- `hour_11_shape` 0.0215
- `hour_3_shape` 0.0190
- `shape_entropy` 0.0175
- `p90_median_ratio` 0.0173
- `base_load_share` 0.0163
- `shape_gini` 0.0146
- `haar_detail_l1` 0.0143
- `hour_14_shape` 0.0130
- `hour_4_shape` 0.0114

Caveats: this is a post-hoc interpretation of an unsupervised grouping,
not a causal analysis. The features were standardized before the surrogate
was fitted, so importance is comparable across features. SHAP values and
permutation importance are different statistics and must not be compared
against each other; the method key above states which one produced this
report.
