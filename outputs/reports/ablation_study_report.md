# Ablation Study Report

## Objective
Compare clustering performance across different feature engineering approaches
to identify which feature set yields the most meaningful, stable clusters.

## Feature Sets Compared
- **behavioral**: Shape-only features (normalized 24h profiles, temporal patterns, variability metrics)
- **scale**: Magnitude features (mean, max, sum, electrical features)
- **combined**: Both behavioral and scale features

## Metrics
- **Optimal K**: Number of clusters selected by multi-metric consensus
- **Silhouette**: Higher is better (cluster separation)
- **Calinski-Harabasz**: Higher is better (cluster compactness/separation)
- **Davies-Bouldin**: Lower is better (cluster similarity)
- **Stability (ARI)**: Higher is better (consistency across runs)
- **Cluster Balance**: Ratio of smallest to largest cluster (closer to 1 is better)

## Results

feature_set  n_features  n_pca_components  optimal_k  silhouette_at_optimal  ch_at_optimal  db_at_optimal  stability_mean_ari  stability_std_ari cluster_sizes  cluster_balance
 behavioral          34                25          2               0.105452      16.600412       3.291335            0.791333           0.111042     [135  65]         0.481481
      scale          10                 5          2               0.353986     128.842140       1.086562            1.000000           0.000000     [ 89 111]         0.801802
   combined          43                27          2               0.103598      25.993786       2.677429            1.000000           0.000000     [ 93 107]         0.869159

## Analysis

**Best Silhouette Score**: scale (0.3540)
**Best Stability**: scale (ARI=1.0000)
**Best Cluster Balance**: combined (balance=0.8692)

## Recommendation

**Primary Feature Set (for this project)**: behavioral
**Rationale**: Project objective is usage-pattern segmentation. Scale often wins raw silhouette because magnitude separates cleanly; behavioral is the scientifically correct primary experiment.

Metric leaders — silhouette: scale (0.3540); stability: scale (ARI=1.0000); balance: combined (0.8692). Higher scale metrics demonstrate the magnitude baseline, not the preferred story.

## Conclusion
Use **behavioral** features for the final analysis and viva defense.
Report scale/combined as ablation controls that show why feature engineering
changes the question from 'who consumes more?' to 'how do consumers consume differently?'.