"""
Seasonal Analysis Module (Improvement 2)

Estimates the two channels of the seasonal model from the data alone:

    * Magnitude channel - how much mean daily energy swings between seasons.
    * Timing (shape) channel - how the hour of peak demand moves across seasons.

Both are per-consumer effects in the generator, drawn independently of archetype,
so the seasonal analysis is deliberately separate from the clustering: it answers
"does demand have a seasonal rhythm?" rather than "do consumers group the same
way?".

Two guards keep this honest:

    1. The estimate never sees the hidden seasonal_phase column. When that column
       IS present (synthetic data only) it is used purely as ground truth to
       score the estimate, exactly as `archetype` scores the clusters.
    2. The magnitude channel is mean-corrected over the window, so within one
       window it cannot leak into scale features. The timing channel is what
       changes the normalized load shape across seasons.

Run via:  py src/seasonal_analysis.py
"""

import json
import logging
from pathlib import Path
from typing import Optional

import matplotlib

matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from data_loader import month_to_season

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

SEASON_ORDER = ['winter', 'spring', 'summer', 'autumn']
# Representative day-of-year of each meteorological season (northern): the
# 15th of Feb, May, Aug, Nov. Used only to turn a recovered season into a
# single day-of-year for correlation against the hidden phase.
SEASON_REP_DOY = {'winter': 46, 'spring': 137, 'summer': 228, 'autumn': 320}

_SEASON_COLORS = {'winter': '#4c72b0', 'spring': '#55a868', 'summer': '#c44e52',
                  'autumn': '#dd8452'}


def _guard_season_column(preprocessed: pd.DataFrame, season_col: str) -> bool:
    """True when the panel has a usable season column with at least two values."""
    if season_col not in preprocessed.columns:
        return False
    return preprocessed[season_col].nunique() >= 2


def _daily_energy_by_season(preprocessed: pd.DataFrame,
                            season_col: str = 'season') -> pd.DataFrame:
    """Per (consumer, season) mean daily kWh.

    Records are hourly in the standard panel, so daily energy is the sum of the
    consumer's energy within a season divided by the number of distinct days.
    Returns a DataFrame with columns consumer_id, season, n_days, mean_daily_kwh.
    """
    grouped = (preprocessed.groupby(['consumer_id', season_col])
               .agg(total_kwh=('energy_consumption_kwh', 'sum'),
                    n_days=('timestamp', lambda s: s.dt.normalize().nunique()))
               .reset_index())
    grouped['mean_daily_kwh'] = grouped['total_kwh'] / grouped['n_days'].clip(lower=1)
    return grouped


def _seasonal_amplitude_per_consumer(daily: pd.DataFrame) -> pd.Series:
    """Fractional seasonal swing per consumer: (max - min) / (2 * mean).

    Only consumers that were observed in at least two seasons contribute; the
    swing is undefined (NaN) for the rest. Median across consumers is the
    estimate reported to the caller.
    """
    pivot = daily.pivot_table(index='consumer_id', columns='season',
                              values='mean_daily_kwh')
    present = pivot.notna().sum(axis=1)
    eligible = pivot[present >= 2]
    if eligible.empty:
        return pd.Series(dtype=float)
    span = eligible.max(axis=1) - eligible.min(axis=1)
    mean_level = eligible.mean(axis=1)
    return (span / (2.0 * mean_level)).replace([np.inf, -np.inf], np.nan)


