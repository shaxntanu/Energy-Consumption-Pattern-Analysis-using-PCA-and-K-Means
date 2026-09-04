"""
Generate Dark-Mode Versions of the Project Plots (core set)

Reuses presentation/dark_theme.py and re-renders the core chart producers in
dark mode: EDA, PCA, clustering, and the per-feature-set ablation figures.

How it works
------------
It monkey-patches sns.set_style / plt.style.use to a forcer before importing
the chart modules (so each module's import-time plot default is the dark
theme), then writes into dark_mode_plots/figures/ (and dark_mode_plots/ablation/
... for the per-arm ablation set). Original light-mode charts in outputs/ are
never touched.

Faithfulness boundary (nothing is re-fitted, nothing is re-generated except the
tiny illustrative EDA panel):

  - EDA figures  : a small fresh 50x7 panel is generated (these are generic
                   illustrations; no EDA panel is persisted). ~seconds.
  - explained_variance.png   : re-rendered from the FITTED models/pca_model.pkl
                   plus the pipeline's recorded variance_threshold.
  - component_loadings.png   : re-rendered from outputs/metrics/pca_loadings.csv.
  - elbow / silhouette / k_selection : re-rendered from
                   outputs/metrics/clustering_metrics.csv + the recorded
                   selected_k in models/analysis_metadata.json.
  - per-arm ablation set     : the same three K figures from each arm's
                   outputs/ablation/<arm>/metrics/clustering_metrics.csv, plus
                   explained_variance from that arm's pca_results.csv and
                   component_loadings from its pca_loadings.csv.
  - pca_projection_2d.png and cluster_visualization_2d.png are SKIPPED with an
                   honest log: they need the per-consumer score matrix, which
                   the pipeline keeps in memory and never persists. Re-deriving
                   it would mean re-running generation + feature engineering,
                   which is out of scope for the dark-mode pass.

Run via:  py presentation/generate_dark_plots.py
"""

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

import json
import logging
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

logger.info("Dark theme force-applied via monkey patching")

# Import the chart modules AFTER the patch so their import-time plot defaults
# (e.g. clustering's sns.set_style('whitegrid')) land on the dark theme.
import clustering
import eda
import pca_analysis

OUTDIR = ROOT / 'dark_mode_plots' / 'figures'
ABLATION_OUTDIR = ROOT / 'dark_mode_plots' / 'ablation'
METRICS = ROOT / 'outputs' / 'metrics'
MODELS = ROOT / 'models'
ABLATION = ROOT / 'outputs' / 'ablation'

FEATURE_SETS = ['scale', 'shape', 'summary', 'behavioral', 'combined']
PCA_VARIANCE_THRESHOLD = 0.95  # the pipeline's configured threshold everywhere


def _load_json(path):
    if not Path(path).exists():
        return None
    try:
        return json.loads(Path(path).read_text(encoding='utf-8'))
    except Exception as exc:
        logger.warning(f"Could not read {path}: {exc}")
        return None


def create_output_structure():
    """Create the output directories (mirrors outputs/ structure)."""
    (OUTDIR).mkdir(parents=True, exist_ok=True)
    for fs in FEATURE_SETS:
        (ABLATION_OUTDIR / fs / 'figures').mkdir(parents=True, exist_ok=True)
    logger.info(f"Created output structure at {ROOT / 'dark_mode_plots'}")


# --------------------------------------------------------------------------- #
# EDA figures (a small fresh panel - these are generic illustrations)
# --------------------------------------------------------------------------- #
def generate_eda_plots(output_dir):
    from data_loader import generate_synthetic_data
    from preprocessing import preprocess_pipeline

    import numpy as np

    df = preprocess_pipeline(generate_synthetic_data(n_consumers=50, n_days=7))

    apply_dark_theme()
    numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()[:6]
    eda.plot_distributions(df, numeric_cols, output_dir)
    logger.info("  distributions.png")

    apply_dark_theme()
    eda.plot_hourly_patterns(df, output_dir)
    logger.info("  hourly_patterns.png")

    apply_dark_theme()
    eda.plot_weekday_weekend_comparison(df, output_dir)
    logger.info("  weekday_weekend_comparison.png")

    apply_dark_theme()
    eda.plot_correlation_heatmap(df, output_dir)
    logger.info("  correlation_heatmap.png")

    apply_dark_theme()
    eda.plot_consumption_variability(df, output_dir)
    logger.info("  consumption_variability.png")

    apply_dark_theme()
    eda.plot_boxplots_by_time(df, output_dir)
    logger.info("  boxplots_by_time.png")


