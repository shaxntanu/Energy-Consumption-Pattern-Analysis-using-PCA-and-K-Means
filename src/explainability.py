"""
Explainability Module (Improvement 4: XAI / SHAP)

Answers one question the clustering result does not: *why* does a consumer land in
the cluster it lands in?

The clustering itself is unsupervised and has no notion of feature importance.
This module therefore trains a small, shallow surrogate model - a random forest
that predicts the recovered cluster labels from the same behavioural features
K-Means was fitted on - and explains *that* model. Two things follow from this
design and are worth stating plainly:

1. The surrogate is POST-HOC. It is fitted after clustering, it never feeds back
   into PCA or K-Means, and it cannot change any cluster. It is an interpreter,
   not part of the analysis.
2. It works on the ORIGINAL 51 behavioural features, not on the PCA scores. That
   is deliberate: a loading table already says how a feature relates to a
   component, but a reader wants to know how a feature separates the clusters.
   The surrogate restates the clusters in feature units, which is the same
   language the cluster profiles use.

Which explainer runs:

- When the optional dependency `shap` is installed, a TreeExplainer is fitted on
  the surrogate and SHAP values are computed for every consumer. Per cluster the
  feature with the largest mean |SHAP| is reported with the sign of the mean SHAP
  (does that feature push consumers INTO this cluster or away from it?).
- When `shap` is not installed the module falls back to per-cluster permutation
  importance: a one-vs-rest forest per cluster and the mean drop in accuracy
  when each feature is shuffled. This is a different, coarser statistic, so the
  artifact records `method: "permutation_fallback"` and never pretends the two
  are the same.

Both methods report how well the surrogate itself can predict the labels
(cross-validated balanced accuracy). That number is the honest ceiling on what
any feature-importance reading can claim: if the surrogate only predicts 60% of
cluster memberships, the features only explain 60% of the grouping, and the
report says so.

Run via:  py src/explainability.py
"""

import json
import logging
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import numpy as np
import pandas as pd

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

N_CLUSTERS_MIN = 2
# Rows fed to TreeExplainer. Feature rows are per-consumer, so even a full year
# of 200 consumers stays tiny; the cap exists for very large panels.
EXPLAIN_CAP = 2000
BACKGROUND_SAMPLE = 100
RANDOM_STATE = 42


def _load_shap():
    """Import shap if it is installed, otherwise return None.

    Returns:
        The shap module, or None when it is not importable.
    """
    try:
        import shap  # type: ignore
        return shap
    except Exception as exc:  # pragma: no cover - environment dependent
        logger.info("shap not available; using permutation fallback")
        return None


def _surrogate_cv_accuracy(X: np.ndarray, labels: np.ndarray) -> float:
    """Cross-validated balanced accuracy of the surrogate classifier.

    scikit-learn's cross_val_score is not used here because it cannot report
    BALANCED accuracy directly, and balanced accuracy is the honest number when
    cluster sizes differ (as they do).

    Args:
        X: Feature matrix, standardized.
        labels: Cluster labels.

    Returns:
        Mean balanced accuracy across 5 folds, 0 to 1.
    """
    from sklearn.model_selection import StratifiedKFold, cross_val_score
    from sklearn.metrics import make_scorer, balanced_accuracy_score
    from sklearn.ensemble import RandomForestClassifier

    cv = StratifiedKFold(n_splits=5, shuffle=True, random_state=RANDOM_STATE)
    clf = RandomForestClassifier(n_estimators=120, max_depth=6,
                                 random_state=RANDOM_STATE, n_jobs=-1)
    scorer = make_scorer(balanced_accuracy_score)
    scores = cross_val_score(clf, X, labels, cv=cv, scoring=scorer)
    return float(np.mean(scores))


def _fit_surrogate(X: np.ndarray, labels: np.ndarray):
    """Fit the post-hoc surrogate forest on the full standardized feature matrix."""
    from sklearn.ensemble import RandomForestClassifier

    clf = RandomForestClassifier(n_estimators=120, max_depth=6,
                                 random_state=RANDOM_STATE, n_jobs=-1)
    clf.fit(X, labels)
    return clf