def _season_of_phase(phase: float) -> str:
    """Season that contains a day-of-year (1..365), northern meteorological."""
    month = int(np.clip(((phase - 1) // 30) + 1, 1, 12))
    return str(month_to_season(np.array([month]), 'northern')[0])


def _recover_phase_from_seasons(daily: pd.DataFrame) -> pd.Series:
    """Per-consumer peak-season estimate -> representative day-of-year.

    The consumer's estimated peak season is the season with its highest mean
    daily kWh. That is a coarse estimate (only four possible values), so the
    correlation against the hidden phase is expected to be positive but modest.
    """
    pivot = daily.pivot_table(index='consumer_id', columns='season',
                              values='mean_daily_kwh')
    if pivot.empty:
        return pd.Series(dtype=float)
    peak_season = pivot.idxmax(axis=1)
    return peak_season.map(SEASON_REP_DOY)


def _mean_shape_by_season(preprocessed: pd.DataFrame,
                          season_col: str = 'season') -> pd.DataFrame:
    """Normalized mean 24-hour load shape per season (shape channel).

    Shape = mean energy by hour within a season, normalized to sum to 1. The
    daily total is removed by construction, so any movement in the peak hour
    across seasons is the timing channel, not magnitude.
    """
    rows = []
    for season, group in preprocessed.groupby(season_col):
        by_hour = (group.groupby('hour')['energy_consumption_kwh'].mean()
                   .reindex(range(24), fill_value=0.0))
        normalized = by_hour / by_hour.sum()
        rows.append({'season': season, 'hour': np.arange(24), 'share': normalized.to_numpy()})
    return rows


def run_seasonal_analysis(raw_data: pd.DataFrame,
                          preprocessed: pd.DataFrame,
                          labels: np.ndarray,
                          consumer_order: list,
                          output_dir: str = 'outputs/figures',
                          reports_dir: str = 'outputs/reports',
                          metrics_dir: str = 'outputs/metrics',
                          hidden_phase_col: str = 'seasonal_phase',
                          season_col: str = 'season') -> dict:
    """Run the full seasonal analysis and persist figures / report.

    Args:
        raw_data: Panel as generated (may carry the hidden seasonal_phase column).
        preprocessed: Cleaned panel used by the pipeline (has a season column).
        labels: Cluster labels aligned with consumer_order (used for a
            cluster x season cross-check; the seasonal rhythm itself is drawn
            independently of archetype, so this should show no structure).
        consumer_order: Consumer ids in label order.
        output_dir: Directory for figures.
        reports_dir: Directory for the markdown report.
        metrics_dir: Directory for the machine-readable metrics JSON.
        hidden_phase_col: Column in raw_data holding hidden ground truth phase.
        season_col: Column holding the season label.

    Returns:
        Dictionary of seasonal metrics, or {'seasonal': False, 'reason': ...}
        when the panel has no usable season column.
    """
    output_dir = Path(output_dir)
    reports_dir = Path(reports_dir)
    metrics_dir = Path(metrics_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    reports_dir.mkdir(parents=True, exist_ok=True)
    metrics_dir.mkdir(parents=True, exist_ok=True)

    if not _guard_season_column(preprocessed, season_col):
        reason = (f"seasonal analysis skipped: no '{season_col}' column with "
                  f">= 2 distinct values in the panel")
        logger.info(reason)
        return {'seasonal': False, 'reason': reason}

    daily = _daily_energy_by_season(preprocessed, season_col)
    seasons_present = [s for s in SEASON_ORDER if s in set(daily['season'])]

    mean_daily_by_season = (
        daily.groupby('season')['mean_daily_kwh'].mean().reindex(seasons_present).round(4)
    )

    amplitude_per_consumer = _seasonal_amplitude_per_consumer(daily)
    has_truth = hidden_phase_col in raw_data.columns

    # Estimated per-consumer phase from the recovered peak season. Only
    # consumers with >= 2 seasons of data have an estimate.
    estimated_phase_doy = _recover_phase_from_seasons(daily)

    phase_recovery_corr = None
    phase_accuracy = None
    n_truth_consumers = 0
    if has_truth:
        truth_phase = (raw_data.groupby('consumer_id')[hidden_phase_col].first()
                       .dropna())
        n_truth_consumers = len(truth_phase)
        joined = pd.concat(
            [estimated_phase_doy.rename('estimated_doy'),
             truth_phase.rename('truth_phase')], axis=1).dropna()
        if len(joined) >= 5:
            phase_recovery_corr = float(np.corrcoef(joined['estimated_doy'],
                                                    joined['truth_phase'])[0, 1])
        # Agreement of the coarse peak-season label vs the hidden phase season.
        truth_season = truth_phase.map(_season_of_phase)
        est_season = estimated_phase_doy.index.map(
            lambda c: _season_of_phase(estimated_phase_doy[c]) if pd.notna(estimated_phase_doy[c])
            else np.nan)
        agreement = pd.Series(est_season, index=estimated_phase_doy.index).eq(truth_season)
        valid = agreement.dropna()
        if len(valid):
            phase_accuracy = float(valid.mean())

    # Cluster x season cross-check. Because the seasonal phase is drawn
    # independently of archetype, mean daily energy should vary with season the
    # same way for every cluster: this table documents that there is no
    # archetype structure hiding inside the seasonal swing.
    label_by_consumer = pd.Series(labels, index=consumer_order, name='cluster')
    label_by_consumer.index.name = 'consumer_id'   # so reset_index() yields a mergeable key
    daily_with_cluster = daily.merge(label_by_consumer.reset_index(),
                                     on='consumer_id', how='left')
    cluster_season_mean = (daily_with_cluster
                           .pivot_table(index='cluster', columns='season',
                                        values='mean_daily_kwh')
                           .reindex(columns=seasons_present))
    cluster_amplitude = _seasonal_amplitude_per_consumer(
        # Reuse the per-consumer amplitude function at the cluster level: the
        # merged frame still carries the per-consumer id, so drop it first -
        # otherwise rename produces two `consumer_id` columns and the pivot fails.
        daily_with_cluster.drop(columns=['consumer_id'])
        .rename(columns={'cluster': 'consumer_id'}))

    shapes = _mean_shape_by_season(preprocessed, season_col)

    # ---- Figures ------------------------------------------------------------
    figures = []
    try:
        fig, ax = plt.subplots(figsize=(8, 5))
        for row in shapes:
            season = row['season']
            if season not in _SEASON_COLORS:
                continue
            ax.plot(row['hour'], row['share'] * 100.0,
                    color=_SEASON_COLORS[season], marker='o', ms=3,
                    label=season.title())
        ax.set_xlabel('Hour of day')
        ax.set_ylabel('Share of daily energy (%)')
        ax.set_title('Normalized load shape by season (timing channel)')
        ax.grid(alpha=0.3)
        ax.legend()
        fig.tight_layout()
        path = output_dir / 'seasonal_mean_shape_by_season.png'
        fig.savefig(path, dpi=150)
        plt.close(fig)
        figures.append(str(path))
    except Exception as exc:  # a plotting issue must not kill the run
        logger.warning(f"Could not render seasonal shape figure: {exc}")

    try:
        fig, axes = plt.subplots(1, 2, figsize=(11, 4.5))
        means = mean_daily_by_season.to_dict()
        axes[0].bar(list(means.keys()), list(means.values()),
                    color=[_SEASON_COLORS[s] for s in means.keys()])
        axes[0].set_title('Mean daily energy by season (magnitude channel)')
        axes[0].set_ylabel('Mean kWh per day')
        axes[0].grid(alpha=0.3, axis='y')

        peak_hours = {}
        for row in shapes:
            peak_hours[row['season']] = int(np.argmax(row['share']))
        axes[1].plot(list(peak_hours.keys()), list(peak_hours.values()),
                     marker='o', color='#2f4f6b')
        axes[1].set_title('Peak hour of the mean shape by season')
        axes[1].set_ylabel('Hour of peak demand')
        axes[1].set_ylim(0, 23)
        axes[1].grid(alpha=0.3)
        fig.tight_layout()
        path = output_dir / 'seasonal_daily_energy_and_peak_hour.png'
        fig.savefig(path, dpi=150)
        plt.close(fig)
        figures.append(str(path))
    except Exception as exc:
        logger.warning(f"Could not render seasonal magnitude figure: {exc}")
        peak_hours = {row['season']: int(np.argmax(row['share'])) for row in shapes}

    if has_truth:
        try:
            fig, ax = plt.subplots(figsize=(6, 6))
            joined = pd.concat([estimated_phase_doy.rename('est'),
                                truth_phase.rename('truth')], axis=1).dropna()
            ax.scatter(joined['truth'], joined['est'], s=8, alpha=0.5)
            lim = [0, 365]
            ax.plot(lim, lim, 'k--', alpha=0.4, label='perfect recovery')
            ax.set_xlabel('Hidden seasonal phase (day of year)')
            ax.set_ylabel('Estimated peak (day of year, season-level)')
            ax.set_title('Seasonal phase recovery (synthetic ground truth)')
            ax.set_xlim(*lim)
            ax.set_ylim(*lim)
            ax.grid(alpha=0.3)
            ax.legend()
            fig.tight_layout()
            path = output_dir / 'seasonal_phase_recovery.png'
            fig.savefig(path, dpi=150)
            plt.close(fig)
            figures.append(str(path))
        except Exception as exc:
            logger.warning(f"Could not render phase recovery figure: {exc}")

    results = {
        'seasonal': True,
        'seasons_present': seasons_present,
        'mean_daily_kwh_by_season': mean_daily_by_season.to_dict(),
        'peak_hour_by_season': peak_hours,
        'amplitude_estimate': (float(amplitude_per_consumer.median())
                               if len(amplitude_per_consumer) else None),
        'amplitude_estimate_q25': (float(amplitude_per_consumer.quantile(0.25))
                                   if len(amplitude_per_consumer) else None),
        'amplitude_estimate_q75': (float(amplitude_per_consumer.quantile(0.75))
                                   if len(amplitude_per_consumer) else None),
        'n_consumers_with_amplitude': int(amplitude_per_consumer.notna().sum()),
        'phase_recovery_corr': phase_recovery_corr,
        'phase_accuracy': phase_accuracy,
        'n_truth_consumers': n_truth_consumers,
        'cluster_amplitude_median': (
            {int(k): (float(v) if pd.notna(v) else None)
             for k, v in cluster_amplitude.items()}
            if len(cluster_amplitude) else {}
        ),
        'figures': figures,
    }

    (metrics_dir / 'seasonal_analysis_metrics.json').write_text(
        json.dumps(results, indent=2, default=str), encoding='utf-8')

    report_lines = [
        "# Seasonal Analysis Report (Improvement 2)",
        "",
        "This file is generated from the data alone. The hidden seasonal_phase",
        "column (synthetic data only) is used strictly as ground truth to score",
        "the estimate, never as an input.",
        "",
        f"- Seasons present: {seasons_present}",
        f"- Mean daily kWh by season: {results['mean_daily_kwh_by_season']}",
        f"- Estimated magnitude amplitude (fractional swing of daily totals): "
        f"{results['amplitude_estimate']}",
        f"- Mean peak hour by season: {results['peak_hour_by_season']}",
    ]
    if has_truth:
        report_lines += [
            "",
            "## Phase recovery (synthetic ground truth only)",
            "",
            f"- Pearson r between season-level estimate and hidden phase: "
            f"{phase_recovery_corr}",
            f"- Peak-season label agreement: {phase_accuracy} "
            f"(over {n_truth_consumers} consumers with a hidden phase)",
            "",
            "The estimate is deliberately coarse (one of four seasons), so a",
            "moderate r is expected and correct.",
        ]
    report_lines += [
        "",
        "## Cluster x season cross-check",
        "",
        "Because the seasonal phase is drawn independently of archetype, the",
        "seasonal swing should be the same for every cluster. The table below is",
        "the evidence for that: mean daily kWh per (cluster, season).",
        "",
        "```",
        cluster_season_mean.round(3).to_string(),
        "```",
        "",
        f"- Median seasonal amplitude per cluster: {results['cluster_amplitude_median']}",
        "",
        "## Channel interpretation",
        "",
        "- Magnitude channel: mean-corrected over the window, so it changes WHEN",
        "  energy is used, not the long-run average. It cannot inflate or create a",
        "  spurious cluster from scale differences.",
        "- Timing channel: moves the daily peak hours across the year and is what",
        "  changes the normalized load shape. It is renormalised so it never",
        "  changes a daily total.",
        "",
    ]
    (reports_dir / 'seasonal_analysis_report.md').write_text(
        "\n".join(report_lines), encoding='utf-8')

    logger.info(
        f"Seasonal analysis done: amplitude={results['amplitude_estimate']}, "
        f"phase r={phase_recovery_corr}"
    )
    return results


if __name__ == "__main__":
    from project_paths import anchor_to_project_root
    from data_loader import SeasonalConfig, generate_synthetic_data
    from preprocessing import preprocess_pipeline

    anchor_to_project_root()

    # Small smoke run: one full year so all four seasons are present.
    raw = generate_synthetic_data(n_consumers=80, n_days=365,
                                  start_date='2024-01-01',
                                  seasonal=SeasonalConfig(enabled=True))
    clean = preprocess_pipeline(raw.drop(columns=['archetype', 'seasonal_phase'],
                                         errors='ignore'))

    # Recover the real full-window segmentation with the same recipe the
    # pipeline uses, so the cluster x season cross-check (which should show no
    # archetype structure inside the seasonal swing) is computed on real
    # clusters instead of one all-zero placeholder cluster.
    from clustering import find_optimal_k, perform_kmeans, select_optimal_k
    from feature_engineering import engineer_all_features
    from pca_analysis import run_pca_pipeline

    features = engineer_all_features(clean, feature_set='behavioral')
    features = features.sort_values('consumer_id').reset_index(drop=True)
    order = features['consumer_id'].tolist()
    X_pca, _pca, _scaler, _n = run_pca_pipeline(features)
    k_values, inertia, silhouette, ch, db, stability = find_optimal_k(
        X_pca, (2, 8), 42, stability_runs=8)
    optimal_k, _trace = select_optimal_k(
        k_values, inertia, silhouette, ch, db, stability_by_k=stability)
    _, labels = perform_kmeans(X_pca, optimal_k, 42)

    result = run_seasonal_analysis(
        raw_data=raw, preprocessed=clean, labels=labels,
        consumer_order=order,
        output_dir='outputs/figures', reports_dir='outputs/reports',
        metrics_dir='outputs/metrics',
    )
    print(json.dumps(result, indent=2, default=str))