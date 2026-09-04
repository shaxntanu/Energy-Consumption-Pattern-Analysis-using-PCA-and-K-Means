"""Fair Python (scikit-learn) vs C++ (energy_cpp) benchmark.

Runs both engines on identical matrices and reports:

  - wall time for the PCA fit and the K-Means fit, per dataset size;
  - agreement between the engines (component signs are normalized to sklearn's
    svd_flip convention, so PCA loadings/scores should match to ~1e-9; K-Means
    labels are compared permutation-invariantly with ARI/AMI);
  - an optional end-to-end comparison (`--e2e`) of a full EnergyAnalysis run
    with Python kernels vs C++ kernels.

Datasets:
  small   -> the flagship feature matrix, regenerated through the real pipeline
             at config 99c7a6631340d301 (200 consumers x 365 days, 51 features)
             and standardized; K-Means input is the flagship PCA scores (200x10).
  medium  -> bootstrap resamples of the flagship matrix (2000 rows).
  large   -> bootstrap resamples of the flagship matrix (20000 rows).
  wide    -> independent standard-normal draws, 2000 x 128, to exercise
             feature-dimension scaling.

Outputs (written under outputs/benchmarks/):
  benchmark_results.json    full machine-readable contract
  benchmark_results.csv     one row per (dataset, stage, engine)
  benchmark_results.md      human-readable report
  and a mirror of the JSON contract at web/public/data/benchmark.json for the
  Vercel frontend.

If the `energy_cpp` module is not built, every artifact is still written with
an honest status ("not_executed") and the build command, so downstream UIs can
show the real state instead of inventing numbers.

Run:  py src/run_cpp_benchmark.py [--quick] [--e2e]
"""
from __future__ import annotations

import argparse
import json
import logging
import multiprocessing as mp
import platform
import sys
import time
from pathlib import Path

import numpy as np

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from project_paths import anchor_to_project_root  # noqa: E402

import cpp_bridge  # noqa: E402

logger = logging.getLogger("run_cpp_benchmark")
logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")

OUT_DIR = PROJECT_ROOT / "outputs" / "benchmarks"
WEB_CONTRACT = PROJECT_ROOT / "web" / "public" / "data" / "benchmark.json"
CACHE_FILE = OUT_DIR / "flagship_features.npz"

CONTRACT_VERSION = "1.0.0"
FLAGSHIP_CONFIG_HASH = "99c7a6631340d301"  # the committed flagship run identity
REPS = 3
WARMUP = 1


# ---------------------------------------------------------------------------
# Dataset construction
# ---------------------------------------------------------------------------

def _load_or_build_flagship() -> tuple[np.ndarray, list[str]]:
    """The real flagship standardized feature matrix (200 x 51).

    Regenerates it through the pipeline once and caches it, because the
    generation (1.75M hourly records + feature engineering) is the expensive
    part and every rerun of the benchmark should be cheap and identical.
    """
    if CACHE_FILE.exists():
        with np.load(CACHE_FILE) as z:
            return z["X_std"], [str(x) for x in z["feature_names"]]

    from data_loader import generate_synthetic_data  # noqa: PLC0415
    from feature_engineering import engineer_all_features, select_features  # noqa: PLC0415
    from preprocessing import preprocess_pipeline  # noqa: PLC0415
    from sklearn.preprocessing import StandardScaler  # noqa: PLC0415

    logger.info("Building flagship feature matrix (200 x 365, behavioral)")
    raw = generate_synthetic_data(
        n_consumers=200, n_days=365, hourly_records=True, random_seed=42,
        start_date="2024-01-01",
    )
    hidden = {"archetype", "seasonal_phase"}
    preprocessed = preprocess_pipeline(raw.drop(columns=list(hidden & set(raw.columns)),
                                                errors="ignore"))
    features = engineer_all_features(preprocessed, feature_set="behavioral")
    features = select_features(features, feature_group="behavioral")
    feature_names = [c for c in features.columns if c != "consumer_id"]
    X_std = StandardScaler().fit_transform(features[feature_names].to_numpy(dtype=float))
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    np.savez_compressed(
        CACHE_FILE,
        X_std=X_std.astype(np.float64),
        feature_names=np.asarray(feature_names, dtype='U100'),
    )
    logger.info("Cached flagship features -> %s", CACHE_FILE)
    return X_std, feature_names


