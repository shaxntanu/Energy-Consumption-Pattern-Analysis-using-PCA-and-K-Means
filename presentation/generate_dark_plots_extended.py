"""
Generate Dark-Mode Versions of the Remaining Chart Producers

Extends presentation/generate_dark_plots.py. That script themes the EDA, PCA,
clustering and per-feature-set ablation figures; this one themes every other
Matplotlib chart producer in the pipeline:

    validation             -> archetype_recovery.png, archetype_crosstab.png
    run_seed_robustness    -> seed_robustness.png
    run_ablation_study     -> ablation_comparison.png  (the cross-arm comparison)
    explainability         -> shap_cluster_importance.png
    longitudinal_analysis  -> longitudinal_cluster_stability.png
    seasonal_analysis      -> seasonal_mean_shape_by_season.png
                             seasonal_daily_energy_and_peak_hour.png
                             seasonal_phase_recovery.png

How it reuses the existing system
---------------------------------
Identical theme mechanism: it imports dark_theme.apply_dark_theme(), monkey-
patches sns.set_style / plt.style.use to a forcer before importing the chart
modules (so each module's import-time plot default is the dark theme), and writes
into the same dark_mode_plots/figures/ tree. Original, light-mode charts in
outputs/ are never touched, and the per-arm ablation output is left to the
existing generator.

How it avoids regenerating the pipeline
---------------------------------------
Four producers are re-rendered from the tables the pipeline already persisted
under outputs/metrics/ using their own plot functions (nothing is recomputed):

    - validation:     plot_recovery_by_k + plot_recovery_crosstab
    - seed robustness: plot_seed_robustness
    - ablation:       plot_ablation_comparison

The longitudinal and seasonal figures are re-drawn from the summary JSONs the
pipeline wrote (segments, monthly trend, seasons, peak hours), so they match the
reported numbers exactly. The two seasonal figures that need data the summary
does not carry - the per-season 24-hour load shape and the per-consumer phase
scatter - are recomputed from a fresh generator run, because that is the only
faithful source for them. That recompute touches only the generator +
preprocessing + the seasonal module's own helper functions; it does not run PCA,
the K sweep, clustering, profiling or the ablation study.

Run via:  py presentation/generate_dark_plots_extended.py
"""

import argparse
import json
import logging
import os
import sys
from pathlib import Path

# Non-interactive backend FIRST, before any chart module imports matplotlib.
os.environ['MPLBACKEND'] = 'Agg'
import matplotlib
matplotlib.use('Agg', force=True)

# Add src/ (for the chart modules) and presentation/ (for dark_theme) to the path.
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'src'))
sys.path.insert(0, str(Path(__file__).resolve().parent))

import matplotlib.pyplot as plt
import seaborn as sns

from dark_theme import apply_dark_theme, COLORS

logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)

# MONKEY PATCH: force every downstream sns.set_style / plt.style.use to the dark theme.
_original_set_style = sns.set_style
_original_style_use = plt.style.use


def force_dark_style(*args, **kwargs):
    apply_dark_theme()


sns.set_style = force_dark_style
plt.style.use = force_dark_style
apply_dark_theme()

# Import the chart modules AFTER the patch so their import-time plot defaults
# (e.g. validation's sns.set_style('whitegrid')) land on the dark theme.
import run_ablation_study
import run_seed_robustness
import seasonal_analysis
import validation

OUTDIR = ROOT / 'dark_mode_plots' / 'figures'
METRICS = ROOT / 'outputs' / 'metrics'
METADATA = ROOT / 'models' / 'analysis_metadata.json'

_SEASON_COLORS = seasonal_analysis._SEASON_COLORS


def _out(name):
    OUTDIR.mkdir(parents=True, exist_ok=True)
    return OUTDIR / name


def _load_json(path):
    if not path.exists():
        return None
    try:
        return json.loads(path.read_text(encoding='utf-8'))
    except Exception as exc:
        logger.warning(f"Could not read {path}: {exc}")
        return None


def _load_csv(name, index_col=None):
    path = METRICS / name
    if not path.exists():
        return None
    import pandas as pd
    try:
        return pd.read_csv(path, index_col=index_col)
    except Exception as exc:
        logger.warning(f"Could not read {path}: {exc}")
        return None


def _metadata():
    meta = _load_json(METADATA)
    if not meta:
        logger.warning("No models/analysis_metadata.json found; selected-K figures "
                       "will not mark the pipeline's choice.")
    return meta or {}


# --------------------------------------------------------------------------- #
# Validation figures (direct producer calls on persisted tables)
# --------------------------------------------------------------------------- #
def validation_figures():
    recovery = _load_csv('archetype_recovery.csv')
    if recovery is None:
        logger.info("  skip archetype_recovery.png (no archetype_recovery.csv)")
        return
    selected_k = _metadata().get('selected_k')
    validation.plot_recovery_by_k(recovery, selected_k=selected_k, output_dir=str(_out('.')))
    logger.info("  archetype_recovery.png")

    crosstab = _load_csv('archetype_crosstab.csv', index_col=0)
    if crosstab is None or crosstab.empty:
        logger.info("  skip archetype_crosstab.png (no archetype_crosstab.csv)")
        return
    validation.plot_recovery_crosstab(crosstab, output_dir=str(_out('.')))
    logger.info("  archetype_crosstab.png")


