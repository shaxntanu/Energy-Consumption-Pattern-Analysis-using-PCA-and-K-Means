"""
Alternative Clustering Module

Implements alternative clustering methods for comparison with K-means.
This addresses reviewer requirement M5 for comparing against at least one
scientifically meaningful alternative clustering approach.
"""

import logging
from typing import Dict, List, Optional, Tuple

import numpy as np
import pandas as pd
from sklearn.cluster import AgglomerativeClustering, KMeans
from sklearn.mixture import GaussianMixture
from sklearn.metrics import (
    adjusted_rand_score,
    calinski_harabasz_score,
    davies_bouldin_score,
    silhouette_score,
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def run_gaussian_mixture_clustering(
    X: np.ndarray,
    n_clusters: int,
    random_state: int = 42,
    covariance_type: str = 'full',
    n_init: int = 10
) -> Dict:
    """Run Gaussian Mixture Model clustering.

    GMM is a probabilistic clustering method that can model clusters with
    different shapes and sizes, unlike K-means which assumes spherical
    clusters of equal size.

    Args:
        X: Feature matrix (n_samples, n_features)
        n_clusters: Number of clusters
        random_state: Random seed
        covariance_type: Type of covariance matrix ('full', 'tied', 'diag', 'spherical')
        n_init: Number of initializations

    Returns:
        Dictionary with clustering results and metrics
    """
    logger.info(f"Running GMM with {n_clusters} clusters, covariance_type={covariance_type}")

    gmm = GaussianMixture(
        n_components=n_clusters,
        covariance_type=covariance_type,
        n_init=n_init,
        random_state=random_state
    )

    labels = gmm.fit_predict(X)

    # Compute metrics
    try:
        silhouette = silhouette_score(X, labels)
    except ValueError:
        silhouette = np.nan
        logger.warning("Could not compute silhouette score (likely single cluster)")

    try:
        ch = calinski_harabasz_score(X, labels)
    except ValueError:
        ch = np.nan
        logger.warning("Could not compute Calinski-Harabasz score")

    try:
        db = davies_bouldin_score(X, labels)
    except ValueError:
        db = np.nan
        logger.warning("Could not compute Davies-Bouldin score")

    # Cluster sizes
    unique, counts = np.unique(labels, return_counts=True)
    cluster_sizes = dict(zip(unique, counts))

    results = {
        'method': 'GaussianMixture',
        'covariance_type': covariance_type,
        'n_clusters': n_clusters,
        'labels': labels,
        'silhouette': silhouette,
        'calinski_harabasz': ch,
        'davies_bouldin': db,
        'cluster_sizes': cluster_sizes,
        'bic': gmm.bic(X),
        'aic': gmm.aic(X),
        'converged': gmm.converged_,
        'n_iter': gmm.n_iter_
    }

    logger.info(f"GMM complete: silhouette={silhouette:.4f}, CH={ch:.4f}, DB={db:.4f}, BIC={results['bic']:.2f}")

    return results


def run_hierarchical_clustering(
    X: np.ndarray,
    n_clusters: int,
    linkage: str = 'ward',
    metric: str = 'euclidean'
) -> Dict:
    """Run hierarchical agglomerative clustering.

    Hierarchical clustering builds a tree of clusters and can reveal
    nested structure that K-means cannot capture.

    Args:
        X: Feature matrix (n_samples, n_features)
        n_clusters: Number of clusters
        linkage: Linkage criterion ('ward', 'complete', 'average', 'single')
        metric: Distance metric (for non-ward linkage)

    Returns:
        Dictionary with clustering results and metrics
    """
    logger.info(f"Running hierarchical clustering with {n_clusters} clusters, linkage={linkage}")

    hierarchical = AgglomerativeClustering(
        n_clusters=n_clusters,
        linkage=linkage,
        metric=metric if linkage != 'ward' else 'euclidean'
    )

    labels = hierarchical.fit_predict(X)

    # Compute metrics
    try:
        silhouette = silhouette_score(X, labels)
    except ValueError:
        silhouette = np.nan
        logger.warning("Could not compute silhouette score")

    try:
        ch = calinski_harabasz_score(X, labels)
    except ValueError:
        ch = np.nan
        logger.warning("Could not compute Calinski-Harabasz score")

    try:
        db = davies_bouldin_score(X, labels)
    except ValueError:
        db = np.nan
        logger.warning("Could not compute Davies-Bouldin score")

    # Cluster sizes
    unique, counts = np.unique(labels, return_counts=True)
    cluster_sizes = dict(zip(unique, counts))

    results = {
        'method': 'Hierarchical',
        'linkage': linkage,
        'metric': metric,
        'n_clusters': n_clusters,
        'labels': labels,
        'silhouette': silhouette,
        'calinski_harabasz': ch,
        'davies_bouldin': db,
        'cluster_sizes': cluster_sizes,
        'n_leaves': hierarchical.n_leaves_
    }

    logger.info(f"Hierarchical complete: silhouette={silhouette:.4f}, CH={ch:.4f}, DB={db:.4f}")

    return results


def compare_clustering_methods(
    X: np.ndarray,
    n_clusters: int,
    kmeans_labels: np.ndarray,
    random_state: int = 42
) -> pd.DataFrame:
    """Compare K-means with alternative clustering methods.

    Args:
        X: Feature matrix
        n_clusters: Number of clusters
        kmeans_labels: Labels from K-means (reference method)
        random_state: Random seed

    Returns:
        DataFrame with comparison metrics
    """
    logger.info("Comparing clustering methods")

    results = []

    # K-means (reference)
    try:
        kmeans_silhouette = silhouette_score(X, kmeans_labels)
        kmeans_ch = calinski_harabasz_score(X, kmeans_labels)
        kmeans_db = davies_bouldin_score(X, kmeans_labels)
    except ValueError:
        kmeans_silhouette = kmeans_ch = kmeans_db = np.nan

    results.append({
        'method': 'KMeans',
        'silhouette': kmeans_silhouette,
        'calinski_harabasz': kmeans_ch,
        'davies_bouldin': kmeans_db,
        'notes': 'Reference method'
    })

    # GMM with different covariance types
    for cov_type in ['full', 'tied', 'diag', 'spherical']:
        try:
            gmm_result = run_gaussian_mixture_clustering(
                X, n_clusters, random_state, covariance_type=cov_type
            )
            results.append({
                'method': f'GMM_{cov_type}',
                'silhouette': gmm_result['silhouette'],
                'calinski_harabasz': gmm_result['calinski_harabasz'],
                'davies_bouldin': gmm_result['davies_bouldin'],
                'bic': gmm_result['bic'],
                'aic': gmm_result['aic'],
                'notes': f'covariance_type={cov_type}'
            })

            # Compute ARI with K-means
            ari = adjusted_rand_score(kmeans_labels, gmm_result['labels'])
            results[-1]['ari_vs_kmeans'] = ari
        except Exception as e:
            logger.warning(f"GMM {cov_type} failed: {e}")

    # Hierarchical with different linkages
    for linkage in ['ward', 'complete', 'average']:
        try:
            hierarchical_result = run_hierarchical_clustering(
                X, n_clusters, linkage=linkage
            )
            results.append({
                'method': f'Hierarchical_{linkage}',
                'silhouette': hierarchical_result['silhouette'],
                'calinski_harabasz': hierarchical_result['calinski_harabasz'],
                'davies_bouldin': hierarchical_result['davies_bouldin'],
                'notes': f'linkage={linkage}'
            })

            # Compute ARI with K-means
            ari = adjusted_rand_score(kmeans_labels, hierarchical_result['labels'])
            results[-1]['ari_vs_kmeans'] = ari
        except Exception as e:
            logger.warning(f"Hierarchical {linkage} failed: {e}")

    df = pd.DataFrame(results)

    logger.info("Clustering method comparison complete")
    return df


def export_clustering_comparison(
    comparison_df: pd.DataFrame,
    output_dir: str = 'outputs/metrics'
) -> None:
    """Export clustering comparison results.

    Args:
        comparison_df: DataFrame from compare_clustering_methods
        output_dir: Directory to save outputs
    """
    from pathlib import Path

    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    comparison_df.to_csv(output_path / 'clustering_method_comparison.csv', index=False)

    logger.info(f"Clustering comparison saved to {output_path}")


if __name__ == '__main__':
    # Test with synthetic data
    np.random.seed(42)
    n_samples = 200
    n_features = 10
    n_clusters = 4

    # Generate synthetic data with cluster structure
    X = np.random.randn(n_samples, n_features)
    for i in range(n_clusters):
        X[i*50:(i+1)*50] += i * 1.5

    # K-means reference
    kmeans = KMeans(n_clusters=n_clusters, random_state=42, n_init=10)
    kmeans_labels = kmeans.fit_predict(X)

    # Compare methods
    comparison = compare_clustering_methods(X, n_clusters, kmeans_labels)
    export_clustering_comparison(comparison)

    print("\nClustering Method Comparison:")
    print(comparison[['method', 'silhouette', 'calinski_harabasz', 'davies_bouldin', 'ari_vs_kmeans']])