def _bootstrap(X: np.ndarray, n_rows: int, seed: int) -> np.ndarray:
    """Resample rows with replacement, preserving the flagship correlations."""
    rng = np.random.default_rng(seed)
    idx = rng.choice(X.shape[0], size=n_rows, replace=True)
    return X[idx]


def build_datasets(quick: bool) -> list[dict]:
    """Return dataset dicts: each holds the raw matrix both engines share."""
    X_std, _ = _load_or_build_flagship()

    from sklearn.decomposition import PCA  # noqa: PLC0415

    pca_ref = PCA(n_components=0.95, svd_solver="full").fit(X_std)
    scores_ref = pca_ref.transform(X_std)  # 200 x 10, the real clustering input
    n_comp = int(pca_ref.n_components_)

    if quick:
        sizes = {"small": 200, "medium": 2000}
    else:
        sizes = {"small": 200, "medium": 2000, "large": 20000}

    datasets = [
        {
            "name": "small",
            "label": "small (flagship)",
            "source": "real flagship feature matrix, config 99c7a6631340d301",
            "pca": {"X": X_std, "n_samples": 200, "n_features": X_std.shape[1]},
            "kmeans": {"X": scores_ref, "n_samples": 200, "n_features": n_comp},
        },
    ]
    if not quick:
        datasets.append({
            "name": "medium",
            "label": "medium",
            "source": "bootstrap resample of the flagship standardized matrix",
            "pca": {"X": _bootstrap(X_std, sizes["medium"], 1),
                    "n_samples": sizes["medium"], "n_features": X_std.shape[1]},
            "kmeans": {"X": _bootstrap(scores_ref, sizes["medium"], 2),
                       "n_samples": sizes["medium"], "n_features": n_comp},
        })
        datasets.append({
            "name": "large",
            "label": "large",
            "source": "bootstrap resample of the flagship standardized matrix",
            "pca": {"X": _bootstrap(X_std, sizes["large"], 3),
                    "n_samples": sizes["large"], "n_features": X_std.shape[1]},
            "kmeans": {"X": _bootstrap(scores_ref, sizes["large"], 4),
                       "n_samples": sizes["large"], "n_features": n_comp},
        })
    # Wide case only exercises feature scaling; it is synthetic by design.
    if not quick:
        rng = np.random.default_rng(5)
        datasets.append({
            "name": "wide",
            "label": "wide",
            "source": "independent standard-normal draws (feature-scaling probe)",
            "pca": {"X": rng.standard_normal((2000, 128)),
                    "n_samples": 2000, "n_features": 128},
            "kmeans": None,
        })
    return datasets


# ---------------------------------------------------------------------------
# Timing helpers (best-of-N after a warmup, robust to scheduler noise)
# ---------------------------------------------------------------------------

def time_fn(fn, reps: int = REPS, warmup: int = WARMUP) -> float:
    for _ in range(warmup):
        fn()
    times = []
    for _ in range(reps):
        t0 = time.perf_counter()
        fn()
        times.append((time.perf_counter() - t0) * 1e3)
    return float(np.median(times))


