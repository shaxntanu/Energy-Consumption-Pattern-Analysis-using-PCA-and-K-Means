"""Repeat the full-year synthetic experiment and compare feature baselines.

This runner keeps the synthetic labels out of preprocessing, scaling, PCA,
K-selection, and model fitting. It evaluates labels only after fitting. Each
independent generation seed includes five predeclared representations:

* normalized 24-hour shape, standardized, no PCA (the requested baseline),
* normalized shape with PCA,
* 51 behavioral features without PCA,
* 51 behavioral features with PCA at fixed K=4, and
* 51 behavioral features with PCA and the project's K-selection rule.

Confidence intervals are percentile bootstrap intervals over independent
synthetic data seeds, not over consumers or individual hourly rows.
"""
from __future__ import annotations

import argparse
import json
import logging
import platform
import sys
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import scipy
import sklearn
from sklearn.cluster import KMeans
from sklearn.metrics import (
    adjusted_rand_score,
    calinski_harabasz_score,
    davies_bouldin_score,
    normalized_mutual_info_score,
    silhouette_score,
)
from sklearn.preprocessing import StandardScaler

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from clustering import N_INIT, find_optimal_k, select_optimal_k  # noqa: E402
from data_loader import SeasonalConfig, generate_synthetic_data  # noqa: E402
from feature_engineering import engineer_all_features, select_features  # noqa: E402
from pca_analysis import perform_pca  # noqa: E402
from preprocessing import preprocess_pipeline  # noqa: E402

logger = logging.getLogger("synthetic_365_replication")

METHODS = {
    "shape_24_no_pca": "24 normalized hourly bins; no PCA; K=4",
    "shape_24_pca95": "24 normalized hourly bins; PCA to 95%; K=4",
    "behavioral_51_no_pca": "51 behavioral features; no PCA; K=4",
    "behavioral_51_pca95_k4": "51 behavioral features; PCA to 95%; K=4",
    "behavioral_51_pca95_selected_k": "51 behavioral features; PCA to 95%; K by predeclared rule",
}


def _scores(X: np.ndarray, labels: np.ndarray, truth: np.ndarray,
            *, method: str, data_seed: int, model_seed: int, k: int,
            n_pca: int | None = None,
            stability_ari: float | None = None) -> dict:
    sizes = np.bincount(labels, minlength=k)
    return {
        "data_seed": data_seed,
        "model_seed": model_seed,
        "method": method,
        "k": int(k),
        "pca_components": n_pca,
        "ari": float(adjusted_rand_score(truth, labels)),
        "nmi": float(normalized_mutual_info_score(truth, labels)),
        "silhouette": float(silhouette_score(X, labels)),
        "calinski_harabasz": float(calinski_harabasz_score(X, labels)),
        "davies_bouldin": float(davies_bouldin_score(X, labels)),
        "minimum_cluster_share": float(sizes.min() / len(labels)),
        "restart_mean_ari": stability_ari,
    }


def _fit_fixed_k(X: np.ndarray, truth: np.ndarray, *, data_seed: int,
                 model_seed: int,
                 method: str, k: int = 4, n_pca: int | None = None) -> dict:
    labels = KMeans(n_clusters=k, random_state=model_seed, n_init=N_INIT).fit_predict(X)
    return _scores(X, labels, truth, method=method,
                   data_seed=data_seed, model_seed=model_seed,
                   k=k, n_pca=n_pca)


