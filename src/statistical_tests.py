"""
Statistical Testing Module

Implements statistical tests for between-cluster differences in features.
This addresses reviewer requirement M3 for rigorous validation of cluster
differences with appropriate effect sizes and p-values.
"""

import logging
from typing import Dict, List, Optional, Tuple

import numpy as np
import pandas as pd
from scipy import stats
from scipy.stats import f_oneway, kruskal

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def test_between_cluster_differences(
    features_df: pd.DataFrame,
    cluster_labels: np.ndarray,
    alpha: float = 0.05
) -> pd.DataFrame:
    """Perform statistical tests for each feature across clusters.

    For each feature, performs:
    - Kruskal-Wallis test (non-parametric, robust to non-normality)
    - Effect size (eta-squared for Kruskal-Wallis)
    - Post-hoc pairwise Mann-Whitney U tests with Holm-Bonferroni correction

    Args:
        features_df: DataFrame with features as columns, consumers as rows
        cluster_labels: Cluster assignment for each consumer
        alpha: Significance level for tests

    Returns:
        DataFrame with one row per feature containing test statistics,
        p-values, effect sizes, and significance flags.
    """
    logger.info("Performing between-cluster statistical tests")

    unique_clusters = np.unique(cluster_labels)
    n_clusters = len(unique_clusters)

    if n_clusters < 2:
        raise ValueError(f"Need at least 2 clusters for testing, got {n_clusters}")

    results = []

    for feature in features_df.columns:
        # Split feature by cluster
        groups = [features_df[cluster_labels == k][feature].values for k in unique_clusters]

        # Kruskal-Wallis test (non-parametric ANOVA)
        try:
            stat, p_value = kruskal(*groups)
        except ValueError as e:
            logger.warning(f"Kruskal-Wallis failed for {feature}: {e}")
            stat, p_value = np.nan, np.nan

        # Effect size (eta-squared for Kruskal-Wallis)
        # H / (N - 1) where H is Kruskal-Wallis statistic
        n_total = len(features_df)
        eta_squared = stat / (n_total - 1) if not np.isnan(stat) else np.nan

        # Effect size interpretation
        if not np.isnan(eta_squared):
            if eta_squared < 0.01:
                effect_size = "negligible"
            elif eta_squared < 0.06:
                effect_size = "small"
            elif eta_squared < 0.14:
                effect_size = "medium"
            else:
                effect_size = "large"
        else:
            effect_size = "unknown"

        # Post-hoc pairwise Mann-Whitney U tests
        pairwise_results = []
        for i in range(n_clusters):
            for j in range(i + 1, n_clusters):
                try:
                    u_stat, p_pair = stats.mannwhitneyu(
                        groups[i], groups[j], alternative='two-sided'
                    )
                    pairwise_results.append({
                        'cluster_i': unique_clusters[i],
                        'cluster_j': unique_clusters[j],
                        'u_statistic': u_stat,
                        'p_value': p_pair
                    })
                except ValueError as e:
                    logger.warning(f"Mann-Whitney U failed for {feature} clusters {i}-{j}: {e}")

        # Holm-Bonferroni correction for pairwise tests
        if pairwise_results:
            p_values = [r['p_value'] for r in pairwise_results]
            # Implement Holm-Bonferroni correction manually
            sorted_indices = np.argsort(p_values)
            sorted_p = np.array(p_values)[sorted_indices]
            n_tests = len(p_values)

            p_corrected = np.ones(n_tests)
            for i, idx in enumerate(sorted_indices):
                # Holm step-down: compare to alpha / (n - i)
                p_corrected[idx] = min(1.0, sorted_p[i] * (n_tests - i))

            rejected = p_corrected < alpha

            for idx, r in enumerate(pairwise_results):
                r['p_corrected'] = float(p_corrected[idx])
                r['significant'] = bool(rejected[idx])

        results.append({
            'feature': feature,
            'kruskal_statistic': stat,
            'kruskal_p_value': p_value,
            'eta_squared': eta_squared,
            'effect_size': effect_size,
            'significant': p_value < alpha if not np.isnan(p_value) else False,
            'pairwise_tests': pairwise_results
        })

        logger.info(f"  {feature}: H={stat:.3f}, p={p_value:.4f}, η²={eta_squared:.3f}")

    return pd.DataFrame(results)


def summarize_statistical_results(test_results: pd.DataFrame) -> Dict:
    """Summarize statistical testing results.

    Args:
        test_results: Output from test_between_cluster_differences

    Returns:
        Dictionary with summary statistics
    """
    n_features = len(test_results)
    n_significant = int(test_results['significant'].sum())

    effect_size_counts = test_results['effect_size'].value_counts().to_dict()
    # Convert numpy types to native Python types for JSON serialization
    effect_size_counts = {k: int(v) if isinstance(v, (np.integer, np.int64)) else v
                         for k, v in effect_size_counts.items()}

    summary = {
        'n_features_tested': int(n_features),
        'n_significant': n_significant,
        'proportion_significant': float(n_significant / n_features if n_features > 0 else 0),
        'effect_size_distribution': effect_size_counts,
        'median_eta_squared': float(test_results['eta_squared'].median()),
        'mean_eta_squared': float(test_results['eta_squared'].mean())
    }

    return summary


def export_statistical_results(
    test_results: pd.DataFrame,
    summary: Dict,
    output_dir: str = 'outputs/metrics'
) -> None:
    """Export statistical test results to CSV and summary to JSON.

    Args:
        test_results: DataFrame from test_between_cluster_differences
        summary: Summary dictionary from summarize_statistical_results
        output_dir: Directory to save outputs
    """
    from pathlib import Path
    import json

    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    # Save full results
    # Flatten pairwise tests for CSV export
    flat_results = []
    for _, row in test_results.iterrows():
        base_row = {
            'feature': row['feature'],
            'kruskal_statistic': float(row['kruskal_statistic']) if not np.isnan(row['kruskal_statistic']) else None,
            'kruskal_p_value': float(row['kruskal_p_value']) if not np.isnan(row['kruskal_p_value']) else None,
            'eta_squared': float(row['eta_squared']) if not np.isnan(row['eta_squared']) else None,
            'effect_size': row['effect_size'],
            'significant': bool(row['significant'])
        }
        flat_results.append(base_row)

    pd.DataFrame(flat_results).to_csv(
        output_path / 'statistical_tests.csv',
        index=False
    )

    # Save summary
    with open(output_path / 'statistical_tests_summary.json', 'w') as f:
        json.dump(summary, f, indent=2, default=str)

    logger.info(f"Statistical test results saved to {output_path}")


if __name__ == '__main__':
    # Test with synthetic data
    np.random.seed(42)
    n_samples = 200
    n_features = 10

    # Generate synthetic features with some cluster differences
    features = np.random.randn(n_samples, n_features)
    features[:100, 0] += 1.0  # Feature 0 differs between clusters
    features[:100, 1] += 0.5  # Feature 1 differs slightly

    feature_names = [f'feature_{i}' for i in range(n_features)]
    features_df = pd.DataFrame(features, columns=feature_names)
    cluster_labels = np.array([0] * 100 + [1] * 100)

    results = test_between_cluster_differences(features_df, cluster_labels)
    summary = summarize_statistical_results(results)

    print("\nStatistical Test Results:")
    print(results[['feature', 'kruskal_p_value', 'eta_squared', 'effect_size', 'significant']])
    print("\nSummary:", summary)
