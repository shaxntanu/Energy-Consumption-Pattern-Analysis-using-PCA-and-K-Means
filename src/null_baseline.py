"""
Null Baseline Module

Implements null model comparisons for clustering structure validation.
This addresses reviewer requirement M5 for testing whether observed clustering
is meaningfully stronger than what would arise under an appropriate null model.
"""

import logging
from typing import Dict, List, Optional

import numpy as np
import pandas as pd
from sklearn.cluster import KMeans
from sklearn.metrics import (
    adjusted_rand_score,
    calinski_harabasz_score,
    davies_bouldin_score,
    silhouette_score,
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def permutation_null_baseline(
    X: np.ndarray,
    n_clusters: int,
    n_permutations: int = 100,
    random_state: int = 42,
    n_init: int = 10
) -> Dict:
    """Generate null distribution of clustering metrics via label permutation.

    This tests whether the observed cluster structure is stronger than what
    would arise from randomly permuting the cluster labels while keeping
    the data fixed.

    Args:
        X: Feature matrix (n_samples, n_features)
        n_clusters: Number of clusters to use
        n_permutations: Number of random permutations
        random_state: Random seed
        n_init: Number of K-means initializations

    Returns:
        Dictionary with null distributions for silhouette, CH, and DB scores
    """
    logger.info(f"Generating permutation null baseline with {n_permutations} permutations")

    rng = np.random.RandomState(random_state)

    # Fit actual clustering to get observed metrics
    kmeans = KMeans(n_clusters=n_clusters, random_state=random_state, n_init=n_init)
    labels = kmeans.fit_predict(X)

    observed_silhouette = silhouette_score(X, labels)
    observed_ch = calinski_harabasz_score(X, labels)
    observed_db = davies_bouldin_score(X, labels)

    logger.info(f"Observed metrics: silhouette={observed_silhouette:.4f}, CH={observed_ch:.4f}, DB={observed_db:.4f}")

    # Generate null distribution by permuting labels
    null_silhouette = []
    null_ch = []
    null_db = []

    for i in range(n_permutations):
        permuted_labels = rng.permutation(labels)

        try:
            s = silhouette_score(X, permuted_labels)
            null_silhouette.append(s)
        except ValueError:
            null_silhouette.append(np.nan)

        try:
            ch = calinski_harabasz_score(X, permuted_labels)
            null_ch.append(ch)
        except ValueError:
            null_ch.append(np.nan)

        try:
            db = davies_bouldin_score(X, permuted_labels)
            null_db.append(db)
        except ValueError:
            null_db.append(np.nan)

        if (i + 1) % 20 == 0:
            logger.info(f"  Completed {i + 1}/{n_permutations} permutations")

    # Compute p-values (proportion of null scores as extreme as observed)
    # For silhouette and CH: higher is better, so p = (null >= observed) / n
    # For DB: lower is better, so p = (null <= observed) / n
    silhouette_p = np.mean(np.array(null_silhouette) >= observed_silhouette)
    ch_p = np.mean(np.array(null_ch) >= observed_ch)
    db_p = np.mean(np.array(null_db) <= observed_db)

    results = {
        'n_permutations': n_permutations,
        'observed_silhouette': observed_silhouette,
        'observed_calinski_harabasz': observed_ch,
        'observed_davies_bouldin': observed_db,
        'null_silhouette_mean': np.mean(null_silhouette),
        'null_silhouette_std': np.std(null_silhouette),
        'null_ch_mean': np.mean(null_ch),
        'null_ch_std': np.std(null_ch),
        'null_db_mean': np.mean(null_db),
        'null_db_std': np.std(null_db),
        'silhouette_p_value': silhouette_p,
        'ch_p_value': ch_p,
        'db_p_value': db_p,
        'null_silhouette_distribution': null_silhouette,
        'null_ch_distribution': null_ch,
        'null_db_distribution': null_db
    }

    logger.info(f"Null baseline complete. Silhouette p={silhouette_p:.4f}, CH p={ch_p:.4f}, DB p={db_p:.4f}")

    return results


def uniform_random_baseline(
    X: np.ndarray,
    n_clusters: int,
    n_simulations: int = 100,
    random_state: int = 42,
    n_init: int = 10
) -> Dict:
    """Generate null distribution by clustering uniformly random data.

    This tests whether the observed clustering structure is stronger than
    what would arise from clustering data with no structure (uniform random).

    Args:
        X: Feature matrix (n_samples, n_features) - used for shape only
        n_clusters: Number of clusters
        n_simulations: Number of random datasets to generate
        random_state: Random seed
        n_init: Number of K-means initializations

    Returns:
        Dictionary with null distributions
    """
    logger.info(f"Generating uniform random baseline with {n_simulations} simulations")

    rng = np.random.RandomState(random_state)
    n_samples, n_features = X.shape

    # Fit actual clustering to get observed metrics
    kmeans = KMeans(n_clusters=n_clusters, random_state=random_state, n_init=n_init)
    labels = kmeans.fit_predict(X)

    observed_silhouette = silhouette_score(X, labels)
    observed_ch = calinski_harabasz_score(X, labels)
    observed_db = davies_bouldin_score(X, labels)

    logger.info(f"Observed metrics: silhouette={observed_silhouette:.4f}, CH={observed_ch:.4f}, DB={observed_db:.4f}")

    # Generate null distribution from uniform random data
    null_silhouette = []
    null_ch = []
    null_db = []

    for i in range(n_simulations):
        # Generate uniform random data with same shape
        X_random = rng.uniform(low=X.min(), high=X.max(), size=X.shape)

        kmeans_random = KMeans(n_clusters=n_clusters, random_state=random_state + i, n_init=n_init)
        labels_random = kmeans_random.fit_predict(X_random)

        try:
            s = silhouette_score(X_random, labels_random)
            null_silhouette.append(s)
        except ValueError:
            null_silhouette.append(np.nan)

        try:
            ch = calinski_harabasz_score(X_random, labels_random)
            null_ch.append(ch)
        except ValueError:
            null_ch.append(np.nan)

        try:
            db = davies_bouldin_score(X_random, labels_random)
            null_db.append(db)
        except ValueError:
            null_db.append(np.nan)

        if (i + 1) % 20 == 0:
            logger.info(f"  Completed {i + 1}/{n_simulations} simulations")

    # Compute p-values
    silhouette_p = np.mean(np.array(null_silhouette) >= observed_silhouette)
    ch_p = np.mean(np.array(null_ch) >= observed_ch)
    db_p = np.mean(np.array(null_db) <= observed_db)

    results = {
        'n_simulations': n_simulations,
        'observed_silhouette': observed_silhouette,
        'observed_calinski_harabasz': observed_ch,
        'observed_davies_bouldin': observed_db,
        'null_silhouette_mean': np.mean(null_silhouette),
        'null_silhouette_std': np.std(null_silhouette),
        'null_ch_mean': np.mean(null_ch),
        'null_ch_std': np.std(null_ch),
        'null_db_mean': np.mean(null_db),
        'null_db_std': np.std(null_db),
        'silhouette_p_value': silhouette_p,
        'ch_p_value': ch_p,
        'db_p_value': db_p,
        'null_silhouette_distribution': null_silhouette,
        'null_ch_distribution': null_ch,
        'null_db_distribution': null_db
    }

    logger.info(f"Uniform random baseline complete. Silhouette p={silhouette_p:.4f}, CH p={ch_p:.4f}, DB p={db_p:.4f}")

    return results


def export_null_baseline_results(
    results: Dict,
    baseline_type: str,
    output_dir: str = 'outputs/metrics'
) -> None:
    """Export null baseline results to JSON.

    Args:
        results: Dictionary from permutation_null_baseline or uniform_random_baseline
        baseline_type: String identifier for the baseline type
        output_dir: Directory to save outputs
    """
    from pathlib import Path
    import json

    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    # Remove distribution arrays from summary (save separately)
    summary = {k: v for k, v in results.items() if not k.endswith('_distribution')}

    with open(output_path / f'null_baseline_{baseline_type}_summary.json', 'w') as f:
        json.dump(summary, f, indent=2)

    # Save distributions as CSV
    for key in results:
        if key.endswith('_distribution'):
            dist = results[key]
            df = pd.DataFrame({baseline_type: dist})
            df.to_csv(output_path / f'null_baseline_{baseline_type}_{key}.csv', index=False)

    logger.info(f"Null baseline results saved to {output_path}")


if __name__ == '__main__':
    # Test with synthetic data
    np.random.seed(42)
    n_samples = 200
    n_features = 10

    # Generate synthetic data with some cluster structure
    X = np.random.randn(n_samples, n_features)
    X[:100] += 1.0  # Two clusters

    # Test permutation baseline
    perm_results = permutation_null_baseline(X, n_clusters=2, n_permutations=50)
    export_null_baseline_results(perm_results, 'permutation')

    # Test uniform random baseline
    uniform_results = uniform_random_baseline(X, n_clusters=2, n_simulations=50)
    export_null_baseline_results(uniform_results, 'uniform_random')

    print("\nPermutation Baseline Results:")
    print(f"  Silhouette p-value: {perm_results['silhouette_p_value']:.4f}")
    print(f"  CH p-value: {perm_results['ch_p_value']:.4f}")
    print(f"  DB p-value: {perm_results['db_p_value']:.4f}")

    print("\nUniform Random Baseline Results:")
    print(f"  Silhouette p-value: {uniform_results['silhouette_p_value']:.4f}")
    print(f"  CH p-value: {uniform_results['ch_p_value']:.4f}")
    print(f"  DB p-value: {uniform_results['db_p_value']:.4f}")