def run_one(data_seed: int, model_seed: int, *, stability_runs: int) -> list[dict]:
    raw = generate_synthetic_data(
        n_consumers=200,
        n_days=365,
        hourly_records=True,
        random_seed=data_seed,
        start_date="2024-01-01",
        seasonal=SeasonalConfig(),
    )
    truth = raw.groupby("consumer_id", sort=True)["archetype"].first().to_numpy()
    hidden = [c for c in ("archetype", "seasonal_phase") if c in raw.columns]
    panel = preprocess_pipeline(raw.drop(columns=hidden, errors="ignore"))

    features = engineer_all_features(panel, feature_set="behavioral")
    features = features.sort_values("consumer_id").reset_index(drop=True)
    ids = features["consumer_id"].to_numpy()
    truth_by_id = raw.groupby("consumer_id")["archetype"].first()
    truth = truth_by_id.reindex(ids).to_numpy()

    shape = select_features(features, feature_group="shape")
    behavioral = select_features(features, feature_group="behavioral")
    X_shape_scaled = StandardScaler().fit_transform(shape.drop(columns="consumer_id"))
    X_behavioral_scaled = StandardScaler().fit_transform(
        behavioral.drop(columns="consumer_id")
    )
    _, X_shape_pca, n_shape_pca, _ = perform_pca(X_shape_scaled, 0.95)
    _, X_behavioral_pca, n_behavioral_pca, _ = perform_pca(X_behavioral_scaled, 0.95)

    rows = [
        _fit_fixed_k(X_shape_scaled, truth, data_seed=data_seed, model_seed=model_seed,
                     method="shape_24_no_pca"),
        _fit_fixed_k(X_shape_pca, truth, data_seed=data_seed, model_seed=model_seed,
                     method="shape_24_pca95", n_pca=n_shape_pca),
        _fit_fixed_k(X_behavioral_scaled, truth, data_seed=data_seed, model_seed=model_seed,
                     method="behavioral_51_no_pca"),
        _fit_fixed_k(X_behavioral_pca, truth, data_seed=data_seed, model_seed=model_seed,
                     method="behavioral_51_pca95_k4", n_pca=n_behavioral_pca),
    ]

    k_values, inertia, sil, ch, db, stability = find_optimal_k(
        X_behavioral_pca,
        k_range=(2, 11),
        random_state=model_seed,
        stability_runs=stability_runs,
    )
    selected_k, trace = select_optimal_k(
        k_values, inertia, sil, ch, db, stability_by_k=stability
    )
    labels = KMeans(
        n_clusters=selected_k, random_state=model_seed, n_init=N_INIT
    ).fit_predict(X_behavioral_pca)
    selected = _scores(
        X_behavioral_pca, labels, truth,
        method="behavioral_51_pca95_selected_k",
        data_seed=data_seed,
        model_seed=model_seed,
        k=selected_k,
        n_pca=n_behavioral_pca,
        stability_ari=stability[selected_k]["mean_ari"],
    )
    selected["eligible_k"] = trace["after_stability_filter"]
    selected["relaxed_filters"] = trace["relaxed_filters"]
    rows.append(selected)
    return rows


def bootstrap_mean_ci(values: np.ndarray, rng: np.random.Generator,
                      draws: int = 5000) -> tuple[float, float, float, float]:
    values = np.asarray(values, dtype=float)
    samples = rng.choice(values, size=(draws, len(values)), replace=True).mean(axis=1)
    return (
        float(values.mean()),
        float(values.std(ddof=1)),
        float(np.quantile(samples, 0.025)),
        float(np.quantile(samples, 0.975)),
    )


def summarize(rows: pd.DataFrame, bootstrap_seed: int) -> tuple[pd.DataFrame, dict]:
    rng = np.random.default_rng(bootstrap_seed)
    summary_rows = []
    paired_diffs = {}
    for method in METHODS:
        subset = rows[rows["method"] == method]
        row = {"method": method, "description": METHODS[method],
               "n_independent_runs": int(len(subset)),
               "selected_k_counts": subset["k"].value_counts().sort_index().to_dict()}
        for metric in ("ari", "nmi", "silhouette", "minimum_cluster_share", "restart_mean_ari"):
            vals = subset[metric].dropna().to_numpy(dtype=float)
            if len(vals):
                mean, sd, lo, hi = bootstrap_mean_ci(vals, rng)
                row.update({f"{metric}_mean": mean, f"{metric}_sd": sd,
                            f"{metric}_ci95_low": lo, f"{metric}_ci95_high": hi})
        summary_rows.append(row)

    pivot = rows.pivot(index="data_seed", columns="method", values="ari")
    baseline = "shape_24_no_pca"
    for method in METHODS:
        if method == baseline:
            continue
        diff = (pivot[method] - pivot[baseline]).dropna().to_numpy(dtype=float)
        mean, sd, lo, hi = bootstrap_mean_ci(diff, rng)
        paired_diffs[method] = {
            "contrast": f"{method} minus {baseline}",
            "mean_ari_difference": mean,
            "sd_ari_difference": sd,
            "bootstrap_ci95_low": lo,
            "bootstrap_ci95_high": hi,
        }
    return pd.DataFrame(summary_rows), paired_diffs


