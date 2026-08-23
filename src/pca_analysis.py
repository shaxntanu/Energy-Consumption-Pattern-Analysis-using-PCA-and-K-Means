"""
PCA Analysis Module

Standardizes the per-consumer feature matrix, fits PCA, and persists everything
needed to reproduce or reload the projection: the scaler, the PCA model, the
feature names in fitted order, the explained-variance table, the loading table
and a metadata file.

Terminology used consistently in this project:

- components_ from scikit-learn are eigenvector WEIGHTS. They are unit-length
  and do not say how strongly a feature relates to a component.
- LOADINGS are weight * sqrt(eigenvalue). Because the input is standardized,
  a loading equals the correlation between the original feature and the
  component score, so it is bounded by -1 and 1 and is what should be read when
  interpreting a component.

Only the loading table is used for interpretation.
"""

import os

# Non-interactive backend must be selected before pyplot is imported so that
# headless runs and the test suite do not try to open a window.
os.environ.setdefault('MPLBACKEND', 'Agg')

import json
import logging
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import joblib
import matplotlib

matplotlib.use('Agg', force=True)

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns
from sklearn.decomposition import PCA
from sklearn.preprocessing import StandardScaler

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

sns.set_style('whitegrid')

# Number of components shown in the loading heatmap. Beyond this the figure
# stops being readable and the CSV is the better reference.
MAX_PLOTTED_COMPONENTS = 5


def standardize_features(df: pd.DataFrame) -> Tuple[np.ndarray, StandardScaler]:
    """Standardize every column to zero mean and unit variance.

    PCA maximizes variance, so unstandardized features would be ranked by their
    units rather than their information content.

    Args:
        df: Numeric feature frame, identifiers already removed.

    Returns:
        Tuple of (scaled array, fitted scaler).
    """
    logger.info("Standardizing features")

    scaler = StandardScaler()
    scaled = scaler.fit_transform(df)

    logger.info(f"Features standardized. Shape: {scaled.shape}")
    return scaled, scaler


def component_count_criteria(explained_variance: np.ndarray,
                             explained_variance_ratio: np.ndarray,
                             variance_threshold: float) -> Dict[str, int]:
    """Compare the common rules for how many components to keep.

    Three rules are reported so the chosen number can be judged against the
    alternatives instead of being asserted:

    - variance_threshold: smallest number of components reaching the cumulative
      variance target. This is the rule the pipeline follows.
    - kaiser: components with an eigenvalue above 1. On standardized data an
      eigenvalue below 1 means the component explains less than a single
      original feature.
    - scree_elbow: the component after which the drop in explained variance
      stops being steep, found as the point furthest from the straight line
      joining the first and last component of the scree curve.

    Args:
        explained_variance: Eigenvalues, in descending order.
        explained_variance_ratio: Eigenvalues as fractions of total variance.
        variance_threshold: Cumulative variance target, for example 0.95.

    Returns:
        Mapping of rule name to component count.
    """
    cumulative = np.cumsum(explained_variance_ratio)
    by_threshold = int(np.argmax(cumulative >= variance_threshold) + 1)
    by_kaiser = int(max(1, np.sum(explained_variance > 1.0)))

    n = len(explained_variance_ratio)
    if n >= 3:
        x = np.arange(n, dtype=float)
        y = explained_variance_ratio
        # Perpendicular distance from each point to the first-to-last chord.
        dx, dy = x[-1] - x[0], y[-1] - y[0]
        norm = np.hypot(dx, dy)
        distance = np.abs(dy * (x - x[0]) - dx * (y - y[0])) / norm
        by_elbow = int(np.argmax(distance) + 1)
    else:
        by_elbow = n

    return {
        'variance_threshold': by_threshold,
        'kaiser': by_kaiser,
        'scree_elbow': by_elbow,
    }


def perform_pca(X: np.ndarray,
                variance_threshold: float = 0.95) -> Tuple[PCA, np.ndarray, int, Dict[str, int]]:
    """Fit PCA and retain components up to a cumulative variance target.

    The full spectrum is fitted first so that the alternative selection rules
    can be evaluated on the same eigenvalues.

    Args:
        X: Standardized feature matrix.
        variance_threshold: Cumulative variance target.

    Returns:
        Tuple of (fitted PCA, transformed data, component count, criteria dict).
    """
    if not 0.0 < variance_threshold <= 1.0:
        raise ValueError(f"variance_threshold must be in (0, 1], got {variance_threshold}")

    logger.info(f"Fitting PCA (cumulative variance target {variance_threshold:.0%})")

    full = PCA().fit(X)
    criteria = component_count_criteria(
        full.explained_variance_, full.explained_variance_ratio_, variance_threshold
    )
    n_components = criteria['variance_threshold']

    logger.info(f"Component count by rule: {criteria}")
    logger.info(f"Retaining {n_components} of {X.shape[1]} components")

    pca = PCA(n_components=n_components)
    X_pca = pca.fit_transform(X)

    cumulative = np.cumsum(pca.explained_variance_ratio_)[-1]
    logger.info(f"Cumulative explained variance retained: {cumulative:.4f}")

    return pca, X_pca, n_components, criteria