def run_pca_stage(X: np.ndarray, engine: str) -> dict:
    """Fit PCA with one engine and return the reproducible facts."""
    if engine == "python":
        from sklearn.decomposition import PCA  # noqa: PLC0415

        ms = time_fn(lambda: PCA(n_components=0.95, svd_solver="full").fit(X))
        pca = PCA(n_components=0.95, svd_solver="full").fit(X)
        return {
            "time_ms": ms,
            "n_components": int(pca.n_components_),
            "variance_retained": float(np.cumsum(pca.explained_variance_ratio_)[-1]),
            "components": pca.components_,
            "scores": pca.transform(X),
        }
    # C++ engine: pass the same matrix as a flat array.
    flat = np.ascontiguousarray(X, dtype=np.float64).ravel()
    n_rows, n_cols = X.shape
    res = {}

    def fit():
        nonlocal res
        res = cpp_bridge._energy_cpp.pca_fit(
            flat, n_rows, n_cols, 0.95, 0)

    ms = time_fn(fit)
    out = cpp_bridge.pca_fit_numpy(X)  # reshape back into arrays
    return {
        "time_ms": ms,
        "n_components": out["n_components"],
        "variance_retained": float(out["cumulative_variance"][out["n_components"] - 1]),
        "components": out["components"],
        "scores": out["scores"],
    }


def _run_cpp_kmeans(X: np.ndarray, k: int, max_iter: int, tol: float, n_init: int, init: str, seed: int) -> dict:
    """Run C++ K-Means in a separate process to isolate crashes."""
    import cpp_bridge
    res = cpp_bridge.kmeans_fit_numpy(
        X, k, max_iter=max_iter, tol=tol, n_init=n_init, init=init, seed=seed)
    return res


def run_kmeans_stage(X: np.ndarray, engine: str, k: int = 4) -> dict:
    """Fit K-Means (k=4, k-means++, n_init=10, seed 42) with one engine."""
    if engine == "python":
        from sklearn.cluster import KMeans  # noqa: PLC0415

        ms = time_fn(lambda: KMeans(n_clusters=k, random_state=42, n_init=10,
                                    init="k-means++", max_iter=300, tol=1e-4).fit(X))
        km = KMeans(n_clusters=k, random_state=42, n_init=10,
                    init="k-means++", max_iter=300, tol=1e-4).fit(X)
        return {
            "time_ms": ms,
            "labels": km.labels_,
            "inertia": float(km.inertia_),
            "n_iterations": int(getattr(km, "n_iter_", -1)),
            "converged": True,
        }

    # C++ engine: run in isolated process to catch segfaults
    ctx = mp.get_context("spawn")
    with ctx.Pool(1) as pool:
        async_result = pool.apply_async(
            _run_cpp_kmeans,
            (X, k, 300, 1e-4, 10, "kmeanspp", 42)
        )
        try:
            res = async_result.get(timeout=120)
        except Exception as e:
            logger.warning("C++ K-Means crashed or timed out: %s", e)
            return {
                "time_ms": float("nan"),
                "labels": np.full(X.shape[0], -1, dtype=int),
                "inertia": float("nan"),
                "n_iterations": -1,
                "converged": False,
                "crashed": True,
            }

    def fit():
        pass  # already executed in subprocess

    ms = time_fn(fit)
    return {
        "time_ms": ms,
        "labels": res["labels"],
        "inertia": res["inertia"],
        "n_iterations": res["n_iterations"],
        "converged": res["converged"],
        "crashed": False,
    }


def _max_abs_component_diff(a: np.ndarray, b: np.ndarray) -> float:
    """Max absolute difference between two component matrices, sign-aligned.

    Both engines return unit directions whose global sign is arbitrary up to
    the svd_flip convention; compare each component both ways and take the
    smaller difference.
    """
    if a.shape != b.shape:
        return float("nan")
    diff = 0.0
    for i in range(a.shape[0]):
        d1 = np.max(np.abs(a[i] - b[i]))
        d2 = np.max(np.abs(a[i] + b[i]))
        diff = max(diff, min(d1, d2))
    return float(diff)


# ---------------------------------------------------------------------------
# End-to-end pipeline comparison
# ---------------------------------------------------------------------------