def save_figure(rows: pd.DataFrame, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    order = list(METHODS)
    data = [rows.loc[rows["method"] == m, "ari"].to_numpy() for m in order]
    fig, ax = plt.subplots(figsize=(10.5, 5.2))
    ax.boxplot(data, tick_labels=[m.replace("_", "\n") for m in order],
               showmeans=True, meanline=True)
    ax.set_ylabel("Adjusted Rand Index against hidden synthetic archetypes")
    ax.set_title("Full-year recovery across independent synthetic seeds")
    ax.grid(axis="y", alpha=0.25)
    ax.spines[["top", "right"]].set_visible(False)
    fig.tight_layout()
    fig.savefig(path, dpi=220, bbox_inches="tight")
    plt.close(fig)


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--runs", type=int, default=20)
    parser.add_argument("--data-seed-start", type=int, default=100)
    parser.add_argument("--model-seed-offset", type=int, default=10000)
    parser.add_argument("--stability-runs", type=int, default=8)
    parser.add_argument("--bootstrap-seed", type=int, default=20261029)
    parser.add_argument(
        "--existing-run-metrics",
        type=Path,
        help="Rebuild summaries and reports from saved seed-level metrics without refitting.",
    )
    return parser


def main() -> int:
    logging.basicConfig(level=logging.WARNING, format="%(levelname)s %(message)s")
    args = _parser().parse_args()
    if args.runs < 2:
        raise ValueError("At least two independent runs are required for intervals.")
    if args.existing_run_metrics:
        results = pd.read_csv(args.existing_run_metrics)
        # Version 1 of the saved run file placed the model seed in the
        # data_seed column for the four fixed-K methods. Recover both keys
        # deterministically from the configured seed offsets before paired
        # seed-level contrasts are calculated.
        if "model_seed" not in results.columns:
            selected_method = "behavioral_51_pca95_selected_k"
            selected = results["method"] == selected_method
            results["model_seed"] = np.where(
                selected,
                args.model_seed_offset + results["data_seed"] - args.data_seed_start,
                results["data_seed"],
            ).astype(int)
            results.loc[~selected, "data_seed"] = (
                args.data_seed_start + results.loc[~selected, "model_seed"]
                - args.model_seed_offset
            )
            results["data_seed"] = results["data_seed"].astype(int)
    else:
        records = []
        for i in range(args.runs):
            data_seed = args.data_seed_start + i
            model_seed = args.model_seed_offset + i
            logger.warning("Full-year replicate %d/%d (data seed=%d, model seed=%d)",
                           i + 1, args.runs, data_seed, model_seed)
            records.extend(run_one(data_seed, model_seed,
                                   stability_runs=args.stability_runs))

        results = pd.DataFrame(records)

    observed_data_seeds = sorted(results["data_seed"].astype(int).unique().tolist())
    if len(observed_data_seeds) < 2:
        raise ValueError("Saved metrics must contain at least two independent data seeds.")
    for method in METHODS:
        method_seeds = sorted(
            results.loc[results["method"] == method, "data_seed"]
            .astype(int).unique().tolist()
        )
        if method_seeds != observed_data_seeds:
            raise ValueError(f"Method {method} has mismatched seed keys: {method_seeds}")
    args.runs = len(observed_data_seeds)
    args.data_seed_start = observed_data_seeds[0]
    if "model_seed" in results.columns:
        args.model_seed_offset = int(results["model_seed"].astype(int).min())

    out_dir = ROOT / "outputs" / "research_additions"
    out_dir.mkdir(parents=True, exist_ok=True)
    raw_path = out_dir / "synthetic_365_seed_runs.csv"
    results.to_csv(raw_path, index=False)
    summary, paired = summarize(results, args.bootstrap_seed)
    summary_path = out_dir / "synthetic_365_seed_summary.csv"
    summary.to_csv(summary_path, index=False)
    fig_path = ROOT / "outputs" / "figures" / "research_additions" / "synthetic_365_baseline_comparison.png"
    save_figure(results, fig_path)

    selected = results[results["method"] == "behavioral_51_pca95_selected_k"]
    selection_frequency = selected["k"].value_counts().sort_index().to_dict()
    metadata = {
        "study": "synthetic_365_day_independent_seed_replication_and_shape_baselines",
        "n_consumers": 200,
        "n_days": 365,
        "hourly_records_per_run": 200 * 365 * 24,
        "independent_runs": int(args.runs),
        "data_seeds": list(range(args.data_seed_start, args.data_seed_start + args.runs)),
        "model_seeds": list(range(args.model_seed_offset, args.model_seed_offset + args.runs)),
        "stability_restarts_per_k": args.stability_runs,
        "k_candidates": list(range(2, 11)),
        "bootstrap": {"unit": "independent synthetic generation seed",
                      "draws": 5000, "seed": args.bootstrap_seed,
                      "interval": "percentile 95% confidence interval"},
        "selected_k_frequency": selection_frequency,
        "methods": METHODS,
        "paired_ari_differences_vs_shape24_no_pca": paired,
        "software": {"python": platform.python_version(), "numpy": np.__version__,
                     "pandas": pd.__version__, "scipy": scipy.__version__,
                     "scikit_learn": sklearn.__version__},
        "outputs": {"run_metrics": str(raw_path.relative_to(ROOT)),
                    "summary": str(summary_path.relative_to(ROOT)),
                    "figure": str(fig_path.relative_to(ROOT))},
        "interpretation_limit": (
            "Intervals quantify variation across this synthetic generator's independent seeds; "
            "they do not quantify uncertainty for a real household population."
        ),
    }
    json_path = out_dir / "synthetic_365_seed_study.json"
    json_path.write_text(json.dumps(metadata, indent=2, default=str), encoding="utf-8")

    report_lines = [
        "# Full-year synthetic replication and shape baseline study", "",
        f"- Consumers per run: 200", f"- Days per run: 365",
        f"- Independent generator seeds: {args.runs} ({args.data_seed_start}--{args.data_seed_start + args.runs - 1})",
        f"- Candidate K values: 2--10; restart runs per K: {args.stability_runs}",
        "- Ground-truth archetypes were used only after fitting to calculate ARI/NMI.",
        "- Baselines use fixed K=4 for a like-for-like test; the primary pipeline also reports its selected K.",
        "- 95% bootstrap intervals resample independent data seeds (5,000 draws), not households or hourly rows.",
        "", "## Mean recovery and internal quality", "",
        "| Method | ARI (95% CI) | NMI (95% CI) | Silhouette mean | K counts |",
        "|---|---:|---:|---:|---|",
    ]
    for _, row in summary.iterrows():
        k_counts = row["selected_k_counts"]
        report_lines.append(
            f"| {row['description']} | {row['ari_mean']:.3f} "
            f"[{row['ari_ci95_low']:.3f}, {row['ari_ci95_high']:.3f}] | "
            f"{row['nmi_mean']:.3f} [{row['nmi_ci95_low']:.3f}, {row['nmi_ci95_high']:.3f}] | "
            f"{row['silhouette_mean']:.3f} | `{json.dumps(k_counts, sort_keys=True)}` |"
        )
    report_lines += ["", "## Paired ARI differences versus the 24-bin no-PCA baseline", "",
                     "Positive values favor the named method in this synthetic experiment.", "",
                     "| Contrast | Mean difference (95% bootstrap CI) |", "|---|---:|"]
    for contrast in paired.values():
        report_lines.append(
            f"| {contrast['contrast']} | {contrast['mean_ari_difference']:.3f} "
            f"[{contrast['bootstrap_ci95_low']:.3f}, {contrast['bootstrap_ci95_high']:.3f}] |"
        )
    report_lines += [
        "", "## Reproducibility and limits", "",
        f"- Raw seed-level metrics: `{raw_path.relative_to(ROOT).as_posix()}`",
        f"- Summary CSV: `{summary_path.relative_to(ROOT).as_posix()}`",
        f"- Figure: `{fig_path.relative_to(ROOT).as_posix()}`",
        f"- Metadata: `{json_path.relative_to(ROOT).as_posix()}`",
        "- Results depend on the repository's synthetic generator. They do not establish recovery on measured households.",
        "- Bootstrap intervals summarize seed-to-seed variation under this generator, not population sampling uncertainty.",
        "",
    ]
    report_path = ROOT / "outputs" / "reports" / "synthetic_365_seed_study.md"
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text("\n".join(report_lines), encoding="utf-8")
    print(f"Run metrics: {raw_path}")
    print(f"Summary: {summary_path}")
    print(f"Report: {report_path}")
    print(f"Figure: {fig_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
