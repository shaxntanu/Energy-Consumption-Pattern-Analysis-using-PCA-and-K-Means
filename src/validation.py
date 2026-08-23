"""
Validation Module

Checks whether the analysis recovered the structure the generator put in.

This is supervised validation, and it is only possible because the data is
synthetic: the generator recorded which archetype it drew each consumer from. The
archetype column is dropped before preprocessing, so it never reaches the
scaler, PCA or K-Means. Comparing it with the recovered clusters afterwards is
therefore an independent test rather than circular reasoning.

On a real dataset none of this is available. Internal indices such as silhouette
would be all there is, which is exactly why it is worth measuring here how well
those indices agree with the truth.

Two measures are reported:

- Adjusted Rand Index: agreement between two partitions, corrected so that
  random agreement scores 0. 1 means identical up to relabelling.
- Normalized Mutual Information: how much knowing the cluster tells you about
  the archetype, on a 0 to 1 scale.
"""

import os

os.environ.setdefault('MPLBACKEND', 'Agg')

import logging
from pathlib import Path
from typing import List, Optional, Sequence

import matplotlib

matplotlib.use('Agg', force=True)

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns
from sklearn.cluster import KMeans
from sklearn.metrics import (
    adjusted_rand_score,
    normalized_mutual_info_score,
    silhouette_score,
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

sns.set_style('whitegrid')

N_INIT = 10


def archetype_recovery(X: np.ndarray,
                       truth: Sequence,
                       k_values: Optional[List[int]] = None,
                       random_state: int = 42) -> pd.DataFrame:
    """Measure how well K-Means recovers the archetypes, for every candidate K.

    Args:
        X: PCA scores, one row per consumer.
        truth: Archetype label per consumer, in the same order as X.
        k_values: Candidate K values. Defaults to 2 through 10.
        random_state: Seed for each fit, matching the main pipeline.

    Returns:
        DataFrame with one row per K holding ari, nmi, silhouette, the number of
        distinct archetypes, and the cluster sizes.
    """
    truth = np.asarray(truth)
    if len(truth) != len(X):
        raise ValueError(f"Got {len(truth)} truth labels for {len(X)} rows; they must match")

    k_values = k_values or list(range(2, 11))
    n_true = int(len(np.unique(truth)))

    logger.info(f"Measuring archetype recovery over K={k_values} against {n_true} archetypes")

    rows = []
    for k in k_values:
        labels = KMeans(n_clusters=k, random_state=random_state, n_init=N_INIT).fit_predict(X)
        rows.append({
            'K': int(k),
            'ari': float(adjusted_rand_score(truth, labels)),
            'nmi': float(normalized_mutual_info_score(truth, labels)),
            'silhouette': float(silhouette_score(X, labels)),
            'n_true_archetypes': n_true,
            'cluster_sizes': str(np.bincount(labels).tolist()),
        })
        logger.info(f"  K={k}: ARI={rows[-1]['ari']:.4f} NMI={rows[-1]['nmi']:.4f}")

    return pd.DataFrame(rows)


def recovery_crosstab(labels: Sequence, truth: Sequence) -> pd.DataFrame:
    """Cross-tabulate recovered clusters against the true archetypes.

    Reading the table down a row shows whether one archetype was split across
    clusters; reading across a column shows whether one cluster merged several
    archetypes.

    Args:
        labels: Cluster label per consumer.
        truth: Archetype label per consumer, in the same order.

    Returns:
        Counts with archetypes as rows and clusters as columns.
    """
    return pd.crosstab(
        pd.Series(np.asarray(truth), name='archetype'),
        pd.Series(np.asarray(labels), name='cluster'),
    )


def plot_recovery_by_k(recovery: pd.DataFrame,
                       selected_k: Optional[int] = None,
                       output_dir: str = 'outputs/figures') -> None:
    """Plot recovery against the archetypes next to the internal silhouette score.

    Putting the two curves on one figure is the point of the figure: it shows
    whether the index used to choose K agrees with the ground truth.
    """
    logger.info("Plotting archetype recovery by K")

    fig, ax = plt.subplots(figsize=(9, 5.5))
    ax.plot(recovery['K'], recovery['ari'], marker='o', color='darkred',
            label='Adjusted Rand Index against archetypes')
    ax.plot(recovery['K'], recovery['nmi'], marker='s', color='indianred',
            linestyle='--', label='Normalized Mutual Information')
    ax.plot(recovery['K'], recovery['silhouette'], marker='^', color='steelblue',
            label='Silhouette (internal, no ground truth)')

    n_true = int(recovery['n_true_archetypes'].iloc[0])
    ax.axvline(n_true, color='green', linestyle=':', label=f'Archetypes in the generator: {n_true}')
    if selected_k is not None:
        ax.axvline(selected_k, color='black', linestyle='--',
                   label=f'K selected by the pipeline: {selected_k}')

    ax.set_xlabel('Number of clusters (K)')
    ax.set_ylabel('Score')
    ax.set_xticks(recovery['K'])
    ax.set_ylim(0, 1.02)
    ax.set_title('What the clusters recover, against what the internal index prefers')
    ax.legend(fontsize=9)

    fig.tight_layout()
    path = Path(output_dir) / 'archetype_recovery.png'
    path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(path, dpi=200, bbox_inches='tight')
    plt.close(fig)
    logger.info(f"Saved archetype recovery plot to {path}")


def plot_recovery_crosstab(crosstab: pd.DataFrame,
                           output_dir: str = 'outputs/figures') -> None:
    """Heatmap of the cluster against archetype counts."""
    logger.info("Plotting recovery crosstab")

    fig, ax = plt.subplots(figsize=(1.4 * len(crosstab.columns) + 3.5,
                                    0.7 * len(crosstab) + 2.5))
    sns.heatmap(crosstab, annot=True, fmt='d', cmap='Blues', cbar=False, ax=ax)
    ax.set_title('Consumers by true archetype and recovered cluster')
    ax.set_xlabel('Recovered cluster')
    ax.set_ylabel('True archetype (hidden from the model)')

    fig.tight_layout()
    path = Path(output_dir) / 'archetype_crosstab.png'
    path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(path, dpi=200, bbox_inches='tight')
    plt.close(fig)
    logger.info(f"Saved recovery crosstab to {path}")


def describe_recovery(recovery: pd.DataFrame,
                      crosstab: pd.DataFrame,
                      selected_k: int) -> str:
    """Write an honest paragraph about what the recovery numbers show.

    The text is generated from the numbers, including the case where the pipeline
    picked a K that does not match the number of archetypes. That case is stated
    plainly rather than smoothed over.

    Args:
        recovery: Output of archetype_recovery.
        crosstab: Output of recovery_crosstab at the selected K.
        selected_k: K the pipeline chose.

    Returns:
        Markdown paragraphs.
    """
    n_true = int(recovery['n_true_archetypes'].iloc[0])
    at_selected = recovery.loc[recovery['K'] == selected_k]
    ari_selected = float(at_selected['ari'].iloc[0])

    best_row = recovery.loc[recovery['ari'].idxmax()]
    best_k = int(best_row['K'])
    best_ari = float(best_row['ari'])

    sil_row = recovery.loc[recovery['silhouette'].idxmax()]
    sil_k = int(sil_row['K'])

    lines = [
        f"The generator drew consumers from {n_true} archetypes. The pipeline selected "
        f"K={selected_k} using internal indices only, and at that K the Adjusted Rand Index "
        f"against the archetypes is {ari_selected:.4f}.",
        "",
        f"Recovery is highest at K={best_k} (ARI {best_ari:.4f}), while the silhouette score "
        f"is highest at K={sil_k}.",
        "",
    ]

    if best_k != selected_k:
        merged = []
        for archetype in crosstab.index:
            row = crosstab.loc[archetype]
            dominant = row.idxmax()
            share = row.max() / row.sum()
            if share < 0.75:
                merged.append(f"{archetype} (only {share:.0%} in its largest cluster)")
            else:
                merged.append(f"{archetype} -> cluster {dominant} ({share:.0%})")

        lines += [
            f"The two disagree, and that disagreement is the result rather than a problem to "
            f"hide. Internal indices reward compact, well-separated clusters. They have no way "
            f"to know how many groups the data was built from, so when two archetypes differ "
            f"along a direction that occupies a small part of the feature space, merging them "
            f"raises the silhouette score even though it loses a real distinction.",
            "",
            "At the selected K each archetype falls out as follows:",
            "",
        ]
        lines += [f"- {entry}" for entry in merged]
        lines += [
            "",
            f"The practical reading: on this dataset the internal indices under-count the "
            f"groups. On a real dataset there would be no way to detect that, which is a "
            f"limit of unsupervised clustering and not of this implementation.",
            "",
        ]
    else:
        lines += [
            f"The pipeline's choice of K matches the number of archetypes, so on this dataset "
            f"the internal indices agree with the ground truth. That agreement is not "
            f"guaranteed in general and should not be assumed for other data.",
            "",
        ]

    return "\n".join(lines)


def run_validation(X_pca: np.ndarray,
                   labels: np.ndarray,
                   truth: Sequence,
                   selected_k: int,
                   k_values: Optional[List[int]] = None,
                   random_state: int = 42,
                   output_dir: str = 'outputs') -> pd.DataFrame:
    """Run the full recovery check and write figures, tables and a report.

    Args:
        X_pca: PCA scores.
        labels: Cluster labels at the selected K.
        truth: Archetype label per consumer, in the same order as X_pca.
        selected_k: K the pipeline chose.
        k_values: Candidate K values to evaluate.
        random_state: Seed for each fit.
        output_dir: Root output directory.

    Returns:
        The recovery table.
    """
    logger.info("Starting validation against the hidden archetypes")

    figures = Path(output_dir) / 'figures'
    metrics = Path(output_dir) / 'metrics'
    reports = Path(output_dir) / 'reports'
    for path in (figures, metrics, reports):
        path.mkdir(parents=True, exist_ok=True)

    recovery = archetype_recovery(X_pca, truth, k_values, random_state)
    crosstab = recovery_crosstab(labels, truth)

    recovery.to_csv(metrics / 'archetype_recovery.csv', index=False)
    crosstab.to_csv(metrics / 'archetype_crosstab.csv')

    plot_recovery_by_k(recovery, selected_k, str(figures))
    plot_recovery_crosstab(crosstab, str(figures))

    report = [
        "# Validation Against the Hidden Archetypes",
        "",
        "THIS IS SYNTHETIC DATA. The check below is possible only because the generator",
        "recorded which archetype each consumer was drawn from. That column is dropped",
        "before preprocessing and never reaches the scaler, PCA or K-Means.",
        "",
        "## What the numbers say",
        "",
        describe_recovery(recovery, crosstab, selected_k),
        "## Recovery by K",
        "",
        "| K | Adjusted Rand Index | Normalized Mutual Information | Silhouette |",
        "| - | ------------------- | ----------------------------- | ---------- |",
    ]
    for _, row in recovery.iterrows():
        marker = " (selected)" if int(row['K']) == selected_k else ""
        report.append(
            f"| {int(row['K'])}{marker} | {row['ari']:.4f} | {row['nmi']:.4f} | "
            f"{row['silhouette']:.4f} |"
        )

    report += [
        "",
        "## Cluster against archetype at the selected K",
        "",
        "```",
        crosstab.to_string(),
        "```",
        "",
    ]

    (reports / 'validation_report.md').write_text("\n".join(report), encoding='utf-8')
    logger.info(f"Validation report saved to {reports / 'validation_report.md'}")

    return recovery


if __name__ == "__main__":
    from project_paths import anchor_to_project_root

    anchor_to_project_root()

    from clustering import run_clustering_pipeline
    from data_loader import generate_synthetic_data
    from feature_engineering import engineer_all_features, select_features
    from pca_analysis import run_pca_pipeline
    from preprocessing import preprocess_pipeline

    raw = generate_synthetic_data(n_consumers=200, n_days=30, hourly_records=True)
    truth_by_consumer = raw.groupby('consumer_id')['archetype'].first()

    preprocessed = preprocess_pipeline(raw.drop(columns=['archetype']))
    behavioral = select_features(
        engineer_all_features(preprocessed, feature_set='behavioral'),
        feature_group='behavioral',
    )
    order = behavioral['consumer_id'].tolist()

    X_pca, pca, scaler, n_components = run_pca_pipeline(behavioral)
    clustering = run_clustering_pipeline(X_pca, test_stability=False)

    table = run_validation(
        X_pca, clustering.labels,
        truth_by_consumer.reindex(order).to_numpy(),
        clustering.optimal_k,
        k_values=clustering.k_values,
    )
    print("\n" + table.to_string(index=False))