# --------------------------------------------------------------------------- #
# Seed robustness figure (direct producer call on persisted tables)
# --------------------------------------------------------------------------- #
def seed_robustness_figure():
    long_ = _load_csv('seed_robustness_by_seed.csv')
    summary = _load_csv('seed_robustness_summary.csv')
    if long_ is None or summary is None:
        logger.info("  skip seed_robustness.png (seed robustness tables missing)")
        return
    run_seed_robustness.plot_seed_robustness(long_, summary,
                                             output_dir=str(_out('.')))
    logger.info("  seed_robustness.png")


# --------------------------------------------------------------------------- #
# Ablation comparison figure (direct producer call on persisted table)
# --------------------------------------------------------------------------- #
def ablation_comparison_figure():
    results = _load_csv('ablation_study_results.csv')
    if results is None or results.empty:
        logger.info("  skip ablation_comparison.png (no ablation_study_results.csv)")
        return
    run_ablation_study.plot_ablation_comparison(results, output_dir=str(_out('.')))
    logger.info("  ablation_comparison.png")


# --------------------------------------------------------------------------- #
# Explainability figure (faithful re-render of the module's inline figure)
# --------------------------------------------------------------------------- #
def explainability_figure():
    data = _load_json(METRICS / 'explainability.json')
    if data is None or data.get('method') in (None, 'not_run'):
        logger.info("  skip shap_cluster_importance.png (explainability not run)")
        return
    method = data['method']
    per_cluster = data.get('per_cluster') or []
    if not per_cluster:
        logger.info("  skip shap_cluster_importance.png (no per-cluster features)")
        return

    import numpy as np
    apply_dark_theme()
    n_clusters = len(per_cluster)
    fig, axes = plt.subplots(1, n_clusters, figsize=(4.2 * n_clusters + 2, 6),
                             squeeze=False)
    for ax, entry in zip(axes[0], per_cluster):
        feats = entry.get('top_features', [])
        if not feats:
            ax.text(0.5, 0.5, 'no features', ha='center', va='center')
            ax.set_axis_off()
            continue
        names = [f['feature'] for f in feats][::-1]
        values = [f.get('mean_abs_shap', f.get('importance', 0.0)) for f in feats][::-1]
        ax.barh(names, values, color='#3BC9DE' if method == 'shap' else '#6C8CFF')
        ax.set_title(f'Cluster {entry["cluster"]}')
        ax.set_xlabel(method.replace('_', ' '))
    fig.suptitle('What separates each cluster, in feature units (post-hoc surrogate)')
    fig.tight_layout()
    fig.savefig(_out('shap_cluster_importance.png'), dpi=150)
    plt.close(fig)
    logger.info("  shap_cluster_importance.png")


# --------------------------------------------------------------------------- #
# Longitudinal figure (faithful re-render of the module's inline figure)
# --------------------------------------------------------------------------- #
def longitudinal_figure():
    data = _load_json(METRICS / 'longitudinal_analysis_metrics.json')
    if data is None or data.get('mean_temporal_stability_ari') is None:
        logger.info("  skip longitudinal_cluster_stability.png "
                    "(longitudinal analysis not run for this window)")
        return

    import numpy as np
    import pandas as pd
    apply_dark_theme()
    segment_ari = data.get('segment_ari_vs_full') or []
    mean_stability = data.get('mean_temporal_stability_ari')
    monthly = pd.Series(data.get('monthly_mean_daily_kwh') or {}, dtype=float)

    fig, axes = plt.subplots(1, 2, figsize=(11, 4.5))
    axes[0].bar(range(len(segment_ari)), segment_ari,
                color=['#55a868' if not (np.isnan(a) if isinstance(a, float)
                                         and np.isnan(a) else False)
                       else '#dd8452' for a in segment_ari])
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

    axes[1].plot(range(len(monthly)), monthly.to_numpy(), marker='o', ms=4,
                 color='#2f4f6b')
    axes[1].set_xticks(range(len(monthly)))
    axes[1].set_xticklabels([str(m)[:7] for m in monthly.index],
                            rotation=45, ha='right', fontsize=8)
    axes[1].set_ylabel('Mean kWh per day')
    axes[1].set_title('Mean daily energy by month (temporal trend)')
    axes[1].grid(alpha=0.3)
    fig.tight_layout()
    fig.savefig(_out('longitudinal_cluster_stability.png'), dpi=150)
    plt.close(fig)
    logger.info("  longitudinal_cluster_stability.png")