def _shap_importance(X: np.ndarray, labels: np.ndarray,
                     feature_names: List[str]) -> Tuple[List[dict], dict]:
    """Per-cluster and global feature importance via SHAP on the surrogate.

    Args:
        X: Standardized feature matrix.
        labels: Cluster labels.
        feature_names: Feature names in X column order.

    Returns:
        Tuple of (per_cluster list, global_importance dict).
    """
    shap = _load_shap()
    if shap is None:
        raise RuntimeError("shap required for _shap_importance")

    clf = _fit_surrogate(X, labels)
    explainer = shap.TreeExplainer(clf)
    explain_rows = min(EXPLAIN_CAP, len(X))
    X_explain = X[:explain_rows]
    labels_explain = labels[:explain_rows]
    raw_values = explainer.shap_values(X_explain)
    shap_values = np.asarray(raw_values)

    # shap changed the multiclass layout across versions: older versions return
    # a list of per-class arrays (K, n, p); 0.52+ returns one array with the
    # class axis LAST (n, p, K). Normalize to class-first so the per-cluster
    # split below is version-proof.
    n_clusters = int(len(np.unique(labels)))
    if (shap_values.ndim == 3 and shap_values.shape[0] == X_explain.shape[0]
            and shap_values.shape[2] == n_clusters):
        shap_values = shap_values.transpose(2, 0, 1)   # (n, p, K) -> (K, n, p)
    elif (shap_values.ndim == 3 and shap_values.shape[1] == n_clusters
            and shap_values.shape[2] == X.shape[1]):
        shap_values = shap_values.transpose(1, 0, 2)   # (n, K, p) -> (K, n, p)
    # else: already (K, n, p), or a genuinely 2-D binary output — leave it.

    # shap_values is (n_clusters, n_rows, n_features).
    if shap_values.ndim == 3 and shap_values.shape[0] == n_clusters:
        per_cluster = []
        for c in range(n_clusters):
            mask = labels_explain == c
            block = shap_values[c][mask]
            if len(block) == 0:
                continue
            mean_abs = np.abs(block).mean(axis=0)
            mean_val = block.mean(axis=0)
            order = np.argsort(-mean_abs)
            per_cluster.append({
                'cluster': int(c),
                'n_rows': int(mask.sum()),
                'top_features': [
                    {
                        'feature': feature_names[i],
                        'mean_abs_shap': float(mean_abs[i]),
                        'mean_shap': float(mean_val[i]),
                        'direction': ('pushes into' if mean_val[i] > 0
                                      else 'pushes away'),
                    }
                    for i in order[:10]
                ],
            })
    else:
        # A binary surrogate returns (n_rows, n_features). There is still one
        # SHAP value per feature per consumer, so the global aggregation below
        # works; only the per-cluster split is unavailable.
        per_cluster = [{
            'cluster': int(c),
            'top_features': [],
        } for c in range(n_clusters)]

    flat = shap_values.reshape(-1, shap_values.shape[-1])
    global_abs = np.abs(flat).mean(axis=0)
    global_signed = flat.mean(axis=0)
    order = np.argsort(-global_abs)
    global_importance = {
        'top_features': [
            {
                'feature': feature_names[i],
                'mean_abs_shap': float(global_abs[i]),
                'mean_shap': float(global_signed[i]),
            }
            for i in order[:15]
        ],
    }
    return per_cluster, global_importance


def _permutation_importance(X: np.ndarray, labels: np.ndarray,
                            feature_names: List[str]) -> Tuple[List[dict], dict]:
    """Per-cluster importance via one-vs-rest permutation importance (fallback).

    For each cluster a binary forest predicts "in this cluster or not"; shuffling
    a feature and measuring the drop in balanced accuracy says how much that
    feature carries the cluster's identity. There is no direction in this method
    (shuffling removes a signal without saying which way it points), so the
    per-cluster rows carry direction=None.

    Args:
        X: Standardized feature matrix.
        labels: Cluster labels.
        feature_names: Feature names in X column order.

    Returns:
        Tuple of (per_cluster list, global_importance dict).
    """
    from sklearn.ensemble import RandomForestClassifier
    from sklearn.inspection import permutation_importance

    clusters = np.unique(labels)
    per_cluster = []
    global_abs = np.zeros(len(feature_names))

    for c in clusters:
        binary = np.asarray(labels == c, dtype=int)
        clf = RandomForestClassifier(n_estimators=100, max_depth=4,
                                     random_state=RANDOM_STATE, n_jobs=-1)
        clf.fit(X, binary)
        result = permutation_importance(
            clf, X, binary, n_repeats=5, random_state=RANDOM_STATE, n_jobs=-1
        )
        mean_imp = result.importances_mean
        global_abs += mean_imp
        order = np.argsort(-mean_imp)
        per_cluster.append({
            'cluster': int(c),
            'n_rows': int((labels == c).sum()),
            'top_features': [
                {
                    'feature': feature_names[i],
                    'importance': float(mean_imp[i]),
                    'direction': None,
                }
                for i in order[:10]
            ],
        })

    global_abs /= len(clusters)
    order = np.argsort(-global_abs)
    global_importance = {
        'top_features': [
            {'feature': feature_names[i], 'importance': float(global_abs[i])}
            for i in order[:15]
        ],
    }
    return per_cluster, global_importance


