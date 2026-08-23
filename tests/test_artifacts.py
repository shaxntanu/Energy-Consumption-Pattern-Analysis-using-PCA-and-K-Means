"""Artifact reload and output-directory creation tests."""
import json
from pathlib import Path

import joblib
import numpy as np
import pytest

from energy_analysis import AnalysisConfig, EnergyAnalysis, ensure_output_dirs


def test_ensure_output_dirs_creates_missing(tmp_path):
    base = tmp_path / 'outputs_new'
    models = tmp_path / 'models_new'
    paths = ensure_output_dirs(str(base), str(models))
    for p in paths.values():
        assert p.exists() and p.is_dir()


def test_artifacts_reload_under_pinned_versions(tmp_path):
    out = tmp_path / 'outputs'
    models = tmp_path / 'models'
    config = AnalysisConfig(
        n_consumers=25,
        n_days=4,
        feature_set='behavioral',
        test_stability=False,
        output_dir=str(out),
        model_dir=str(models),
        experiment_name='artifact_reload_test',
        k_range=(2, 4),
    )
    results = EnergyAnalysis(config).run()

    scaler = joblib.load(models / 'scaler.pkl')
    pca = joblib.load(models / 'pca_model.pkl')
    kmeans = joblib.load(models / 'kmeans_model.pkl')
    labels = np.load(models / 'cluster_labels.npy')
    meta = json.loads((models / 'analysis_metadata.json').read_text(encoding='utf-8'))

    assert scaler is not None
    assert pca.n_components_ == results.n_pca_components
    assert kmeans.n_clusters == results.optimal_k
    np.testing.assert_array_equal(labels, results.cluster_labels)

    assert 'synthetic' in meta['dataset_source'].lower()
    assert meta['selected_k'] == results.optimal_k
    assert meta['pca_components'] == results.n_pca_components
    assert 'package_versions' in meta
    assert 'scikit-learn' in meta['package_versions']
    assert meta['feature_list'] == results.feature_names
    assert (models / 'feature_names.txt').exists()
    assert (out / 'metrics' / 'pca_results.csv').exists()
    assert (out / 'metrics' / 'clustering_metrics.csv').exists()
