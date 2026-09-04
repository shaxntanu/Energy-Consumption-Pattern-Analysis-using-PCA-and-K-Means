"""Optional bridge between the Python pipeline and the C++ performance engine.

The engine is a pybind11 module named `energy_cpp` (built from cpp_engine/).
Everything in this module is defensive: if the module is absent, or fails to
import for any reason (missing binary, wrong ABI, DLL not found), the bridge
reports `AVAILABLE = False` with a reason and every function that would have
used C++ simply is not offered. The Python/scikit-learn pipeline is the
scientific reference and never depends on this module.

Modes understood across this project:
    "python"  -> always the scikit-learn reference path
    "cpp"     -> the C++ engine (raises EngineUnavailable if not built)
    "auto"    -> C++ when available, otherwise the Python reference
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Optional, Sequence, Tuple

import numpy as np

logger = logging.getLogger(__name__)

try:  # The one place the optional extension is imported.
    import energy_cpp as _energy_cpp  # type: ignore

    AVAILABLE = True
    REASON: Optional[str] = None
    COMPILE_INFO: dict = dict(_energy_cpp.compile_info())
    logger.info(
        "energy_cpp module available (%s, OpenMP=%s, C++%s)",
        COMPILE_INFO.get("compiler", "unknown"),
        COMPILE_INFO.get("openmp", False),
        COMPILE_INFO.get("cxx_standard", "?"),
    )
except Exception as exc:  # noqa: BLE001 - any import failure means "optional"
    AVAILABLE = False
    REASON = f"{type(exc).__name__}: {exc}"
    COMPILE_INFO = {}
    logger.warning("energy_cpp module not available: %s", REASON)


class EngineUnavailable(RuntimeError):
    """Raised when a caller explicitly asks for the C++ engine and it is not
    importable. The Python reference path never raises this."""


def module_status() -> dict:
    """A dict for UIs and the benchmark report: is the engine importable, and
    what do we know about how it was compiled?"""
    return {
        "available": AVAILABLE,
        "reason": REASON,
        "compile_info": COMPILE_INFO,
        "build_command": (
            "py -m pip install ./cpp_engine"
            if not AVAILABLE
            else None
        ),
    }


def resolve_engine(engine: str) -> str:
    """Normalize an engine selector to 'python' or 'cpp'.

    "auto" prefers the C++ engine but falls back to Python. Explicit "cpp"
    raises EngineUnavailable when the module is not importable.
    """
    if engine in ("python", "ref", "reference"):
        return "python"
    if engine in ("cpp", "c++", "cxx"):
        if not AVAILABLE:
            raise EngineUnavailable(REASON or "energy_cpp is not importable")
        return "cpp"
    if engine in ("auto", "best", ""):
        return "cpp" if AVAILABLE else "python"
    raise ValueError(f"unknown engine selector: {engine!r}")


# ---------------------------------------------------------------------------
# PCA
# ---------------------------------------------------------------------------

def pca_fit_numpy(
    X: np.ndarray,
    variance_threshold: float = 0.95,
    max_components: int = 0,
) -> dict:
    """Fit PCA with the C++ engine on a numpy matrix.

    Returns a dict with numpy arrays: n_components, mean, components (k x d),
    eigen_values, explained_variance_ratio, cumulative_variance, scores (n x k),
    jacobi_sweeps. Component signs follow sklearn's svd_flip convention, so
    loadings and scores line up with the reference up to float error.
    """
    if not AVAILABLE:
        raise EngineUnavailable(REASON or "energy_cpp is not importable")
    X = np.asarray(X, dtype=np.float64)
    if X.ndim != 2:
        raise ValueError("pca_fit_numpy expects a 2-D matrix")
    n_rows, n_cols = X.shape
    flat = np.ascontiguousarray(X).ravel()
    out = _energy_cpp.pca_fit(
        flat, n_rows, n_cols, float(variance_threshold), int(max_components)
    )
    k = int(out["n_components"])
    return {
        "n_components": k,
        "mean": np.asarray(out["mean"], dtype=np.float64),
        "components": np.asarray(out["components"], dtype=np.float64).reshape(k, n_cols),
        "eigen_values": np.asarray(out["eigen_values"], dtype=np.float64),
        "explained_variance_ratio": np.asarray(
            out["explained_variance_ratio"], dtype=np.float64
        ),
        "cumulative_variance": np.asarray(out["cumulative_variance"], dtype=np.float64),
        "scores": np.asarray(out["scores"], dtype=np.float64).reshape(n_rows, k),
        "jacobi_sweeps": int(out["jacobi_sweeps"]),
    }


# ---------------------------------------------------------------------------
# K-Means
# ---------------------------------------------------------------------------

def kmeans_fit_numpy(
    X: np.ndarray,
    k: int,
    max_iter: int = 300,
    tol: float = 1e-4,
    n_init: int = 10,
    init: str = "kmeanspp",
    seed: int = 42,
) -> dict:
    """Fit K-Means with the C++ engine on a numpy matrix.

    Returns a dict: labels (n, int), centroids (k x d), inertia, n_iterations,
    best_init, converged. Parameter names mirror sklearn's KMeans so the two
    can be compared one-for-one.
    """
    if not AVAILABLE:
        raise EngineUnavailable(REASON or "energy_cpp is not importable")
    X = np.asarray(X, dtype=np.float64)
    if X.ndim != 2:
        raise ValueError("kmeans_fit_numpy expects a 2-D matrix")
    n_rows, n_cols = X.shape
    flat = np.ascontiguousarray(X).ravel()
    out = _energy_cpp.kmeans_fit(
        flat, n_rows, n_cols, int(k), int(max_iter), float(tol),
        int(n_init), str(init), int(seed),
    )
    return {
        "labels": np.asarray(out["labels"], dtype=np.int64),
        "centroids": np.asarray(out["centroids"], dtype=np.float64).reshape(k, n_cols),
        "inertia": float(out["inertia"]),
        "n_iterations": int(out["n_iterations"]),
        "best_init": int(out["best_init"]),
        "converged": bool(out["converged"]),
        "k": int(out["k"]),
        "seed": int(out["seed"]),
        "n_init": int(out["n_init"]),
    }


# ---------------------------------------------------------------------------
# Drop-in sklearn-compatible wrappers (used by the end-to-end comparison and
# the benchmark; identical in shape to the sklearn classes they replace).
# ---------------------------------------------------------------------------

class CppKMeans:
    """A minimal KMeans-shaped object backed by the C++ engine.

    Implements fit/fit_predict/predict and the attributes the clustering module
    reads (labels_, inertia_, cluster_centers_, n_iter_), so the pipeline's
    K-sweep and stability machinery can run entirely on C++ without edits.
    """

    def __init__(
        self,
        n_clusters: int = 8,
        *,
        random_state: int = 42,
        n_init: int = 10,
        init: str = "k-means++",
        max_iter: int = 300,
        tol: float = 1e-4,
    ):
        if not AVAILABLE:
            raise EngineUnavailable(REASON or "energy_cpp is not importable")
        self.n_clusters = int(n_clusters)
        self.random_state = int(random_state)
        self.n_init = int(n_init)
        self.init = init
        self.max_iter = int(max_iter)
        self.tol = float(tol)
        self.labels_: Optional[np.ndarray] = None
        self.inertia_: float = 0.0
        self.cluster_centers_: Optional[np.ndarray] = None
        self.n_iter_: int = 0
        self.n_features_in_: int = 0

    def _fit(self, X: np.ndarray):
        X = np.asarray(X, dtype=np.float64)
        if X.ndim != 2:
            raise ValueError("CppKMeans expects a 2-D matrix")
        self.n_features_in_ = X.shape[1]
        init = "kmeanspp" if self.init in ("k-means++", "kmeans++") else "random"
        res = kmeans_fit_numpy(
            X, self.n_clusters,
            max_iter=self.max_iter, tol=self.tol, n_init=self.n_init,
            init=init, seed=self.random_state,
        )
        self.labels_ = res["labels"]
        self.inertia_ = res["inertia"]
        self.cluster_centers_ = res["centroids"]
        self.n_iter_ = res["n_iterations"]
        return self

    def fit(self, X, y=None):  # noqa: D102
        return self._fit(X)

    def fit_predict(self, X, y=None):  # noqa: D102
        return self._fit(X).labels_

    def predict(self, X):
        """Assign rows to the nearest learned centroid."""
        if self.cluster_centers_ is None:
            raise RuntimeError("CppKMeans.predict called before fit")
        X = np.asarray(X, dtype=np.float64)
        centers = self.cluster_centers_
        diff = X[:, None, :] - centers[None, :, :]
        dists = np.einsum("ijk,ijk->ij", diff, diff)
        return np.argmin(dists, axis=1).astype(np.int64)


def cpp_pca_object(
    X: np.ndarray, variance_threshold: float = 0.95, max_components: int = 0
) -> Tuple[object, np.ndarray, int, dict]:
    """Return a PCA-shaped object plus scores from the C++ engine.

    The object exposes the attributes the pipeline reads off a fitted sklearn
    PCA (components_, explained_variance_, explained_variance_ratio_,
    n_components_, mean_) and a working transform(), so run_pca_pipeline can
    consume C++ results unchanged. Component counts are chosen by the same
    three rules as the reference (variance_threshold / kaiser / scree_elbow).
    """
    if not AVAILABLE:
        raise EngineUnavailable(REASON or "energy_cpp is not importable")

    # The full spectrum is fitted once; the three selection rules are evaluated
    # on the same eigenvalues, exactly as pca_analysis.perform_pca does.
    out = pca_fit_numpy(X, variance_threshold=variance_threshold,
                        max_components=max_components)
    d = X.shape[1]
    k = out["n_components"]
    ratios = out["explained_variance_ratio"]
    eig = out["eigen_values"]

    cumulative = np.cumsum(ratios)
    by_threshold = int(np.argmax(cumulative >= variance_threshold) + 1)
    by_kaiser = int(max(1, np.sum(eig > 1.0)))
    n = len(ratios)
    if n >= 3:
        xs = np.arange(n, dtype=float)
        ys = ratios
        dx, dy = xs[-1] - xs[0], ys[-1] - ys[0]
        norm = np.hypot(dx, dy)
        dist = np.abs(dy * (xs - xs[0]) - dx * (ys - ys[0])) / norm
        by_elbow = int(np.argmax(dist) + 1)
    else:
        by_elbow = n
    criteria = {
        "variance_threshold": by_threshold,
        "kaiser": by_kaiser,
        "scree_elbow": by_elbow,
    }

    class _CppPCA:
        def __init__(self, kk, comp, ev, evr, mean, scores, feats):
            self.n_components_ = kk
            self.components_ = comp          # (k, d)
            self.explained_variance_ = ev    # (k,)
            self.explained_variance_ratio_ = evr
            self.mean_ = mean
            self._scores = scores
            self.n_features_in_ = feats

        def transform(self, X2):
            X2 = np.asarray(X2, dtype=np.float64)
            return (X2 - self.mean_) @ self.components_.T

        def fit(self, X2, y=None):
            return self

        def fit_transform(self, X2, y=None):
            return self.transform(X2)

    pca_obj = _CppPCA(
        k, out["components"], eig[:k], ratios[:k], out["mean"],
        out["scores"], d,
    )
    return pca_obj, out["scores"], int(by_threshold), criteria


# ---------------------------------------------------------------------------
# End-to-end kernel swap (used by the benchmark's --e2e comparison).
# ---------------------------------------------------------------------------

def patch_pipeline_kernels(enable: bool = True) -> None:
    """Point the pipeline's PCA and K-Means kernels at the C++ engine.

    Monkeypatches pca_analysis.perform_pca and clustering.KMeans so a full
    EnergyAnalysis run uses C++ for the two compute kernels while every other
    step (data generation, feature engineering, selection rules, validation,
    reporting) stays the Python code. Call with enable=False to restore.
    Raises EngineUnavailable if the module is not importable.
    """
    if not AVAILABLE:
        raise EngineUnavailable(REASON or "energy_cpp is not importable")
    # Local imports keep the bridge import-safe (a bare `import cpp_bridge`
    # must never drag the whole pipeline in).
    import clustering  # noqa: PLC0415
    import longitudinal_analysis  # noqa: PLC0415
    import pca_analysis  # noqa: PLC0415
    import validation  # noqa: PLC0415

    if enable:
        if not getattr(pca_analysis, "_energy_cpp_patched", False):

            def _cpp_perform_pca(X, variance_threshold=0.95):
                from pca_analysis import component_count_criteria  # noqa: PLC0415

                pca_obj, X_pca, n_components, criteria = cpp_pca_object(
                    X, variance_threshold=variance_threshold
                )
                cumulative = np.cumsum(pca_obj.explained_variance_ratio_)[-1]
                logger.info(
                    "C++ PCA: retaining %d components, cumulative variance %.4f",
                    n_components, cumulative,
                )
                return pca_obj, X_pca, n_components, criteria

            pca_analysis.perform_pca = _cpp_perform_pca
            for mod in (clustering, longitudinal_analysis, validation):
                mod.KMeans = CppKMeans
            pca_analysis._energy_cpp_patched = True
            logger.info("Pipeline kernels patched to use the C++ engine")
    else:
        # Restore by reloading the patched modules from source (the pipeline's
        # internal state is stateless between runs).
        import importlib  # noqa: PLC0415

        importlib.reload(pca_analysis)
        importlib.reload(clustering)
        importlib.reload(longitudinal_analysis)
        importlib.reload(validation)
        logger.info("Pipeline kernels restored to scikit-learn")
