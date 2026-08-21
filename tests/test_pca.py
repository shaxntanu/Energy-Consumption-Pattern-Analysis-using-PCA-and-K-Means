"""PCA pipeline tests — feature order, saved artifacts, transform shape."""
from pathlib import Path

import joblib
import numpy as np
import pytest

from feature_engineering import select_features
from pca_analysis import run_pca_pipeline, standardize_features


def test_pca_excludes_consumer_id(small_features, tmp_path):
    selected = select_features(small_features, feature_group='behavioral')
    assert 'consumer_id' in selected.columns

    X_pca, pca, scaler, n_components = run_pca_pipeline(
        selected,
        variance_threshold=0.95,
        output_dir=str(tmp_path / 'figures'),
        model_dir=str(tmp_path / 'models'),
    )

    n_features = selected.drop(columns=['consumer_id']).shape[1]
    assert scaler.n_features_in_ == n_features
    assert pca.n_features_in_ == n_features
    assert X_pca.shape == (len(selected), n_components)
    assert n_components >= 1
    assert np.isclose(np.cumsum(pca.explained_variance_ratio_)[-1], 1.0) or \
           np.cumsum(pca.explained_variance_ratio_)[-1] >= 0.95


def test_pca_feature_order_and_reload(small_features, tmp_path):
    selected = select_features(small_features, feature_group='behavioral')
    model_dir = tmp_path / 'models'
    fig_dir = tmp_path / 'figures'

    X_pca, pca, scaler, n_components = run_pca_pipeline(
        selected, output_dir=str(fig_dir), model_dir=str(model_dir)
    )

    feature_names = (model_dir / 'feature_names.txt').read_text(encoding='utf-8').splitlines()
    assert feature_names == list(selected.drop(columns=['consumer_id']).columns)

    scaler2 = joblib.load(model_dir / 'scaler.pkl')
    pca2 = joblib.load(model_dir / 'pca_model.pkl')

    X = selected.drop(columns=['consumer_id']).select_dtypes(include=[np.number])
    X_scaled = scaler2.transform(X)
    X_reload = pca2.transform(X_scaled)
    np.testing.assert_allclose(X_pca, X_reload, rtol=1e-6)


def test_standardize_zero_mean_unit_var(small_features):
    X = small_features.drop(columns=['consumer_id']).select_dtypes(include=[np.number])
    scaled, scaler = standardize_features(X)
    means = scaled.mean(axis=0)
    stds = scaled.std(axis=0, ddof=0)
    np.testing.assert_allclose(means, 0, atol=1e-7)
    np.testing.assert_allclose(stds, 1, atol=1e-7)