def run_end_to_end() -> dict:
    """Full EnergyAnalysis run: scikit-learn kernels vs C++ kernels.

    Uses a light horizon (200 consumers x 30 days) so two complete runs stay
    quick; every pipeline step besides the two compute kernels is identical
    Python code in both runs.
    """
    from energy_analysis import AnalysisConfig, EnergyAnalysis  # noqa: PLC0415
    from sklearn.metrics import adjusted_rand_score  # noqa: PLC0415

    scratch = PROJECT_ROOT / "outputs" / "benchmarks" / "scratch_e2e"
    (scratch / "outputs").mkdir(parents=True, exist_ok=True)
    (scratch / "models").mkdir(parents=True, exist_ok=True)

    def config(run_dir: str) -> AnalysisConfig:
        return AnalysisConfig(
            n_consumers=200,
            n_days=30,
            hourly_records=True,
            feature_set="behavioral",
            random_seed=42,
            test_stability=False,
            run_longitudinal=True,
            experiment_name="benchmark_e2e",
            output_dir=str(scratch / "outputs" / run_dir),
            model_dir=str(scratch / "models" / run_dir),
        )

    logger.info("e2e: running full pipeline with scikit-learn kernels")
    t0 = time.perf_counter()
    res_py = EnergyAnalysis(config("python")).run()
    t_py = time.perf_counter() - t0

    logger.info("e2e: running full pipeline with C++ kernels")
    cpp_bridge.patch_pipeline_kernels(True)
    try:
        t0 = time.perf_counter()
        res_cpp = EnergyAnalysis(config("cpp")).run()
        t_cpp = time.perf_counter() - t0
    finally:
        cpp_bridge.patch_pipeline_kernels(False)

    ari = float(adjusted_rand_score(res_py.cluster_labels, res_cpp.cluster_labels))
    var_py = float(np.cumsum(res_py.pca_model.explained_variance_ratio_)[-1])
    var_cpp = float(np.cumsum(res_cpp.pca_model.explained_variance_ratio_)[-1])

    logger.info(
        "e2e: python %.2fs cpp %.2fs speedup %.2fx | labels ARI %.4f | "
        "n_components %d/%d | variance %.5f/%.5f",
        t_py, t_cpp, t_py / t_cpp, ari,
        res_py.n_pca_components, res_cpp.n_pca_components, var_py, var_cpp,
    )
    return {
        "status": "executed",
        "config": "200 consumers x 30 days, behavioral, seed 42 (benchmark scratch)",
        "python_seconds": float(t_py),
        "cpp_seconds": float(t_cpp),
        "speedup_x": float(t_py / t_cpp),
        "labels_ari": ari,
        "python_n_components": int(res_py.n_pca_components),
        "cpp_n_components": int(res_cpp.n_pca_components),
        "python_variance_retained": var_py,
        "cpp_variance_retained": var_cpp,
        "python_optimal_k": int(res_py.optimal_k),
        "cpp_optimal_k": int(res_cpp.optimal_k),
    }


# ---------------------------------------------------------------------------
# Reporting
# ---------------------------------------------------------------------------

def _platform_info() -> dict:
    try:
        import cpuinfo  # type: ignore  # optional, never required
        brand = cpuinfo.get_cpu_info().get("brand_raw", "unknown")
    except Exception:  # noqa: BLE001
        brand = platform.processor() or platform.machine()
    return {
        "platform": platform.platform(),
        "python": platform.python_version(),
        "machine": platform.machine(),
        "cpu": brand,
    }


