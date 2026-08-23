"""Clustering tests.

Two things are under test here. First, that the pipeline returns an object whose
parts agree with each other and with what was written to disk. Second, and more
important, that select_optimal_k follows the rule stated in the clustering module
docstring rather than favouring any particular K.
"""
import joblib
import numpy as np
import pytest

from clustering import (
    ClusteringResults,
    curve_knee,
    measure_cluster_stability,
    run_clustering_pipeline,
    select_optimal_k,
)
from feature_engineering import select_features
from pca_analysis import run_pca_pipeline


def _metrics(k_values, silhouette, ch, db, inertia=None):
    """Build the four by-K dictionaries select_optimal_k expects."""
    inertia = inertia or [100.0 - 10 * i for i in range(len(k_values))]
    return (
        list(k_values),
        dict(zip(k_values, inertia)),
        dict(zip(k_values, silhouette)),
        dict(zip(k_values, ch)),
        dict(zip(k_values, db)),
    )


def test_clustering_pipeline_is_internally_consistent(small_features, tmp_path):
    selected = select_features(small_features, feature_group='behavioral')
    X_pca, _, _, _ = run_pca_pipeline(
        selected,
        output_dir=str(tmp_path / 'figures'),
        model_dir=str(tmp_path / 'models'),
    )

    results = run_clustering_pipeline(
        X_pca,
        k_range=(2, 6),
        test_stability=True,
        stability_runs=4,
        output_dir=str(tmp_path / 'figures'),
        model_dir=str(tmp_path / 'models'),
        metrics_dir=str(tmp_path / 'metrics'),
    )

    assert isinstance(results, ClusteringResults)
    assert results.k_values == [2, 3, 4, 5]
    for by_k in (results.inertia_by_k, results.silhouette_by_k,
                 results.ch_by_k, results.db_by_k, results.stability_by_k):
        assert sorted(by_k) == results.k_values

    assert results.optimal_k in results.k_values
    assert len(results.labels) == X_pca.shape[0]
    assert len(np.unique(results.labels)) == results.optimal_k
    assert results.model.n_clusters == results.optimal_k
    np.testing.assert_array_equal(results.model.predict(X_pca), results.labels)

    # The stability property points at the selected K, not at an arbitrary one.
    assert results.stability['n_clusters'] == results.optimal_k

    frame = results.metrics_frame()
    assert len(frame) == len(results.k_values)
    assert set(frame['K']) == set(results.k_values)

    kmeans_reloaded = joblib.load(tmp_path / 'models' / 'kmeans_model.pkl')
    labels_reloaded = np.load(tmp_path / 'models' / 'cluster_labels.npy')
    assert kmeans_reloaded.n_clusters == results.optimal_k
    np.testing.assert_array_equal(results.labels, labels_reloaded)

    assert (tmp_path / 'metrics' / 'clustering_metrics.csv').exists()


def test_stability_measured_at_every_k(small_features, tmp_path):
    """Stability must be known for all candidates, since it filters candidates.

    Measuring it only after selection, as an earlier version did, means the
    filter can never reject anything.
    """
    selected = select_features(small_features, feature_group='behavioral')
    X_pca, _, _, _ = run_pca_pipeline(
        selected,
        output_dir=str(tmp_path / 'figures'),
        model_dir=str(tmp_path / 'models'),
    )
    results = run_clustering_pipeline(
        X_pca,
        k_range=(2, 5),
        test_stability=True,
        stability_runs=4,
        output_dir=str(tmp_path / 'figures'),
        model_dir=str(tmp_path / 'models'),
        metrics_dir=str(tmp_path / 'metrics'),
    )

    for k in results.k_values:
        record = results.stability_by_k[k]
        assert record['n_clusters'] == k
        assert 0.0 <= record['mean_ari'] <= 1.0
        # The smallest cluster cannot hold more than an equal share.
        assert 0.0 < record['min_cluster_share'] <= 1.0 / k + 1e-9

    assert (tmp_path / 'metrics' / 'stability_results.csv').exists()
    assert (tmp_path / 'metrics' / 'k_selection_trace.json').exists()


def test_k2_wins_when_it_dominates_every_metric():
    """No forced 3 to 6 window: if K=2 is best on all three indices, take it."""
    k_values, inertia, sil, ch, db = _metrics(
        [2, 3, 4, 5, 6],
        silhouette=[0.5, 0.3, 0.2, 0.15, 0.1],
        ch=[200, 100, 80, 60, 40],
        db=[0.5, 1.0, 1.2, 1.5, 1.8],
    )
    optimal_k, trace = select_optimal_k(k_values, inertia, sil, ch, db)
    assert optimal_k == 2
    assert trace['selected_k'] == 2
    assert trace['best_k_by_score'] == 2


