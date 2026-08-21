"""Clustering tests — K range, metrics, labels, saved model."""
from pathlib import Path

import joblib
import numpy as np

from feature_engineering import select_features
from pca_analysis import run_pca_pipeline
from clustering import run_clustering_pipeline, select_optimal_k


def test_clustering_k_range_metrics_and_labels(small_features, tmp_path):
    selected = select_features(small_features, feature_group='behavioral')
    X_pca, _, _, _ = run_pca_pipeline(
        selected,
        output_dir=str(tmp_path / 'figures'),
        model_dir=str(tmp_path / 'models'),
    )

    k_range = (2, 6)
    kmeans, labels, optimal_k, k_values, inertia, sil, ch, db, stability = run_clustering_pipeline(
        X_pca,
        k_range=k_range,
        test_stability=True,
        output_dir=str(tmp_path / 'figures'),
        model_dir=str(tmp_path / 'models'),
    )

    k_values = list(k_values)
    assert k_values == list(range(2, 6))
    assert len(inertia) == len(k_values)
    assert len(sil) == len(k_values)
    assert len(ch) == len(k_values)
    assert len(db) == len(k_values)
    assert optimal_k in k_values
    assert len(labels) == X_pca.shape[0]
    assert len(np.unique(labels)) == optimal_k
    assert kmeans.n_clusters == optimal_k

    # Saved artifacts reload
    kmeans2 = joblib.load(tmp_path / 'models' / 'kmeans_model.pkl')
    labels2 = np.load(tmp_path / 'models' / 'cluster_labels.npy')
    assert kmeans2.n_clusters == optimal_k
    np.testing.assert_array_equal(labels, labels2)

    metrics_path = tmp_path / 'metrics' / 'clustering_metrics.csv'
    assert metrics_path.exists()


def test_select_optimal_k_no_hardcoded_preference():
    """If K=2 dominates all metrics, it must be selected (no forced 3–6)."""
    k_values = [2, 3, 4, 5, 6]
    inertia = [100, 90, 80, 70, 60]
    silhouette = [0.5, 0.3, 0.2, 0.15, 0.1]
    ch = [200, 100, 80, 60, 40]
    db = [0.5, 1.0, 1.2, 1.5, 1.8]
    assert select_optimal_k(k_values, inertia, silhouette, ch, db) == 2
