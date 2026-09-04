"""
Longitudinal Analysis Module (Improvement 1)

Answers one question that a single short window cannot: do the recovered consumer
groups still hold when you look at a longer period of time?

The observation window is split into several time segments. Within each segment
the same behavioural features are re-engineered, the same standardize -> PCA ->
K-Means recipe is re-fit, and the recovered labels are compared with the
full-window labels with the Adjusted Rand Index (which is invariant to label
permutation, so no matching step is needed). High and stable ARI means the groups
are temporally consistent - the clusters describe the consumer, not the season or
the month. It also reports the mean daily energy by month, so a long window's
temporal trend is visible at a glance.

This is a deliberate choice of a *re-fit* recipe rather than freezing one model:
it tests whether the structure itself is stable, not whether a single model
happens to give the same answer when asked twice.

Only meaningful for long windows, so the caller gates on n_days >=
LONGITUDINAL_MIN_DAYS (see energy_analysis). Run via: py src/longitudinal_analysis.py
"""

import json
import logging
from pathlib import Path

import matplotlib

matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from sklearn.cluster import KMeans
from sklearn.decomposition import PCA
from sklearn.metrics import adjusted_rand_score
from sklearn.preprocessing import StandardScaler

from feature_engineering import engineer_all_features, select_features

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

N_SEGMENTS_DEFAULT = 4
PCA_VARIANCE_THRESHOLD = 0.95
MIN_DAYS_PER_SEGMENT = 21


def _segment_ranges(preprocessed: pd.DataFrame, n_segments: int) -> list:
    """Equal-width time ranges covering the observation window.

    Args:
        preprocessed: Panel with a parsed timestamp column.
        n_segments: Number of segments to split into.

    Returns:
        List of (start, end) inclusive pandas Timestamps.
    """
    start = preprocessed['timestamp'].min()
    end = preprocessed['timestamp'].max()
    span = (end - start) / n_segments
    ranges = []
    for i in range(n_segments):
        seg_start = start + i * span
        seg_end = start + (i + 1) * span if i < n_segments - 1 else end
        ranges.append((seg_start, seg_end))
    return ranges


def _fit_segment_clusters(segment: pd.DataFrame,
                          optimal_k: int,
                          feature_set: str,
                          random_seed: int) -> tuple:
    """Engineer behavioural features for one segment and re-fit PCA + K-Means.

    Args:
        segment: Panel subset for the segment.
        optimal_k: Number of clusters to fit (taken from the full-window run).
        feature_set: Feature group used for the full-window run.
        random_seed: Seed for the K-Means restart.

    Returns:
        Tuple of (labels array aligned with the segment's consumer ids,
        consumer_ids list).
    """
    features = engineer_all_features(segment, feature_set=feature_set)
    features = select_features(features, feature_group=feature_set)
    feature_cols = [c for c in features.columns if c != 'consumer_id']
    consumer_ids = features['consumer_id'].tolist()

    X = StandardScaler().fit_transform(features[feature_cols].to_numpy(dtype=float))
    n_components = min(len(feature_cols),
                       int(np.searchsorted(np.cumsum(
                           PCA().fit(X).explained_variance_ratio_),
                           PCA_VARIANCE_THRESHOLD)) + 1)
    X_pca = PCA(n_components=n_components, random_state=random_seed).fit_transform(X)
    labels = KMeans(n_clusters=optimal_k, random_state=random_seed,
                    n_init=10).fit_predict(X_pca)
    return labels, consumer_ids


def _monthly_daily_energy(preprocessed: pd.DataFrame) -> pd.DataFrame:
    """Mean daily kWh per calendar month, for the temporal trend figure."""
    daily = (preprocessed.groupby(['consumer_id', preprocessed['timestamp'].dt.to_period('M')])
             .agg(total=('energy_consumption_kwh', 'sum'),
                  n_days=('timestamp', lambda s: s.dt.normalize().nunique()))
             .reset_index())
    daily['mean_daily_kwh'] = daily['total'] / daily['n_days'].clip(lower=1)
    monthly = daily.groupby('timestamp')['mean_daily_kwh'].mean()
    monthly.index = monthly.index.astype(str)
    return monthly