# --------------------------------------------------------------------------- #
# PCA figures (re-rendered from the persisted fitted model + tables)
# --------------------------------------------------------------------------- #
def generate_pca_plots(output_dir):
    import joblib

    model_path = MODELS / 'pca_model.pkl'
    if not model_path.exists():
        logger.info("  skip explained_variance.png (no models/pca_model.pkl on disk)")
        return

    meta = _load_json(MODELS / 'pca_metadata.json') or {}
    threshold = meta.get('variance_threshold', PCA_VARIANCE_THRESHOLD)

    pca_model = joblib.load(str(model_path))

    apply_dark_theme()
    pca_analysis.plot_explained_variance(pca_model, threshold, output_dir)
    logger.info("  explained_variance.png")

    loadings_path = METRICS / 'pca_loadings.csv'
    if loadings_path.exists():
        import pandas as pd
        loadings = pd.read_csv(loadings_path, index_col=0)
        apply_dark_theme()
        pca_analysis.plot_component_loadings(loadings, output_dir)
        logger.info("  component_loadings.png")
    else:
        logger.info("  skip component_loadings.png (no pca_loadings.csv)")

    # The score matrix is not persisted, so the projection scatter cannot be
    # re-rendered faithfully without re-running generation + feature engineering.
    logger.info("  skip pca_projection_2d.png (per-consumer score matrix is not "
                "persisted; re-rendering would require re-running the pipeline)")


# --------------------------------------------------------------------------- #
# Clustering figures (re-rendered from the persisted K-sweep table)
# --------------------------------------------------------------------------- #
def generate_clustering_plots(output_dir):
    metrics_path = METRICS / 'clustering_metrics.csv'
    if not metrics_path.exists():
        logger.info("  skip clustering figures (no clustering_metrics.csv)")
        return

    import pandas as pd

    metrics = pd.read_csv(metrics_path)
    meta = _load_json(MODELS / 'analysis_metadata.json') or {}
    selected_k = meta.get('selected_k')
    if selected_k is None:
        selected = metrics[metrics.get('selected', False)]['K']
        selected_k = int(selected.iloc[0]) if len(selected) else None

    k_values = metrics['K'].tolist()

    apply_dark_theme()
    clustering.plot_elbow_curve(k_values, metrics['inertia'].tolist(),
                                selected_k, output_dir)
    logger.info("  elbow_curve.png")

    apply_dark_theme()
    clustering.plot_silhouette_scores(k_values, metrics['silhouette'].tolist(),
                                      selected_k, output_dir)
    logger.info("  silhouette_scores.png")

    apply_dark_theme()
    clustering.plot_k_selection_metrics(metrics, selected_k, output_dir)
    logger.info("  k_selection_metrics.png")

    logger.info("  skip cluster_visualization_2d.png (per-consumer score matrix is "
                "not persisted; re-rendering would require re-running the pipeline)")


# --------------------------------------------------------------------------- #
# Ablation figures (re-rendered from each arm's persisted tables)
# --------------------------------------------------------------------------- #
def _plot_explained_variance_from_table(pca_results, output_dir):
    """Faithful per-arm explained-variance figure from the persisted table.

    The per-arm PCA model is not persisted, only its numbers in pca_results.csv
    (component, eigenvalue, explained_variance_ratio, cumulative_variance). This
    draws the same two panels as pca_analysis.plot_explained_variance directly
    from those stored numbers - nothing is re-fitted or changed.
    """
    import numpy as np

    ratios = pca_results['explained_variance_ratio'].to_numpy()
    cumulative = np.cumsum(ratios)
    components = np.arange(1, len(ratios) + 1)

    fig, axes = plt.subplots(1, 2, figsize=(13, 5))

    axes[0].bar(components, ratios, color='steelblue')
    axes[0].set_xlabel('Principal component')
    axes[0].set_ylabel('Share of total variance')
    axes[0].set_title('Variance explained per component')

    axes[1].plot(components, cumulative, marker='o', color='darkred')
    axes[1].axhline(PCA_VARIANCE_THRESHOLD, color='green', linestyle='--',
                    label=f'{PCA_VARIANCE_THRESHOLD:.0%} target')
    axes[1].set_xlabel('Components retained')
    axes[1].set_ylabel('Cumulative share of variance')
    axes[1].set_title('Cumulative variance explained')
    axes[1].set_ylim(0, 1.02)
    axes[1].legend()

    fig.tight_layout()
    fig.savefig(Path(output_dir) / 'explained_variance.png', dpi=200,
                bbox_inches='tight')
    plt.close(fig)