# --------------------------------------------------------------------------- #
# Seasonal figures
#   - magnitude + peak hour: re-rendered from the persisted summary JSON.
#   - per-season 24h shape + phase scatter: need data the summary does not carry,
#     so they are recomputed from a fresh generator run (see module docstring).
# --------------------------------------------------------------------------- #
def seasonal_summary_figures():
    data = _load_json(METRICS / 'seasonal_analysis_metrics.json')
    if data is None or not data.get('seasonal'):
        logger.info("  skip seasonal figures (seasonal analysis not run for this window)")
        return

    import numpy as np
    apply_dark_theme()
    means = data.get('mean_daily_kwh_by_season') or {}
    peak_hours = data.get('peak_hour_by_season') or {}

    fig, axes = plt.subplots(1, 2, figsize=(11, 4.5))
    axes[0].bar(list(means.keys()), list(means.values()),
                color=[_SEASON_COLORS[s] for s in means.keys() if s in _SEASON_COLORS])
    axes[0].set_title('Mean daily energy by season (magnitude channel)')
    axes[0].set_ylabel('Mean kWh per day')
    axes[0].grid(alpha=0.3, axis='y')

    axes[1].plot(list(peak_hours.keys()), list(peak_hours.values()),
                 marker='o', color='#2f4f6b')
    axes[1].set_title('Peak hour of the mean shape by season')
    axes[1].set_ylabel('Hour of peak demand')
    axes[1].set_ylim(0, 23)
    axes[1].grid(alpha=0.3)
    fig.tight_layout()
    fig.savefig(_out('seasonal_daily_energy_and_peak_hour.png'), dpi=150)
    plt.close(fig)
    logger.info("  seasonal_daily_energy_and_peak_hour.png")


def _seasonal_panel(include_shape, include_phase):
    """Recompute the two seasonal figures that need the hourly panel.

    Uses the same generator config as the committed 365-day flagship run
    (200 consumers, one full year, seasonality enabled, seed 42) and the seasonal
    module's own helpers, so the drawn data is genuine and consistent with the
    numbers reported in outputs/metrics/seasonal_analysis_metrics.json.
    """
    from data_loader import SeasonalConfig, generate_synthetic_data
    from preprocessing import preprocess_pipeline

    if not include_shape and not include_phase:
        return

    import numpy as np
    import pandas as pd
    apply_dark_theme()

    logger.info("  regenerating the hourly panel for the seasonal shape/phase figures "
                "(generator only, no clustering)")
    raw = generate_synthetic_data(n_consumers=200, n_days=365,
                                  start_date='2024-01-01',
                                  seasonal=SeasonalConfig(enabled=True))
    clean = preprocess_pipeline(raw.drop(columns=['archetype', 'seasonal_phase'],
                                         errors='ignore'))

    if include_shape:
        shapes = seasonal_analysis._mean_shape_by_season(clean, 'season')
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
        fig.savefig(_out('seasonal_mean_shape_by_season.png'), dpi=150)
        plt.close(fig)
        logger.info("  seasonal_mean_shape_by_season.png")

    if include_phase:
        daily = seasonal_analysis._daily_energy_by_season(clean, 'season')
        estimated = seasonal_analysis._recover_phase_from_seasons(daily)
        truth = (raw.groupby('consumer_id')['seasonal_phase'].first().dropna())
        joined = pd.concat([estimated.rename('est'), truth.rename('truth')],
                           axis=1).dropna()
        if len(joined) < 5:
            logger.info("  skip seasonal_phase_recovery.png (too few paired consumers)")
            return
        fig, ax = plt.subplots(figsize=(6, 6))
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
        fig.savefig(_out('seasonal_phase_recovery.png'), dpi=150)
        plt.close(fig)
        logger.info("  seasonal_phase_recovery.png")


def main():
    parser = argparse.ArgumentParser(
        description="Dark-mode versions of the remaining chart producers.")
    parser.add_argument('--skip-seasonal-shape', action='store_true',
                        help="Skip the seasonal per-season load-shape figure "
                             "(the only one that regenerates the hourly panel).")
    parser.add_argument('--skip-plotly', action='store_true',
                        help="Compatibility no-op; retained for symmetry.")
    args = parser.parse_args()

    logger.info("=" * 70)
    logger.info("DARK-MODE EXTENDED CHART GENERATION")
    logger.info("=" * 70)
    logger.info(f"Output: {OUTDIR}")

    # Reading-only producers on persisted tables.
    logger.info("Validation figures")
    validation_figures()
    logger.info("Seed robustness figure")
    seed_robustness_figure()
    logger.info("Ablation comparison figure")
    ablation_comparison_figure()
    logger.info("Explainability figure")
    explainability_figure()
    logger.info("Longitudinal figure")
    longitudinal_figure()
    logger.info("Seasonal summary figures")
    seasonal_summary_figures()

    # Panel-dependent seasonal figures (shape always; phase unless skipped too).
    logger.info("Seasonal shape / phase figures (regenerate hourly panel)")
    try:
        _seasonal_panel(include_shape=not args.skip_seasonal_shape,
                        include_phase=not args.skip_seasonal_shape)
    except Exception as exc:
        logger.warning(f"Seasonal shape/phase figures failed: {exc}")

    n = sum(1 for _ in OUTDIR.rglob('*.png')) if OUTDIR.exists() else 0
    logger.info("=" * 70)
    logger.info(f"COMPLETE. {n} dark-mode extended charts in {OUTDIR}")
    logger.info("Original light-mode plots in outputs/ are untouched.")
    logger.info("=" * 70)


if __name__ == '__main__':
    main()