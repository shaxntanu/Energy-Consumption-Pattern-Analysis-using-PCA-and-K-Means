"""
Dashboard / analysis-object consistency tests.

Pages must read from AnalysisResults, never recomputing a different PCA/K-Means
for display, and K→metric lookup must be by explicit key.
"""
import pytest

from energy_analysis import AnalysisConfig, EnergyAnalysis


@pytest.fixture(scope='module')
def analysis_results(tmp_path_factory):
    out = tmp_path_factory.mktemp('out')
    models = tmp_path_factory.mktemp('models')
    config = AnalysisConfig(
        n_consumers=30,
        n_days=5,
        feature_set='behavioral',
        test_stability=False,
        output_dir=str(out),
        model_dir=str(models),
        experiment_name='dashboard_consistency_test',
        k_range=(2, 5),
    )
    return EnergyAnalysis(config).run()


def test_labels_match_fitted_kmeans(analysis_results):
    r = analysis_results
    predicted = r.kmeans_model.predict(r.pca_transformed)
    import numpy as np
    np.testing.assert_array_equal(predicted, r.cluster_labels)
    assert r.kmeans_model.n_clusters == r.optimal_k
    assert len(r.cluster_labels) == r.pca_transformed.shape[0]


def test_k_to_silhouette_dictionary_lookup(analysis_results):
    r = analysis_results
    # Must work via key, not positional index assumption (optimal_k - 2)
    sil = r.silhouette_for_k(r.optimal_k)
    assert isinstance(sil, float)
    assert sil == r.silhouette_by_k[r.optimal_k]

    with pytest.raises(KeyError):
        r.silhouette_for_k(999)


def test_config_hash_changes_on_parameter_change():
    a = AnalysisConfig(n_consumers=50, n_days=7, feature_set='behavioral')
    b = AnalysisConfig(n_consumers=51, n_days=7, feature_set='behavioral')
    c = AnalysisConfig(n_consumers=50, n_days=7, feature_set='scale')
    assert a.config_hash() == AnalysisConfig(n_consumers=50, n_days=7, feature_set='behavioral').config_hash()
    assert a.config_hash() != b.config_hash()
    assert a.config_hash() != c.config_hash()


def test_pca_and_labels_come_from_same_object(analysis_results):
    r = analysis_results
    assert r.pca_transformed.shape[1] == r.n_pca_components
    assert r.pca_model.n_components_ == r.n_pca_components
    assert set(r.k_values) == set(r.silhouette_by_k.keys())
    assert r.optimal_k in r.silhouette_by_k