def generate_all_ablation_plots():
    import pandas as pd

    for fs in FEATURE_SETS:
        arm_metrics = ABLATION / fs / 'metrics'
        out_dir = ABLATION_OUTDIR / fs / 'figures'
        out_dir.mkdir(parents=True, exist_ok=True)
        output_dir = str(out_dir)

        metrics_path = arm_metrics / 'clustering_metrics.csv'
        if not metrics_path.exists():
            logger.info(f"  {fs}: skip (no clustering_metrics.csv)")
            continue

        try:
            metrics = pd.read_csv(metrics_path)
            selected = metrics[metrics.get('selected', False)]['K']
            selected_k = int(selected.iloc[0]) if len(selected) else None
            k_values = metrics['K'].tolist()

            apply_dark_theme()
            clustering.plot_elbow_curve(k_values, metrics['inertia'].tolist(),
                                        selected_k, output_dir)
            apply_dark_theme()
            clustering.plot_silhouette_scores(k_values, metrics['silhouette'].tolist(),
                                              selected_k, output_dir)
            apply_dark_theme()
            clustering.plot_k_selection_metrics(metrics, selected_k, output_dir)
            logger.info(f"  {fs}: elbow_curve.png, silhouette_scores.png, "
                        f"k_selection_metrics.png (K={selected_k})")

            pca_path = arm_metrics / 'pca_results.csv'
            if pca_path.exists():
                apply_dark_theme()
                _plot_explained_variance_from_table(pd.read_csv(pca_path), output_dir)
                logger.info(f"  {fs}: explained_variance.png")

            loadings_path = arm_metrics / 'pca_loadings.csv'
            if loadings_path.exists():
                loadings = pd.read_csv(loadings_path, index_col=0)
                apply_dark_theme()
                pca_analysis.plot_component_loadings(loadings, output_dir)
                logger.info(f"  {fs}: component_loadings.png")

            logger.info(f"  {fs}: skip pca_projection_2d.png, "
                        f"cluster_visualization_2d.png (per-arm score matrix not "
                        f"persisted)")
        except Exception as exc:
            logger.warning(f"Ablation {fs} error: {exc}")


def main():
    logger.info("=" * 70)
    logger.info("DARK-MODE PLOT GENERATION FOR ALL PLOTS")
    logger.info("=" * 70)

    create_output_structure()

    logger.info("\n=== REGENERATING ALL PLOTS WITH DARK THEME ===\n")

    logger.info("Generating main figures plots...")
    generate_eda_plots(str(OUTDIR))
    generate_pca_plots(str(OUTDIR))
    generate_clustering_plots(str(OUTDIR))

    logger.info("\nGenerating ablation feature-set plots...")
    generate_all_ablation_plots()

    logger.info("\n=== ALL PLOTS REGENERATED WITH DARK THEME ===")

    new_path = ROOT / 'dark_mode_plots'

    logger.info("\n" + "=" * 70)
    logger.info("COMPLETE")
    logger.info(f"Output: {new_path}/")
    logger.info("Original plots untouched in outputs/figures/")
    logger.info("=" * 70)

    try:
        total_dark = sum(1 for _ in new_path.rglob('*.png'))
        logger.info(f"\nTotal dark-mode plots generated: {total_dark}")
    except Exception:
        pass


if __name__ == '__main__':
    main()
