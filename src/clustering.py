"""
Clustering Module

Runs K-Means over a range of K on the PCA scores, then selects K from evidence
rather than from a preference for a particular number.

The selection rule is fixed in advance and applied without looking at the hidden
archetype labels:

1. Score every candidate K on silhouette, Calinski-Harabasz, Davies-Bouldin,
   inertia, and stability across random restarts.
2. Discard any K whose smallest cluster holds less than a minimum share of
   consumers. A solution that isolates a handful of outliers is not a
   segmentation.
3. Discard any K whose mean pairwise Adjusted Rand Index across restarts falls
   below a minimum. An unstable partition is not a finding.
4. Combine silhouette, Calinski-Harabasz and Davies-Bouldin into one score by
   min-max normalizing each across the surviving candidates.
5. Among candidates within a tolerance of the best score, take the smallest K.
   When two solutions are statistically indistinguishable the simpler one is
   preferred.

If every candidate fails a filter, the filter is relaxed and the fact is logged,
so the pipeline reports a weak result instead of silently inventing one.
"""

import os

os.environ.setdefault('MPLBACKEND', 'Agg')

import json
import logging
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional, Sequence, Tuple

import joblib
import matplotlib

matplotlib.use('Agg', force=True)

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns
from scipy.optimize import linear_sum_assignment
from sklearn.cluster import KMeans
from sklearn.metrics import (
    adjusted_rand_score,
    calinski_harabasz_score,
    davies_bouldin_score,
    silhouette_score,
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

sns.set_style('whitegrid')

N_INIT = 10
DEFAULT_STABILITY_RUNS = 10
MIN_CLUSTER_SHARE = 0.05
MIN_STABILITY_ARI = 0.60
SCORE_TOLERANCE = 0.05


@dataclass
class ClusteringResults:
    """Everything the clustering step produced, keyed by K where applicable."""

    model: KMeans
    labels: np.ndarray
    optimal_k: int
    k_values: List[int]
    inertia_by_k: Dict[int, float]
    silhouette_by_k: Dict[int, float]
    ch_by_k: Dict[int, float]
    db_by_k: Dict[int, float]
    stability_by_k: Dict[int, dict]
    selection_trace: dict = field(default_factory=dict)

    @property
    def stability(self) -> Optional[dict]:
        """Stability record for the selected K, if stability was measured."""
        return self.stability_by_k.get(self.optimal_k)

    def metrics_frame(self) -> pd.DataFrame:
        """Return one row per candidate K with every metric measured."""
        rows = []
        for k in self.k_values:
            stability = self.stability_by_k.get(k, {})
            rows.append({
                'K': k,
                'inertia': self.inertia_by_k[k],
                'silhouette': self.silhouette_by_k[k],
                'calinski_harabasz': self.ch_by_k[k],
                'davies_bouldin': self.db_by_k[k],
                'stability_mean_ari': stability.get('mean_ari'),
                'stability_std_ari': stability.get('std_ari'),
                'assignment_agreement': stability.get('mean_agreement'),
                'min_cluster_share': stability.get('min_cluster_share'),
                'selected': k == self.optimal_k,
            })
        return pd.DataFrame(rows)


def _label_agreement(labels_a: np.ndarray, labels_b: np.ndarray) -> float:
    """Share of consumers given the same cluster after optimally matching labels.

    Cluster numbers are arbitrary, so two identical partitions can use different
    integers. The Hungarian algorithm finds the best one-to-one matching before
    counting agreement.

    Args:
        labels_a: Labels from one run.
        labels_b: Labels from another run over the same rows.

    Returns:
        Agreement between 0 and 1.
    """
    classes_a = np.unique(labels_a)
    classes_b = np.unique(labels_b)
    table = np.zeros((len(classes_a), len(classes_b)), dtype=int)
    for i, a in enumerate(classes_a):
        for j, b in enumerate(classes_b):
            table[i, j] = np.sum((labels_a == a) & (labels_b == b))
    rows, cols = linear_sum_assignment(-table)
    return float(table[rows, cols].sum() / len(labels_a))


def measure_cluster_stability(X: np.ndarray,
                              n_clusters: int,
                              n_runs: int = DEFAULT_STABILITY_RUNS,
                              random_state: int = 42) -> dict:
    """Refit K-Means from several seeds and measure how much the partition moves.

    Named "measure_" rather than "test_" on purpose: pytest collects any
    module-level function whose name starts with test_, and this is library code,
    not a test case.

    Args:
        X: PCA scores.
        n_clusters: K to examine.
        n_runs: Number of independent restarts.
        random_state: Base seed. Run i uses random_state + i.

    Returns:
        Dictionary with mean and spread of pairwise ARI, mean assignment
        agreement, inertia spread, and the smallest cluster share observed.
    """
    logger.info(f"Measuring stability for K={n_clusters} over {n_runs} restarts")

    all_labels = []
    inertias = []
    min_shares = []

    for run in range(n_runs):
        kmeans = KMeans(n_clusters=n_clusters, random_state=random_state + run, n_init=N_INIT)
        labels = kmeans.fit_predict(X)
        all_labels.append(labels)
        inertias.append(kmeans.inertia_)
        min_shares.append(np.bincount(labels, minlength=n_clusters).min() / len(labels))

    ari_scores = []
    agreements = []
    for i in range(n_runs):
        for j in range(i + 1, n_runs):
            ari_scores.append(adjusted_rand_score(all_labels[i], all_labels[j]))
            agreements.append(_label_agreement(all_labels[i], all_labels[j]))

    result = {
        'n_clusters': int(n_clusters),
        'n_runs': int(n_runs),
        'mean_ari': float(np.mean(ari_scores)),
        'std_ari': float(np.std(ari_scores)),
        'min_ari': float(np.min(ari_scores)),
        'mean_agreement': float(np.mean(agreements)),
        'mean_inertia': float(np.mean(inertias)),
        'std_inertia': float(np.std(inertias)),
        'min_cluster_share': float(np.min(min_shares)),
    }

    logger.info(
        f"  K={n_clusters}: ARI {result['mean_ari']:.4f} +/- {result['std_ari']:.4f}, "
        f"agreement {result['mean_agreement']:.3f}, "
        f"smallest cluster {result['min_cluster_share']:.1%}"
    )
    return result


def find_optimal_k(X: np.ndarray,
                   k_range: Tuple[int, int] = (2, 11),
                   random_state: int = 42,
                   stability_runs: int = DEFAULT_STABILITY_RUNS) -> Tuple[List[int], Dict[int, float], Dict[int, float], Dict[int, float], Dict[int, float], Dict[int, dict]]:
    """Evaluate every candidate K on quality and stability.

    Args:
        X: PCA scores.
        k_range: Half-open (min, max) range of K, matching the range built-in.
        random_state: Seed for the reference fit at each K.
        stability_runs: Restarts per K. Zero skips the stability measurement.

    Returns:
        Tuple of (k_values, inertia, silhouette, ch, db, stability), where every
        element after the first is a dictionary keyed by K.
    """
    k_values = list(range(k_range[0], k_range[1]))
    if not k_values:
        raise ValueError(f"Empty k_range: {k_range}")
    if min(k_values) < 2:
        raise ValueError("K must be at least 2 for the clustering metrics to be defined")
    if max(k_values) >= len(X):
        raise ValueError(f"k_range {k_range} exceeds the number of samples ({len(X)})")

    logger.info(f"Evaluating K in {k_values}")

    inertia, silhouette, ch, db, stability = {}, {}, {}, {}, {}

    for k in k_values:
        kmeans = KMeans(n_clusters=k, random_state=random_state, n_init=N_INIT)
        labels = kmeans.fit_predict(X)

        inertia[k] = float(kmeans.inertia_)
        silhouette[k] = float(silhouette_score(X, labels))
        ch[k] = float(calinski_harabasz_score(X, labels))
        db[k] = float(davies_bouldin_score(X, labels))

        logger.info(
            f"K={k}: inertia={inertia[k]:.1f} silhouette={silhouette[k]:.4f} "
            f"CH={ch[k]:.1f} DB={db[k]:.4f} sizes={np.bincount(labels).tolist()}"
        )

        if stability_runs > 0:
            stability[k] = measure_cluster_stability(X, k, stability_runs, random_state)
        else:
            stability[k] = {
                'n_clusters': int(k),
                'min_cluster_share': float(np.bincount(labels).min() / len(labels)),
            }

    return k_values, inertia, silhouette, ch, db, stability


def _min_max(values: Sequence[float]) -> np.ndarray:
    """Scale a sequence to [0, 1]. A constant sequence maps to all ones."""
    array = np.asarray(values, dtype=float)
    spread = array.max() - array.min()
    if spread <= 0:
        return np.ones_like(array)
    return (array - array.min()) / spread


def curve_knee(x: Sequence[float], y: Sequence[float]) -> Optional[float]:
    """Locate the elbow of a monotone curve as the point furthest from its chord.

    Args:
        x: Monotone x values, for example K.
        y: Corresponding y values, for example inertia.

    Returns:
        The x value at the knee, or None if the curve is too short.
    """
    x = np.asarray(x, dtype=float)
    y = np.asarray(y, dtype=float)
    if len(x) < 3:
        return None

    xs = _min_max(x)
    ys = _min_max(y)
    dx, dy = xs[-1] - xs[0], ys[-1] - ys[0]
    norm = np.hypot(dx, dy)
    if norm == 0:
        return None
    distance = np.abs(dy * (xs - xs[0]) - dx * (ys - ys[0])) / norm
    return float(x[int(np.argmax(distance))])


def select_optimal_k(k_values: List[int],
                     inertia_by_k: Dict[int, float],
                     silhouette_by_k: Dict[int, float],
                     ch_by_k: Dict[int, float],
                     db_by_k: Dict[int, float],
                     stability_by_k: Optional[Dict[int, dict]] = None,
                     min_cluster_share: float = MIN_CLUSTER_SHARE,
                     min_stability_ari: float = MIN_STABILITY_ARI,
                     tolerance: float = SCORE_TOLERANCE) -> Tuple[int, dict]:
    """Choose K from quality, stability, cluster balance and parsimony.

    See the module docstring for the rule. Ground truth is never consulted.

    Args:
        k_values: Candidate K values.
        inertia_by_k: Inertia per K. Reported and used for the elbow, not for
            ranking, because inertia always falls as K rises.
        silhouette_by_k: Silhouette per K, higher is better.
        ch_by_k: Calinski-Harabasz per K, higher is better.
        db_by_k: Davies-Bouldin per K, lower is better.
        stability_by_k: Stability record per K, or None to skip both filters.
        min_cluster_share: Smallest acceptable share of consumers in a cluster.
        min_stability_ari: Smallest acceptable mean pairwise ARI.
        tolerance: How close to the best composite score a smaller K must be to
            win on parsimony, on the 0 to 1 composite scale.

    Returns:
        Tuple of (selected K, trace dictionary explaining the decision).
    """
    logger.info("Selecting K from quality, stability and parsimony")

    stability_by_k = stability_by_k or {}
    trace: dict = {
        'candidates': list(k_values),
        'rules': {
            'min_cluster_share': min_cluster_share,
            'min_stability_ari': min_stability_ari,
            'tolerance': tolerance,
        },
        'relaxed_filters': [],
    }

    candidates = list(k_values)

    balanced = [k for k in candidates
                if stability_by_k.get(k, {}).get('min_cluster_share', 1.0) >= min_cluster_share]
    if balanced:
        if len(balanced) < len(candidates):
            logger.info(f"Rejected for tiny clusters: {sorted(set(candidates) - set(balanced))}")
        candidates = balanced
    else:
        trace['relaxed_filters'].append('min_cluster_share')
        logger.warning("Every K produced a cluster below the minimum share; filter relaxed")
    trace['after_balance_filter'] = list(candidates)

    has_stability = any('mean_ari' in stability_by_k.get(k, {}) for k in candidates)
    if has_stability:
        stable = [k for k in candidates
                  if stability_by_k.get(k, {}).get('mean_ari', 0.0) >= min_stability_ari]
        if stable:
            if len(stable) < len(candidates):
                logger.info(f"Rejected for instability: {sorted(set(candidates) - set(stable))}")
            candidates = stable
        else:
            trace['relaxed_filters'].append('min_stability_ari')
            logger.warning("No K met the stability threshold; filter relaxed and result is weak")
    trace['after_stability_filter'] = list(candidates)

    composite = (
        _min_max([silhouette_by_k[k] for k in candidates])
        + _min_max([ch_by_k[k] for k in candidates])
        + _min_max([-db_by_k[k] for k in candidates])
    ) / 3.0
    scores = {k: float(score) for k, score in zip(candidates, composite)}
    trace['composite_scores'] = scores

    best_score = max(scores.values())
    within_tolerance = sorted(k for k, score in scores.items() if score >= best_score - tolerance)
    optimal_k = within_tolerance[0]

    trace['best_score'] = best_score
    trace['best_k_by_score'] = int(max(scores, key=lambda k: (scores[k], -k)))
    trace['within_tolerance'] = within_tolerance
    trace['selected_k'] = int(optimal_k)
    trace['elbow_k'] = curve_knee(k_values, [inertia_by_k[k] for k in k_values])

    logger.info(f"Composite scores: { {k: round(v, 4) for k, v in scores.items()} }")
    logger.info(f"Best score at K={trace['best_k_by_score']}, within tolerance: {within_tolerance}")
    logger.info(f"Selected K={optimal_k} (inertia elbow suggests K={trace['elbow_k']})")

    return int(optimal_k), trace


def perform_kmeans(X: np.ndarray, n_clusters: int, random_state: int = 42) -> Tuple[KMeans, np.ndarray]:
    """Fit the final K-Means model.

    Args:
        X: PCA scores.
        n_clusters: Chosen K.
        random_state: Seed.

    Returns:
        Tuple of (fitted model, labels).
    """
    logger.info(f"Fitting final K-Means with K={n_clusters}")

    kmeans = KMeans(n_clusters=n_clusters, random_state=random_state, n_init=N_INIT)
    labels = kmeans.fit_predict(X)

    logger.info(f"Cluster sizes: {np.bincount(labels).tolist()}")
    return kmeans, labels


def plot_elbow_curve(k_values: List[int],
                     inertia_values: List[float],
                     selected_k: Optional[int] = None,
                     output_dir: str = 'outputs/figures') -> None:
    """Plot inertia against K, marking the elbow and the selected K."""
    logger.info("Plotting elbow curve")

    fig, ax = plt.subplots(figsize=(8, 5))
    ax.plot(k_values, inertia_values, marker='o', color='steelblue')

    knee = curve_knee(k_values, inertia_values)
    if knee is not None:
        ax.axvline(knee, color='grey', linestyle=':', label=f'Elbow at K={int(knee)}')
    if selected_k is not None:
        ax.axvline(selected_k, color='darkred', linestyle='--', label=f'Selected K={selected_k}')

    ax.set_xlabel('Number of clusters (K)')
    ax.set_ylabel('Inertia (within-cluster sum of squares)')
    ax.set_title('Inertia falls with every extra cluster, so it cannot pick K alone')
    ax.set_xticks(k_values)
    ax.legend()

    fig.tight_layout()
    path = Path(output_dir) / 'elbow_curve.png'
    fig.savefig(path, dpi=200, bbox_inches='tight')
    plt.close(fig)
    logger.info(f"Saved elbow curve to {path}")


def plot_silhouette_scores(k_values: List[int],
                           silhouette_values: List[float],
                           selected_k: Optional[int] = None,
                           output_dir: str = 'outputs/figures') -> None:
    """Plot silhouette against K, marking the selected K."""
    logger.info("Plotting silhouette scores")

    fig, ax = plt.subplots(figsize=(8, 5))
    ax.plot(k_values, silhouette_values, marker='o', color='darkred')
    if selected_k is not None:
        ax.axvline(selected_k, color='darkred', linestyle='--', label=f'Selected K={selected_k}')
        ax.legend()

    ax.set_xlabel('Number of clusters (K)')
    ax.set_ylabel('Silhouette score')
    ax.set_title('Silhouette by K')
    ax.set_xticks(k_values)

    fig.tight_layout()
    path = Path(output_dir) / 'silhouette_scores.png'
    fig.savefig(path, dpi=200, bbox_inches='tight')
    plt.close(fig)
    logger.info(f"Saved silhouette plot to {path}")


def plot_k_selection_metrics(results_frame: pd.DataFrame,
                             selected_k: int,
                             output_dir: str = 'outputs/figures') -> None:
    """Plot all four selection metrics plus stability in one panel."""
    logger.info("Plotting K selection metrics")

    panels = [
        ('silhouette', 'Silhouette (higher is better)'),
        ('calinski_harabasz', 'Calinski-Harabasz (higher is better)'),
        ('davies_bouldin', 'Davies-Bouldin (lower is better)'),
        ('stability_mean_ari', 'Stability, mean pairwise ARI (higher is better)'),
    ]

    fig, axes = plt.subplots(2, 2, figsize=(12, 8))
    for ax, (column, title) in zip(axes.ravel(), panels):
        if column not in results_frame or results_frame[column].isnull().all():
            ax.text(0.5, 0.5, f'{column} not measured', ha='center', va='center')
            ax.set_axis_off()
            continue
        ax.plot(results_frame['K'], results_frame[column], marker='o', color='steelblue')
        ax.axvline(selected_k, color='darkred', linestyle='--')
        ax.set_title(title, fontsize=10)
        ax.set_xlabel('K')
        ax.set_xticks(results_frame['K'])

    fig.suptitle(f'Evidence behind the choice of K (selected K={selected_k}, dashed line)')
    fig.tight_layout()
    path = Path(output_dir) / 'k_selection_metrics.png'
    fig.savefig(path, dpi=200, bbox_inches='tight')
    plt.close(fig)
    logger.info(f"Saved K selection metrics to {path}")


def plot_cluster_visualization(X_pca: np.ndarray,
                               labels: np.ndarray,
                               kmeans: KMeans,
                               output_dir: str = 'outputs/figures') -> None:
    """Scatter the first two components, coloured by cluster.

    Centroids come from the fitted model that produced these labels. Refitting a
    second model here would draw centroids belonging to a different partition.
    """
    if X_pca.shape[1] < 2:
        logger.warning("Fewer than two components, skipping cluster scatter")
        return

    logger.info("Plotting cluster visualization")

    fig, ax = plt.subplots(figsize=(8.5, 6.5))
    palette = plt.cm.tab10(np.linspace(0, 1, 10))

    for cluster_id in np.unique(labels):
        mask = labels == cluster_id
        ax.scatter(X_pca[mask, 0], X_pca[mask, 1],
                   color=palette[cluster_id % 10], label=f'Cluster {cluster_id}',
                   alpha=0.65, s=34, edgecolors='white', linewidth=0.4)

    centroids = kmeans.cluster_centers_
    ax.scatter(centroids[:, 0], centroids[:, 1], c='black', marker='X', s=150,
               label='Centroids', zorder=10)

    ax.set_xlabel('PC1')
    ax.set_ylabel('PC2')
    ax.set_title('Clusters in the first two principal components')
    ax.legend()

    fig.tight_layout()
    path = Path(output_dir) / 'cluster_visualization_2d.png'
    fig.savefig(path, dpi=200, bbox_inches='tight')
    plt.close(fig)
    logger.info(f"Saved cluster visualization to {path}")


def save_clustering_model(kmeans: KMeans, labels: np.ndarray, model_dir: str = 'models') -> None:
    """Persist the fitted model and the labels it produced."""
    logger.info("Saving clustering model")

    Path(model_dir).mkdir(parents=True, exist_ok=True)
    joblib.dump(kmeans, Path(model_dir) / 'kmeans_model.pkl')
    np.save(Path(model_dir) / 'cluster_labels.npy', labels)

    logger.info(f"Clustering model saved to {model_dir}")


def run_clustering_pipeline(X_pca: np.ndarray,
                            k_range: Tuple[int, int] = (2, 11),
                            random_state: int = 42,
                            test_stability: bool = True,
                            stability_runs: int = DEFAULT_STABILITY_RUNS,
                            output_dir: str = 'outputs/figures',
                            model_dir: str = 'models',
                            metrics_dir: Optional[str] = None) -> ClusteringResults:
    """Run the full clustering step and persist metrics, figures and models.

    Args:
        X_pca: PCA scores, one row per consumer.
        k_range: Half-open (min, max) range of candidate K.
        random_state: Seed for every fit.
        test_stability: Whether to measure stability across restarts.
        stability_runs: Restarts per K when stability is measured.
        output_dir: Directory for figures.
        model_dir: Directory for models.
        metrics_dir: Directory for CSV tables. Defaults to a sibling 'metrics'
            directory next to output_dir.

    Returns:
        ClusteringResults holding the fitted model, labels and every metric.
    """
    logger.info("Starting clustering pipeline")

    figures_path = Path(output_dir)
    models_path = Path(model_dir)
    metrics_path = Path(metrics_dir) if metrics_dir else figures_path.parent / 'metrics'
    for path in (figures_path, models_path, metrics_path):
        path.mkdir(parents=True, exist_ok=True)

    k_values, inertia, silhouette, ch, db, stability = find_optimal_k(
        X_pca, k_range, random_state,
        stability_runs=stability_runs if test_stability else 0,
    )

    optimal_k, trace = select_optimal_k(
        k_values, inertia, silhouette, ch, db,
        stability_by_k=stability if test_stability else None,
    )

    kmeans, labels = perform_kmeans(X_pca, optimal_k, random_state)

    results = ClusteringResults(
        model=kmeans,
        labels=labels,
        optimal_k=optimal_k,
        k_values=k_values,
        inertia_by_k=inertia,
        silhouette_by_k=silhouette,
        ch_by_k=ch,
        db_by_k=db,
        stability_by_k=stability,
        selection_trace=trace,
    )

    frame = results.metrics_frame()
    frame.to_csv(metrics_path / 'clustering_metrics.csv', index=False)
    if test_stability:
        pd.DataFrame([stability[k] for k in k_values]).to_csv(
            metrics_path / 'stability_results.csv', index=False
        )
    (metrics_path / 'k_selection_trace.json').write_text(
        json.dumps(trace, indent=2), encoding='utf-8'
    )

    plot_elbow_curve(k_values, [inertia[k] for k in k_values], optimal_k, str(figures_path))
    plot_silhouette_scores(k_values, [silhouette[k] for k in k_values], optimal_k, str(figures_path))
    plot_k_selection_metrics(frame, optimal_k, str(figures_path))
    plot_cluster_visualization(X_pca, labels, kmeans, str(figures_path))

    save_clustering_model(kmeans, labels, str(models_path))

    logger.info("Clustering pipeline completed")
    return results


if __name__ == "__main__":
    from project_paths import anchor_to_project_root

    anchor_to_project_root()

    from data_loader import generate_synthetic_data
    from feature_engineering import engineer_all_features, select_features
    from pca_analysis import run_pca_pipeline
    from preprocessing import preprocess_pipeline

    raw = generate_synthetic_data(n_consumers=200, n_days=30, hourly_records=True)
    preprocessed = preprocess_pipeline(raw.drop(columns=['archetype']))
    features = select_features(
        engineer_all_features(preprocessed, feature_set='behavioral'),
        feature_group='behavioral',
    )
    X_pca, pca, scaler, n_components = run_pca_pipeline(features)

    results = run_clustering_pipeline(X_pca, test_stability=True)

    print(f"\nSelected K: {results.optimal_k}")
    print(f"Cluster sizes: {np.bincount(results.labels).tolist()}")
    print(f"Silhouette at selected K: {results.silhouette_by_k[results.optimal_k]:.4f}")
    if results.stability:
        print(f"Stability ARI: {results.stability['mean_ari']:.4f} "
              f"+/- {results.stability['std_ari']:.4f}")
    print("\n" + results.metrics_frame().to_string(index=False))