def loading_table(pca: PCA, feature_names: List[str]) -> pd.DataFrame:
    """Build the loading table for a fitted PCA.

    Args:
        pca: Fitted PCA.
        feature_names: Feature names in the order the PCA was fitted on.

    Returns:
        DataFrame indexed by feature, one column per retained component,
        holding the correlation between the feature and the component score.
    """
    loadings = pca.components_.T * np.sqrt(pca.explained_variance_)
    columns = [f'PC{i + 1}' for i in range(pca.n_components_)]
    return pd.DataFrame(loadings, index=feature_names, columns=columns)


def describe_component(loadings: pd.DataFrame, component: str, top_n: int = 5) -> str:
    """Summarize one component by its strongest loadings.

    This is deliberately mechanical. A component is described by which features
    load on it, not by a behavioural story invented on top of it.

    Args:
        loadings: Output of loading_table.
        component: Column name, for example 'PC1'.
        top_n: How many features to list.

    Returns:
        One-line description string.
    """
    ranked = loadings[component].reindex(loadings[component].abs().sort_values(ascending=False).index)
    parts = [f"{name} {value:+.2f}" for name, value in ranked.head(top_n).items()]
    return f"{component}: " + ", ".join(parts)


def plot_explained_variance(pca: PCA,
                            variance_threshold: float,
                            output_dir: str = 'outputs/figures') -> None:
    """Plot the scree curve and the cumulative variance curve side by side."""
    logger.info("Plotting explained variance")

    ratios = pca.explained_variance_ratio_
    cumulative = np.cumsum(ratios)
    components = np.arange(1, len(ratios) + 1)

    fig, axes = plt.subplots(1, 2, figsize=(13, 5))

    axes[0].bar(components, ratios, color='steelblue')
    axes[0].set_xlabel('Principal component')
    axes[0].set_ylabel('Share of total variance')
    axes[0].set_title('Variance explained per component')

    axes[1].plot(components, cumulative, marker='o', color='darkred')
    axes[1].axhline(variance_threshold, color='green', linestyle='--',
                    label=f'{variance_threshold:.0%} target')
    axes[1].set_xlabel('Components retained')
    axes[1].set_ylabel('Cumulative share of variance')
    axes[1].set_title('Cumulative variance explained')
    axes[1].set_ylim(0, 1.02)
    axes[1].legend()

    fig.tight_layout()
    path = Path(output_dir) / 'explained_variance.png'
    fig.savefig(path, dpi=200, bbox_inches='tight')
    plt.close(fig)
    logger.info(f"Saved explained variance plot to {path}")


def plot_pca_projection(X_pca: np.ndarray,
                        pca: PCA,
                        output_dir: str = 'outputs/figures') -> None:
    """Scatter the first two components, labelled with their variance shares."""
    if X_pca.shape[1] < 2:
        logger.warning("Fewer than two components retained, skipping 2D projection")
        return

    logger.info("Plotting PCA projection")

    ratios = pca.explained_variance_ratio_
    fig, ax = plt.subplots(figsize=(7.5, 6))
    ax.scatter(X_pca[:, 0], X_pca[:, 1], alpha=0.6, s=32,
               color='steelblue', edgecolors='white', linewidth=0.4)
    ax.set_xlabel(f'PC1 ({ratios[0]:.1%} of variance)')
    ax.set_ylabel(f'PC2 ({ratios[1]:.1%} of variance)')
    ax.set_title('Consumers projected onto the first two components')

    fig.tight_layout()
    path = Path(output_dir) / 'pca_projection_2d.png'
    fig.savefig(path, dpi=200, bbox_inches='tight')
    plt.close(fig)
    logger.info(f"Saved 2D PCA projection to {path}")


def plot_component_loadings(loadings: pd.DataFrame,
                            output_dir: str = 'outputs/figures') -> None:
    """Heatmap of feature loadings on the leading components.

    A heatmap is used rather than one bar chart per component because the
    feature set is large enough that separate panels become unreadable.
    """
    logger.info("Plotting component loadings")

    columns = loadings.columns[:MAX_PLOTTED_COMPONENTS]
    subset = loadings[columns]

    height = max(5.0, 0.24 * len(subset))
    fig, ax = plt.subplots(figsize=(1.6 * len(columns) + 4.0, height))
    sns.heatmap(subset, cmap='RdBu_r', center=0, vmin=-1, vmax=1,
                annot=len(subset) <= 24, fmt='.2f',
                cbar_kws={'label': 'Loading (correlation with component)'}, ax=ax)
    ax.set_title('Feature loadings on the leading principal components')
    ax.set_xlabel('')
    ax.set_ylabel('')

    fig.tight_layout()
    path = Path(output_dir) / 'component_loadings.png'
    fig.savefig(path, dpi=200, bbox_inches='tight')
    plt.close(fig)
    logger.info(f"Saved component loadings plot to {path}")


