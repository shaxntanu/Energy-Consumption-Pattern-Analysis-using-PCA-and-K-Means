"""Tests for the optional C++ bridge (src/cpp_bridge.py).

The `energy_cpp` module is strictly optional: every test here skips cleanly
when it is not built, so `py -m pytest` passes either way. When the module IS
available, the tests pin down the contract the pipeline and the benchmark rely
on (sklearn-shaped PCA/K-Means objects, sign-aligned components, and the
kernel patch round-trip).
"""
import numpy as np
import pytest

import cpp_bridge

requires_cpp = pytest.mark.skipif(
    not cpp_bridge.AVAILABLE,
    reason="energy_cpp module not built (py -m pip install ./cpp_engine)",
)


def test_module_status_shape():
    status = cpp_bridge.module_status()
    assert set(status) >= {"available", "reason", "compile_info", "build_command"}
    assert status["available"] is cpp_bridge.AVAILABLE


def test_resolve_engine_python_always_works():
    assert cpp_bridge.resolve_engine("python") == "python"
    assert cpp_bridge.resolve_engine("auto") in ("python", "cpp")


def test_resolve_engine_cpp_raises_when_unavailable():
    if not cpp_bridge.AVAILABLE:
        with pytest.raises(cpp_bridge.EngineUnavailable):
            cpp_bridge.resolve_engine("cpp")
    else:
        assert cpp_bridge.resolve_engine("cpp") == "cpp"


@pytest.fixture(scope="module")
def X():
    """A small well-conditioned matrix with real correlation structure."""
    rng = np.random.default_rng(42)
    base = rng.standard_normal((80, 12))
    # Introduce rank-deficient structure so PCA has a clear elbow.
    X = np.column_stack([base[:, :4], base[:, :4] * 2 + 0.1 * base[:, 4:8],
                         base[:, 4:8], 0.05 * rng.standard_normal((80, 4))])
    return X.astype(np.float64)


# ---------------------------------------------------------------------------
# PCA
# ---------------------------------------------------------------------------

@requires_cpp
def test_pca_matches_sklearn_sign_aligned(X):
    from sklearn.decomposition import PCA

    ref = PCA(n_components=0.95, svd_solver="full").fit(X)
    out = cpp_bridge.pca_fit_numpy(X, variance_threshold=0.95)

    assert out["n_components"] == ref.n_components_
    np.testing.assert_allclose(out["mean"], ref.mean_, rtol=0, atol=1e-9)

    # Compare component directions up to sign (both engines follow svd_flip,
    # but assert the invariant directly rather than trusting the convention).
    a, b = out["components"], ref.components_
    for i in range(a.shape[0]):
        d1 = np.max(np.abs(a[i] - b[i]))
        d2 = np.max(np.abs(a[i] + b[i]))
        assert min(d1, d2) < 1e-6

    np.testing.assert_allclose(
        out["explained_variance_ratio"],
        ref.explained_variance_ratio_,
        rtol=1e-6, atol=1e-9,
    )
    np.testing.assert_allclose(
        np.cumsum(out["explained_variance_ratio"])[out["n_components"] - 1],
        np.cumsum(ref.explained_variance_ratio_)[ref.n_components_ - 1],
        rtol=1e-6,
    )


@requires_cpp
def test_pca_object_is_sklearn_shaped(X):
    from sklearn.decomposition import PCA

    pca_obj, scores, n_components, criteria = cpp_bridge.cpp_pca_object(
        X, variance_threshold=0.95
    )
    assert set(criteria) >= {"variance_threshold", "kaiser", "scree_elbow"}
    assert scores.shape == (X.shape[0], n_components)
    assert n_components >= 1

    ref = PCA(n_components=n_components).fit(X)
    assert pca_obj.n_components_ == n_components
    assert pca_obj.n_features_in_ == X.shape[1]
    np.testing.assert_allclose(pca_obj.mean_, ref.mean_, rtol=0, atol=1e-9)
    np.testing.assert_allclose(pca_obj.transform(X), ref.transform(X),
                               rtol=1e-6, atol=1e-6)


# ---------------------------------------------------------------------------
# K-Means
# ---------------------------------------------------------------------------

@requires_cpp
def test_kmeans_matches_sklearn_labels(X):
    from sklearn.cluster import KMeans
    from sklearn.metrics import adjusted_rand_score

    ref = KMeans(n_clusters=4, random_state=42, n_init=10, init="k-means++",
                 max_iter=300, tol=1e-4).fit(X)
    out = cpp_bridge.kmeans_fit_numpy(X, k=4, max_iter=300, tol=1e-4,
                                      n_init=10, init="kmeanspp", seed=42)

    assert out["labels"].shape == (X.shape[0],)
    assert out["centroids"].shape == (4, X.shape[1])
    assert out["converged"] is True
    # Labels may be permuted; ARI is permutation-invariant.
    assert adjusted_rand_score(ref.labels_, out["labels"]) > 0.99
    # Inertia is permutation-invariant and should agree closely.
    assert abs(out["inertia"] - ref.inertia_) / ref.inertia_ < 1e-3


@requires_cpp
def test_cpp_kmeans_wrapper_sklearn_api(X):
    km = cpp_bridge.CppKMeans(n_clusters=3, random_state=42, n_init=5)
    labels = km.fit_predict(X)
    assert labels.shape == (X.shape[0],)
    assert km.labels_ is labels
    assert km.cluster_centers_.shape == (3, X.shape[1])
    assert km.inertia_ > 0
    assert km.n_iter_ >= 1
    pred = km.predict(X)
    assert pred.shape == labels.shape


@requires_cpp
def test_patch_pipeline_kernels_roundtrip(X):
    """Patching must be reversible: restore reloads the sklearn references."""
    import clustering
    import longitudinal_analysis
    import pca_analysis
    import validation

    sklearn_km = clustering.KMeans
    sklearn_pca_name = pca_analysis.perform_pca.__name__

    cpp_bridge.patch_pipeline_kernels(True)
    assert clustering.KMeans is cpp_bridge.CppKMeans
    assert longitudinal_analysis.KMeans is cpp_bridge.CppKMeans
    assert validation.KMeans is cpp_bridge.CppKMeans
    assert pca_analysis.perform_pca.__name__ != sklearn_pca_name

    cpp_bridge.patch_pipeline_kernels(False)
    # importlib.reload re-executes the module body, so the restored perform_pca
    # is a *new* function object (identity cannot be compared). Assert the real
    # contract instead: the source def is back (same name) and it is not the
    # C++ patcher; KMeans is sklearn's class again (sklearn is module-cached,
    # so that identity DOES hold).
    assert pca_analysis.perform_pca.__name__ == sklearn_pca_name
    assert clustering.KMeans is sklearn_km