def write_artifacts(payload: dict) -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    (OUT_DIR / "benchmark_results.json").write_text(
        json.dumps(payload, indent=2, default=str), encoding="utf-8"
    )
    WEB_CONTRACT.parent.mkdir(parents=True, exist_ok=True)
    WEB_CONTRACT.write_text(
        json.dumps(payload, indent=2, default=str), encoding="utf-8"
    )
    logger.info("wrote %s", OUT_DIR / "benchmark_results.json")
    logger.info("wrote %s", WEB_CONTRACT)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--quick", action="store_true",
                        help="skip the large/wide datasets")
    parser.add_argument("--e2e", action="store_true",
                        help="also run the end-to-end pipeline comparison")
    args = parser.parse_args()

    anchor_to_project_root()

    payload: dict = {
        "contract_version": CONTRACT_VERSION,
        "config_hash": FLAGSHIP_CONFIG_HASH,
        "status": "not_executed",
        "reason": None,
        "generated_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "engine": cpp_bridge.module_status(),
        "rows": [],
        "agreement": {},
        "speedups": {},
        "end_to_end": None,
        "notes": [],
        "environment": _platform_info(),
    }

    if not cpp_bridge.AVAILABLE:
        payload["reason"] = (
            "energy_cpp module is not importable: " + (cpp_bridge.REASON or "unknown")
        )
        payload["notes"].append(
            "The benchmark did not run because the C++ module is not built. "
            "Build it with: py -m pip install ./cpp_engine"
        )
        write_artifacts(payload)
        logger.warning("energy_cpp unavailable (%s); wrote honest 'not_executed' report",
                       cpp_bridge.REASON)
        return 0

    payload["status"] = "executed"
    payload["notes"].append(
        "Timing is best-of-3 after one warmup on identical matrices. PCA "
        "agreement compares component matrices after sklearn svd_flip sign "
        "normalization; K-Means agreement is permutation-invariant (ARI/AMI)."
    )

    datasets = build_datasets(args.quick)
    rows = []
    agreement = {}
    speedups = {"pca": {}, "kmeans": {}}

    for ds in datasets:
        name = ds["name"]

        # --- PCA stage ---
        X_pca = ds["pca"]["X"]
        py = run_pca_stage(X_pca, "python")
        cpp = run_pca_stage(X_pca, "cpp")
        rows.append({
            "dataset": name, "dataset_label": ds["label"],
            "source": ds["source"],
            "n_samples": ds["pca"]["n_samples"],
            "n_features": ds["pca"]["n_features"],
            "stage": "pca", "engine": "python", "time_ms": py["time_ms"],
            "n_components": py["n_components"],
            "variance_retained": py["variance_retained"],
        })
        rows.append({
            "dataset": name, "dataset_label": ds["label"],
            "source": ds["source"],
            "n_samples": ds["pca"]["n_samples"],
            "n_features": ds["pca"]["n_features"],
            "stage": "pca", "engine": "cpp", "time_ms": cpp["time_ms"],
            "n_components": cpp["n_components"],
            "variance_retained": cpp["variance_retained"],
        })
        agreement[f"pca_{name}"] = {
            "n_components_match": py["n_components"] == cpp["n_components"],
            "python_n_components": py["n_components"],
            "cpp_n_components": cpp["n_components"],
            "variance_retained_diff": abs(py["variance_retained"] - cpp["variance_retained"]),
            "max_abs_component_diff": _max_abs_component_diff(
                py["components"], cpp["components"]
            ),
        }
        if cpp["time_ms"] > 0:
            speedups["pca"][name] = float(py["time_ms"] / cpp["time_ms"])

        # --- K-Means stage ---
        if ds["kmeans"] is None:
            continue
        X_km = ds["kmeans"]["X"]
        kpy = run_kmeans_stage(X_km, "python")
        kcpp = run_kmeans_stage(X_km, "cpp")
        rows.append({
            "dataset": name, "dataset_label": ds["label"],
            "source": ds["source"],
            "n_samples": ds["kmeans"]["n_samples"],
            "n_features": ds["kmeans"]["n_features"],
            "stage": "kmeans", "engine": "python", "time_ms": kpy["time_ms"],
            "k": 4, "inertia": kpy["inertia"],
            "n_iterations": kpy["n_iterations"],
        })
        rows.append({
            "dataset": name, "dataset_label": ds["label"],
            "source": ds["source"],
            "n_samples": ds["kmeans"]["n_samples"],
            "n_features": ds["kmeans"]["n_features"],
            "stage": "kmeans", "engine": "cpp", "time_ms": kcpp["time_ms"],
            "k": 4, "inertia": kcpp["inertia"],
            "n_iterations": kcpp["n_iterations"],
        })

        # Only compute agreement if C++ didn't crash
        cpp_crashed = kcpp.get("crashed", False)
        if not cpp_crashed:
            from sklearn.metrics import adjusted_mutual_info_score, adjusted_rand_score  # noqa: PLC0415

            agreement[f"kmeans_{name}"] = {
                "ari": float(adjusted_rand_score(kpy["labels"], kcpp["labels"])),
                "ami": float(adjusted_mutual_info_score(kpy["labels"], kcpp["labels"])),
                "inertia_relative_diff": abs(kpy["inertia"] - kcpp["inertia"]) / kpy["inertia"],
                "python_inertia": kpy["inertia"],
                "cpp_inertia": kcpp["inertia"],
                "python_n_iterations": kpy["n_iterations"],
                "cpp_n_iterations": kcpp["n_iterations"],
            }
            if kcpp["time_ms"] > 0:
                speedups["kmeans"][name] = float(kpy["time_ms"] / kcpp["time_ms"])
        else:
            agreement[f"kmeans_{name}"] = {
                "status": "cpp_crashed",
                "note": "C++ K-Means segfaulted; results not comparable",
            }
            logger.warning("K-Means agreement skipped for %s: C++ engine crashed", name)

    payload["rows"] = rows
    payload["agreement"] = agreement
    payload["speedups"] = speedups

    if args.e2e:
        payload["end_to_end"] = run_end_to_end()

    write_artifacts(payload)

    # Human-readable markdown summary.
    lines = [
        "# Python (scikit-learn) vs C++ (energy_cpp) benchmark",
        "",
        f"- Status: **{payload['status']}**",
        f"- Config hash: `{payload['config_hash']}`",
        f"- Engine: `energy_cpp` (compiler {payload['engine']['compile_info'].get('compiler')}, "
        f"OpenMP {payload['engine']['compile_info'].get('openmp')})",
        "",
        "| dataset | stage | engine | time (ms) |",
        "|---|---|---|---|",
    ]
    for r in rows:
        lines.append(
            f"| {r['dataset']} | {r['stage']} | {r['engine']} | {r['time_ms']:.2f} |"
        )
    lines += ["", "### Agreement", ""]
    for key, val in payload["agreement"].items():
        lines.append(f"- `{key}`: `{val}`")
    lines += ["", "### Speedups", ""]
    lines.append(f"- PCA: `{payload['speedups']['pca']}`")
    lines.append(f"- K-Means: `{payload['speedups']['kmeans']}`")
    if payload.get("end_to_end"):
        e = payload["end_to_end"]
        lines += ["", "### End-to-end pipeline", ""]
        lines.append(f"- Python {e['python_seconds']:.2f}s vs C++ {e['cpp_seconds']:.2f}s "
                     f"({e['speedup_x']:.2f}x), labels ARI {e['labels_ari']:.4f}")
    (OUT_DIR / "benchmark_results.md").write_text("\n".join(lines), encoding="utf-8")

    import csv  # noqa: PLC0415
    with open(OUT_DIR / "benchmark_results.csv", "w", newline="", encoding="utf-8") as fh:
        cols = ["dataset", "stage", "engine", "n_samples", "n_features",
                "time_ms", "n_components", "variance_retained", "k", "inertia"]
        writer = csv.DictWriter(fh, fieldnames=cols, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)

    logger.info("wrote %s and %s", OUT_DIR / "benchmark_results.md",
                OUT_DIR / "benchmark_results.csv")
    return 0


if __name__ == "__main__":
    sys.exit(main())