def run_explainability(features: pd.DataFrame,
                       labels: np.ndarray,
                       feature_names: Optional[List[str]] = None,
                       output_dir: str = 'outputs/figures',
                       reports_dir: str = 'outputs/reports',
                       metrics_dir: str = 'outputs/metrics') -> dict:
    """Explain the recovered clusters in feature units and persist the artifacts.

    Args:
        features: Per-consumer feature frame, one row per consumer. Must contain
            every column named in feature_names.
        labels: Cluster label per consumer, in the same order as features.
        feature_names: Features to explain, in order. Defaults to every non-
            consumer_id column of features.
        output_dir: Directory for figures.
        reports_dir: Directory for the markdown report.
        metrics_dir: Directory for the JSON and CSV metrics.

    Returns:
        Dictionary of explainability results with a 'method' key ('shap' or
        'permutation_fallback'). Returns {'method': 'not_run', 'reason': ...}
        when the input has too few consumers or clusters.
    """
    output_dir = Path(output_dir)
    reports_dir = Path(reports_dir)
    metrics_dir = Path(metrics_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    reports_dir.mkdir(parents=True, exist_ok=True)
    metrics_dir.mkdir(parents=True, exist_ok=True)

    labels = np.asarray(labels)
    if feature_names is None:
        feature_names = [c for c in features.columns if c != 'consumer_id']
    feature_names = [c for c in feature_names if c in features.columns]
    if not feature_names:
        return {'method': 'not_run', 'reason': 'no feature columns to explain'}

    if len(labels) < N_CLUSTERS_MIN + 1 or len(np.unique(labels)) < N_CLUSTERS_MIN:
        return {'method': 'not_run',
                'reason': f'need at least {N_CLUSTERS_MIN} clusters and consumers'}

    X = features[feature_names].to_numpy(dtype=float)
    # Standardize for the surrogate exactly as the pipeline standardizes for PCA,
    # so a feature's importance is not an artefact of its units.
    from sklearn.preprocessing import StandardScaler
    X_std = StandardScaler().fit_transform(X)

    cv_accuracy = _surrogate_cv_accuracy(X_std, labels)

    shap = _load_shap()
    method = 'shap' if shap is not None else 'permutation_fallback'
    if method == 'shap':
        try:
            per_cluster, global_importance = _shap_importance(X_std, labels, feature_names)
        except Exception as exc:  # pragma: no cover - environment dependent
            # A broken shap install must never take the pipeline down with it.
            # Fall back to permutation importance and say so honestly.
            logger.warning(f"SHAP explainer failed ({exc}); using permutation fallback")
            method = 'permutation_fallback'
            per_cluster, global_importance = _permutation_importance(
                X_std, labels, feature_names
            )
    else:
        per_cluster, global_importance = _permutation_importance(
            X_std, labels, feature_names
        )

    results = {
        'method': method,
        'surrogate': 'RandomForestClassifier (post-hoc, fitted after clustering)',
        'n_features': len(feature_names),
        'n_clusters': int(len(np.unique(labels))),
        'n_consumers': int(len(labels)),
        'cv_balanced_accuracy': cv_accuracy,
        'note': (
            'cv_balanced_accuracy is the cross-validated accuracy of a forest '
            'predicting the recovered cluster labels from the behavioural features. '
            'It is the ceiling on how much of the grouping the features can be said '
            'to explain.'
        ),
        'per_cluster': per_cluster,
        'global_importance': global_importance,
    }

    (metrics_dir / 'explainability.json').write_text(
        json.dumps(results, indent=2), encoding='utf-8')

    # CSV: one row per (cluster, feature) for the dashboard / Vercel.
    rows = []
    for entry in per_cluster:
        for feat in entry.get('top_features', []):
            rows.append({
                'cluster': entry['cluster'],
                'feature': feat['feature'],
                'importance': feat.get('mean_abs_shap', feat.get('importance', None)),
                'direction': feat.get('direction'),
            })
    if rows:
        pd.DataFrame(rows).to_csv(metrics_dir / 'shap_importance.csv', index=False)

    # Figure: one horizontal bar panel per cluster, top features.
    try:
        import matplotlib
        matplotlib.use('Agg', force=True)
        import matplotlib.pyplot as plt

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
        path = output_dir / 'shap_cluster_importance.png'
        fig.savefig(path, dpi=150)
        plt.close(fig)
        results['figure'] = str(path)
    except Exception as exc:
        logger.warning(f"Could not render explainability figure: {exc}")

    report_lines = [
        "# Explainability Report (Improvement 4: XAI / SHAP)",
        "",
        "The clustering itself is unsupervised and has no feature importance. A",
        "small, shallow random forest was therefore fitted AFTER clustering to",
        "predict the recovered cluster labels from the same 51 behavioural features",
        f"the pipeline used. Method: **{method}**.",
        "",
        f"- Surrogate: RandomForestClassifier (post-hoc, never feeds back into PCA",
        f"  or K-Means)",
        f"- Consumers explained: {len(labels)}, features: {len(feature_names)}",
        f"- Cross-validated balanced accuracy of the surrogate: {cv_accuracy:.3f}",
        "",
        "This accuracy is the honest ceiling on feature-importance claims: if the",
        "surrogate predicts most memberships, the features genuinely carry the",
        "grouping; if it does not, the clusters are driven by structure the",
        "features do not capture and no importance table can manufacture it.",
        "",
    ]
    if method == 'shap':
        report_lines += [
            "## SHAP (TreeExplainer)",
            "",
            "Per cluster, the ten features with the largest mean |SHAP| are listed.",
            "The direction column says whether a HIGHER value of the feature pushes a",
            "consumer INTO the cluster or AWAY from it.",
            "",
        ]
    else:
        report_lines += [
            "## Permutation importance (fallback)",
            "",
            "`shap` is not installed, so each cluster was explained by a one-vs-rest",
            "forest and the mean drop in balanced accuracy when each feature is",
            "shuffled. There is no direction in this method: it says which features",
            "matter, not which way they point.",
            "",
        ]
    for entry in per_cluster:
        report_lines.append(f"### Cluster {entry['cluster']} ({entry.get('n_rows', '?')} consumers)")
        feats = entry.get('top_features', [])
        if not feats:
            report_lines.append("- no features")
            continue
        for f in feats:
            value = f.get('mean_abs_shap', f.get('importance', 0.0))
            direction = f.get('direction')
            line = f"- `{f['feature']}` importance {value:.4f}"
            if direction:
                line += f" ({direction})"
            report_lines.append(line)
        report_lines.append("")

    report_lines += [
        "## Global picture",
        "",
        "The features that separate the clusters most overall:",
        "",
    ]
    for f in global_importance.get('top_features', []):
        value = f.get('mean_abs_shap', f.get('importance', 0.0))
        report_lines.append(f"- `{f['feature']}` {value:.4f}")
    report_lines += [
        "",
        "Caveats: this is a post-hoc interpretation of an unsupervised grouping,",
        "not a causal analysis. The features were standardized before the surrogate",
        "was fitted, so importance is comparable across features. SHAP values and",
        "permutation importance are different statistics and must not be compared",
        "against each other; the method key above states which one produced this",
        "report.",
        "",
    ]
    (reports_dir / 'explainability_report.md').write_text(
        "\n".join(report_lines), encoding='utf-8')

    logger.info(
        f"Explainability done: method={method}, surrogate cv accuracy={cv_accuracy:.3f}"
    )
    return results


if __name__ == "__main__":
    from project_paths import anchor_to_project_root

    anchor_to_project_root()

    from clustering import run_clustering_pipeline
    from data_loader import generate_synthetic_data
    from feature_engineering import engineer_all_features, select_features
    from pca_analysis import run_pca_pipeline
    from preprocessing import preprocess_pipeline

    raw = generate_synthetic_data(n_consumers=200, n_days=30, hourly_records=True)
    preprocessed = preprocess_pipeline(raw.drop(columns=['archetype', 'seasonal_phase'],
                                                 errors='ignore'))
    behavioral = select_features(
        engineer_all_features(preprocessed, feature_set='behavioral'),
        feature_group='behavioral',
    )
    order = behavioral['consumer_id'].tolist()

    X_pca, pca, scaler, n_components = run_pca_pipeline(behavioral)
    clustering = run_clustering_pipeline(X_pca, test_stability=False)

    result = run_explainability(
        behavioral, clustering.labels,
        feature_names=[c for c in behavioral.columns if c != 'consumer_id'],
        output_dir='outputs/figures', reports_dir='outputs/reports',
        metrics_dir='outputs/metrics',
    )
    print(json.dumps(result, indent=2, default=str))