def save_models(scaler: StandardScaler, pca: PCA, model_dir: str = 'models') -> None:
    """Persist the fitted scaler and PCA model."""
    logger.info("Saving PCA models")

    Path(model_dir).mkdir(parents=True, exist_ok=True)
    joblib.dump(scaler, Path(model_dir) / 'scaler.pkl')
    joblib.dump(pca, Path(model_dir) / 'pca_model.pkl')

    logger.info(f"Models saved to {model_dir}")


def run_pca_pipeline(df: pd.DataFrame,
                     variance_threshold: float = 0.95,
                     output_dir: str = 'outputs/figures',
                     model_dir: str = 'models',
                     metrics_dir: Optional[str] = None) -> Tuple[np.ndarray, PCA, StandardScaler, int]:
    """Standardize, fit PCA, write figures, tables and models.

    Args:
        df: Per-consumer feature frame. consumer_id is dropped if present.
        variance_threshold: Cumulative variance target.
        output_dir: Directory for figures.
        model_dir: Directory for the scaler, PCA model and metadata.
        metrics_dir: Directory for the CSV tables. Defaults to a sibling
            'metrics' directory next to output_dir.

    Returns:
        Tuple of (transformed data, fitted PCA, fitted scaler, component count).
    """
    logger.info("Starting PCA pipeline")

    figures_path = Path(output_dir)
    models_path = Path(model_dir)
    metrics_path = Path(metrics_dir) if metrics_dir else figures_path.parent / 'metrics'
    for path in (figures_path, models_path, metrics_path):
        path.mkdir(parents=True, exist_ok=True)

    feature_df = (df.drop(columns=['consumer_id'], errors='ignore')
                    .select_dtypes(include=[np.number]))
    if feature_df.shape[1] == 0:
        raise ValueError("No numeric features available for PCA after dropping identifiers")
    if feature_df.isnull().any().any():
        raise ValueError("Feature matrix contains missing values; fix feature engineering first")

    feature_names = feature_df.columns.tolist()

    X_scaled, scaler = standardize_features(feature_df)
    pca, X_pca, n_components, criteria = perform_pca(X_scaled, variance_threshold)
    loadings = loading_table(pca, feature_names)

    plot_explained_variance(pca, variance_threshold, str(figures_path))
    plot_pca_projection(X_pca, pca, str(figures_path))
    plot_component_loadings(loadings, str(figures_path))

    save_models(scaler, pca, str(models_path))
    (models_path / 'feature_names.txt').write_text('\n'.join(feature_names), encoding='utf-8')

    variance_table = pd.DataFrame({
        'component': np.arange(1, n_components + 1),
        'eigenvalue': pca.explained_variance_,
        'explained_variance_ratio': pca.explained_variance_ratio_,
        'cumulative_variance': np.cumsum(pca.explained_variance_ratio_),
    })
    variance_table.to_csv(metrics_path / 'pca_results.csv', index=False)
    loadings.to_csv(metrics_path / 'pca_loadings.csv', index_label='feature')

    metadata = {
        'n_input_features': len(feature_names),
        'feature_names': feature_names,
        'variance_threshold': variance_threshold,
        'n_components_retained': int(n_components),
        'cumulative_variance_retained': float(np.cumsum(pca.explained_variance_ratio_)[-1]),
        'component_count_by_criterion': criteria,
        'component_descriptions': [
            describe_component(loadings, column)
            for column in loadings.columns[:MAX_PLOTTED_COMPONENTS]
        ],
    }
    (models_path / 'pca_metadata.json').write_text(
        json.dumps(metadata, indent=2), encoding='utf-8'
    )

    for line in metadata['component_descriptions']:
        logger.info(f"  {line}")

    logger.info("PCA pipeline completed")
    return X_pca, pca, scaler, n_components


if __name__ == "__main__":
    from project_paths import anchor_to_project_root

    anchor_to_project_root()

    from data_loader import generate_synthetic_data
    from feature_engineering import engineer_all_features, select_features
    from preprocessing import preprocess_pipeline

    raw = generate_synthetic_data(n_consumers=200, n_days=30, hourly_records=True)
    preprocessed = preprocess_pipeline(raw.drop(columns=['archetype']))
    features = select_features(
        engineer_all_features(preprocessed, feature_set='behavioral'),
        feature_group='behavioral',
    )

    X_pca, pca, scaler, n_components = run_pca_pipeline(features)

    print(f"\nComponents retained: {n_components} of {features.shape[1] - 1} features")
    print(f"Cumulative variance: {np.cumsum(pca.explained_variance_ratio_)[-1]:.4f}")
    print("\nLeading components:")
    table = loading_table(pca, [c for c in features.columns if c != 'consumer_id'])
    for column in table.columns[:3]:
        print("  " + describe_component(table, column))