def run_longitudinal_analysis(preprocessed: pd.DataFrame,
                              labels: np.ndarray,
                              consumer_order: list,
                              optimal_k: int,
                              random_seed: int = 42,
                              n_segments: int = N_SEGMENTS_DEFAULT,
                              feature_set: str = 'behavioral',
                              output_dir: str = 'outputs/figures',
                              reports_dir: str = 'outputs/reports',
                              metrics_dir: str = 'outputs/metrics') -> dict:
    """Run the longitudinal analysis and persist figures / report.

    Args:
        preprocessed: Cleaned panel (full window) with parsed timestamps.
        labels: Full-window cluster labels aligned with consumer_order.
        consumer_order: Consumer ids in label order.
        optimal_k: Number of clusters selected on the full window.
        random_seed: Seed for the per-segment K-Means fits.
        n_segments: Number of time segments to split the window into.
        feature_set: Feature group to re-engineer per segment.
        output_dir: Directory for figures.
        reports_dir: Directory for the markdown report.
        metrics_dir: Directory for the machine-readable metrics JSON.

    Returns:
        Dictionary of longitudinal metrics.
    """
    output_dir = Path(output_dir)
    reports_dir = Path(reports_dir)
    metrics_dir = Path(metrics_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    reports_dir.mkdir(parents=True, exist_ok=True)
    metrics_dir.mkdir(parents=True, exist_ok=True)

    full_label = pd.Series(labels, index=consumer_order, name='cluster')

    ranges = _segment_ranges(preprocessed, n_segments)
    segment_ari = []
    segment_consumers = []
    segment_ranges_labeled = []
    for seg_index, (seg_start, seg_end) in enumerate(ranges):
        n_days = (seg_end - seg_start).days + 1
        if n_days < MIN_DAYS_PER_SEGMENT:
            logger.info(f"Skipping segment {seg_index}: only {n_days} days")
            continue
        segment = preprocessed[
            (preprocessed['timestamp'] >= seg_start) &
            (preprocessed['timestamp'] <= seg_end)
        ].copy()
        seg_labels, seg_order = _fit_segment_clusters(segment, optimal_k,
                                                      feature_set, random_seed)
        seg_label = pd.Series(seg_labels, index=seg_order)
        common = seg_label.index.intersection(full_label.index)
        if len(common) < 5:
            segment_ari.append(np.nan)
            continue
        ari = adjusted_rand_score(full_label[common].to_numpy(),
                                  seg_label[common].to_numpy())
        segment_ari.append(float(ari))
        segment_consumers.append(len(common))
        segment_ranges_labeled.append(
            f"{seg_index}: {seg_start:%Y-%m-%d} to {seg_end:%Y-%m-%d}")

    valid_ari = [a for a in segment_ari if not np.isnan(a)]
    mean_stability = float(np.mean(valid_ari)) if valid_ari else None

    monthly = _monthly_daily_energy(preprocessed)
    monthly_dict = monthly.round(4).to_dict()

    results = {
        'n_segments': n_segments,
        'segment_ari_vs_full': segment_ari,
        'segment_labels': segment_ranges_labeled,
        'mean_temporal_stability_ari': mean_stability,
        'monthly_mean_daily_kwh': monthly_dict,
        'n_consumers_per_segment': segment_consumers,
        'optimal_k': int(optimal_k),
        'feature_set': feature_set,
    }

    # ---- Figures ------------------------------------------------------------
    figures = []
    try:
        fig, axes = plt.subplots(1, 2, figsize=(11, 4.5))
        axes[0].bar(range(len(segment_ari)), segment_ari,
                    color=['#55a868' if not np.isnan(a) else '#dd8452'
                           for a in segment_ari])
        axes[0].axhline(mean_stability if mean_stability is not None else 0.0,
                        color='#c44e52', ls='--', lw=1,
                        label=f"mean {mean_stability:.3f}")
        axes[0].set_xticks(range(len(segment_ari)))
        axes[0].set_ylim(0, 1)
        axes[0].set_xlabel('Time segment')
        axes[0].set_ylabel('ARI vs full-window labels')
        axes[0].set_title('Temporal cluster stability across segments')
        axes[0].grid(alpha=0.3, axis='y')
        axes[0].legend()

        axes[1].plot(range(len(monthly)), monthly.to_numpy(),
                     marker='o', ms=4, color='#2f4f6b')
        axes[1].set_xticks(range(len(monthly)))
        axes[1].set_xticklabels([str(m)[:7] for m in monthly.index],
                                rotation=45, ha='right', fontsize=8)
        axes[1].set_ylabel('Mean kWh per day')
        axes[1].set_title('Mean daily energy by month (temporal trend)')
        axes[1].grid(alpha=0.3)
        fig.tight_layout()
        path = output_dir / 'longitudinal_cluster_stability.png'
        fig.savefig(path, dpi=150)
        plt.close(fig)
        figures.append(str(path))
    except Exception as exc:
        logger.warning(f"Could not render longitudinal figure: {exc}")

    results['figures'] = figures

    (metrics_dir / 'longitudinal_analysis_metrics.json').write_text(
        json.dumps(results, indent=2, default=str), encoding='utf-8')

    report_lines = [
        "# Longitudinal Analysis Report (Improvement 1)",
        "",
        "The observation window was split into time segments. Behavioural",
        "features were re-engineered and the standardize -> PCA -> K-Means recipe",
        "re-fit inside each segment, then the segment labels were compared with",
        "the full-window labels using the Adjusted Rand Index (permutation-",
        "invariant, so no label-matching step is needed).",
        "",
        f"- Window segments: {segment_ranges_labeled}",
        f"- Consumers per segment: {segment_consumers}",
        f"- Optimal K (from the full-window run): {optimal_k}",
        f"- Segment ARI vs full window: {segment_ari}",
        f"- Mean temporal cluster stability (ARI): {mean_stability}",
        "",
        "Interpretation: A high, flat value means the consumer groups are a",
        "property of the consumers, not of the month or season; a value that",
        "collapses in one segment means the structure is not stable across time",
        "within this window.",
        "",
        "## Mean daily energy by month",
        "",
        "```",
        pd.Series(monthly_dict).round(3).to_string(),
        "```",
        "",
    ]
    (reports_dir / 'longitudinal_analysis_report.md').write_text(
        "\n".join(report_lines), encoding='utf-8')

    logger.info(
        f"Longitudinal analysis done: mean temporal stability ARI = {mean_stability}"
    )
    return results


if __name__ == "__main__":
    from project_paths import anchor_to_project_root
    from data_loader import generate_synthetic_data
    from preprocessing import preprocess_pipeline

    anchor_to_project_root()

    # Small smoke run on a one-year window.
    raw = generate_synthetic_data(n_consumers=60, n_days=365,
                                  start_date='2024-01-01')
    clean = preprocess_pipeline(raw.drop(columns=['archetype', 'seasonal_phase'],
                                         errors='ignore'))

    # Recover the full-window segmentation with the same recipe the pipeline
    # uses, so segment-vs-full ARI measures something real. (A constant label
    # vector here would make every segment ARI ~ 0 by construction and prove
    # nothing about temporal stability.)
    from clustering import find_optimal_k, perform_kmeans, select_optimal_k
    from feature_engineering import engineer_all_features
    from pca_analysis import run_pca_pipeline

    features = engineer_all_features(clean, feature_set='behavioral')
    features = features.sort_values('consumer_id').reset_index(drop=True)
    order = features['consumer_id'].tolist()
    X_pca, _pca, _scaler, _n_components = run_pca_pipeline(features)
    k_values, inertia, silhouette, ch, db, stability = find_optimal_k(
        X_pca, (2, 8), 42, stability_runs=8)
    optimal_k, _trace = select_optimal_k(
        k_values, inertia, silhouette, ch, db, stability_by_k=stability)
    _, labels = perform_kmeans(X_pca, optimal_k, 42)

    result = run_longitudinal_analysis(
        preprocessed=clean,
        labels=labels,
        consumer_order=order,
        optimal_k=optimal_k,
        random_seed=42,
        n_segments=4,
        output_dir='outputs/figures', reports_dir='outputs/reports',
        metrics_dir='outputs/metrics',
    )
    print(json.dumps(result, indent=2, default=str))