def test_larger_k_wins_when_it_dominates_every_metric():
    """The mirror image of the previous test, so the rule is not biased low."""
    k_values, inertia, sil, ch, db = _metrics(
        [2, 3, 4, 5, 6],
        silhouette=[0.10, 0.15, 0.20, 0.30, 0.55],
        ch=[40, 60, 80, 100, 220],
        db=[1.8, 1.5, 1.2, 1.0, 0.4],
    )
    optimal_k, _ = select_optimal_k(k_values, inertia, sil, ch, db)
    assert optimal_k == 6


def test_tiny_clusters_disqualify_a_k():
    """K=5 wins on quality but leaves a cluster holding 1 percent of consumers."""
    k_values, inertia, sil, ch, db = _metrics(
        [2, 3, 4, 5],
        silhouette=[0.20, 0.30, 0.25, 0.60],
        ch=[50, 80, 70, 200],
        db=[1.6, 1.2, 1.3, 0.4],
    )
    stability = {
        2: {'mean_ari': 0.95, 'min_cluster_share': 0.40},
        3: {'mean_ari': 0.95, 'min_cluster_share': 0.25},
        4: {'mean_ari': 0.95, 'min_cluster_share': 0.15},
        5: {'mean_ari': 0.95, 'min_cluster_share': 0.01},
    }
    optimal_k, trace = select_optimal_k(k_values, inertia, sil, ch, db, stability)
    assert 5 not in trace['after_balance_filter']
    assert optimal_k == 3


def test_unstable_k_disqualified():
    """K=4 wins on quality but the partition moves between restarts."""
    k_values, inertia, sil, ch, db = _metrics(
        [2, 3, 4],
        silhouette=[0.20, 0.30, 0.70],
        ch=[50, 80, 300],
        db=[1.6, 1.2, 0.3],
    )
    stability = {
        2: {'mean_ari': 0.90, 'min_cluster_share': 0.40},
        3: {'mean_ari': 0.88, 'min_cluster_share': 0.25},
        4: {'mean_ari': 0.20, 'min_cluster_share': 0.20},
    }
    optimal_k, trace = select_optimal_k(k_values, inertia, sil, ch, db, stability)
    assert 4 not in trace['after_stability_filter']
    assert optimal_k == 3


def test_parsimony_breaks_a_near_tie_toward_the_smaller_k():
    """A K within the tolerance of the best score wins if it is simpler."""
    k_values, inertia, sil, ch, db = _metrics(
        [2, 3, 4],
        silhouette=[0.400, 0.401, 0.100],
        ch=[199.0, 200.0, 50.0],
        db=[0.501, 0.500, 1.500],
    )
    optimal_k, trace = select_optimal_k(k_values, inertia, sil, ch, db, tolerance=0.05)
    assert trace['best_k_by_score'] == 3
    assert optimal_k == 2
    assert trace['within_tolerance'] == [2, 3]

    # With no tolerance the raw winner stands, which shows the tolerance is what
    # produced the answer above rather than some hidden preference for K=2.
    strict_k, _ = select_optimal_k(k_values, inertia, sil, ch, db, tolerance=0.0)
    assert strict_k == 3


def test_filters_relax_rather_than_crash_when_nothing_qualifies():
    """Every K unstable: report the weakness, still return a usable K."""
    k_values, inertia, sil, ch, db = _metrics(
        [2, 3, 4],
        silhouette=[0.30, 0.20, 0.10],
        ch=[100, 80, 60],
        db=[1.0, 1.2, 1.4],
    )
    stability = {k: {'mean_ari': 0.10, 'min_cluster_share': 0.001} for k in k_values}
    optimal_k, trace = select_optimal_k(k_values, inertia, sil, ch, db, stability)
    assert optimal_k in k_values
    assert 'min_cluster_share' in trace['relaxed_filters']
    assert 'min_stability_ari' in trace['relaxed_filters']


def test_selection_is_deterministic():
    k_values, inertia, sil, ch, db = _metrics(
        [2, 3, 4, 5],
        silhouette=[0.25, 0.31, 0.29, 0.30],
        ch=[63, 82, 80, 73],
        db=[1.66, 1.22, 1.28, 1.31],
    )
    first, _ = select_optimal_k(k_values, inertia, sil, ch, db)
    for _ in range(5):
        again, _ = select_optimal_k(k_values, inertia, sil, ch, db)
        assert again == first


def test_curve_knee_finds_a_sharp_elbow():
    x = [2, 3, 4, 5, 6, 7]
    y = [100.0, 40.0, 20.0, 18.0, 16.5, 15.0]
    assert curve_knee(x, y) == 4
    assert curve_knee([2], [1.0]) is None


def test_stability_is_high_on_well_separated_blobs():
    rng = np.random.default_rng(0)
    blobs = np.vstack([
        rng.normal(loc, 0.15, size=(40, 2))
        for loc in ([0, 0], [10, 0], [0, 10])
    ])
    record = measure_cluster_stability(blobs, n_clusters=3, n_runs=5, random_state=42)
    assert record['mean_ari'] > 0.99
    assert record['mean_agreement'] > 0.99
    assert record['min_cluster_share'] == pytest.approx(1 / 3, abs=0.02)
