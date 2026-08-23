"""
Ablation Study Module

Answers one question: does the feature engineering actually change what the
clustering finds, or would any set of columns have produced a similar answer?

Five arms, run on the same generated data with the same seed and the same K
selection rule, so the only thing that varies is the input columns:

- A, scale: magnitude only. Mean, max, total and electrical summaries. This is
  the naive baseline, the analysis someone gets by feeding raw numbers to
  K-Means.
- B, shape: the normalized 24-hour profile and nothing else.
- C, summary: the scalars derived from that profile, without the profile itself.
  Period shares, peak timing, weekend behaviour, concentration, frequency
  content, variability.
- D, behavioral: B and C together. This is what the primary pipeline uses.
- E, combined: everything, behaviour and magnitude.

Arms B and C exist because D is not self-evidently better than either of them.
The 24 raw bins and the 27 descriptors carry overlapping information, and adding
both means a distinction encoded in one feature competes with 50 other
standardized dimensions. Running them separately is the only way to find out
whether the larger set earns its size.

The decision rule is written down here before any numbers are produced, for the
same reason the K selection rule is pre-registered in clustering.py.

    1. Reject an arm whose partition is unstable across restarts (mean pairwise
       ARI below MIN_STABILITY_ARI) or which leaves a cluster below
       MIN_CLUSTER_SHARE of consumers. An unstable partition is not a finding.
    2. Among the arms that survive, prefer the one that best serves the stated
       research question: grouping consumers by when they use energy rather than
       how much. On synthetic data that is measurable directly, as agreement with
       the hidden archetypes the generator drew from. Where no ground truth
       exists, fall back to the shape separation ratio defined below.
    3. When two arms come within ARM_SCORE_TOLERANCE of each other on that
       criterion, prefer the one with fewer features. Differences that small are
       not resolvable on 200 consumers, and a smaller feature set is easier to
       explain and gives each distinction more of the distance budget.
    4. Report every arm's silhouette score, but do not let it decide. Silhouette
       rewards compact, well separated clusters in whatever space it is given.
       An arm that separates cleanly on magnitude scores well while answering a
       different question, so using silhouette to pick the arm would quietly
       replace the research question with whichever one the data answers most
       easily.

Two diagnostics make the "different question" claim measurable. Both are
computed from the same combined feature table for every arm, so they compare
like with like:

- scale_separation: between-cluster spread of mean kWh, divided by the spread of
  mean kWh across all consumers. High means the arm sorted consumers by how much
  they use.
- shape_separation: the same ratio computed on the normalized 24-hour load shape
  and averaged over the 24 hours. High means the arm sorted consumers by when
  they use energy.

THIS IS SYNTHETIC DATA. The comparison shows how the pipeline behaves under
different inputs. It is not evidence about real households.
"""

import logging
import os

os.environ.setdefault('MPLBACKEND', 'Agg')

from pathlib import Path
from typing import Dict, List, Optional, Sequence, Tuple

import matplotlib

matplotlib.use('Agg', force=True)

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from sklearn.metrics import adjusted_rand_score, normalized_mutual_info_score

from clustering import MIN_CLUSTER_SHARE, MIN_STABILITY_ARI, run_clustering_pipeline
from data_loader import generate_synthetic_data
from feature_engineering import engineer_all_features, select_features
from pca_analysis import run_pca_pipeline
from preprocessing import preprocess_pipeline

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

ARMS: List[Tuple[str, str]] = [
    ('scale', 'A, scale only: magnitude summaries, the naive baseline'),
    ('shape', 'B, shape only: the normalized 24-hour profile, nothing else'),
    ('summary', 'C, summary only: the scalars derived from the profile, without the profile'),
    ('behavioral', 'D, behavioral: shape and summary together, what the pipeline uses'),
    ('combined', 'E, combined: behaviour and magnitude together'),
]

SCALE_METRICS: Tuple[str, ...] = ('energy_consumption_kwh_mean', 'mean_kwh')

# Two arms scoring within this of each other on the deciding criterion are treated
# as tied, and the smaller feature set wins. On 200 consumers an ARI gap of a few
# hundredths is not a distinction worth acting on.
ARM_SCORE_TOLERANCE = 0.02


def _separation_ratio(values: pd.Series, labels: np.ndarray) -> float:
    """Between-cluster spread of one feature, relative to its overall spread.

    Weighted standard deviation of the cluster means over the standard deviation
    across consumers. Zero means the clusters carry no information about the
    feature; one means almost all of the variation sits between clusters.

    Args:
        values: One feature, one value per consumer.
        labels: Cluster label per consumer, in the same order.

    Returns:
        The ratio, or nan when the feature does not vary.
    """
    series = pd.Series(np.asarray(values, dtype=float))
    total_sd = series.std()
    if not np.isfinite(total_sd) or total_sd == 0:
        return float('nan')

    grand_mean = series.mean()
    counts = pd.Series(labels).value_counts()
    cluster_means = series.groupby(pd.Series(labels)).mean()
    between_var = float(
        (counts.reindex(cluster_means.index) * (cluster_means - grand_mean) ** 2).sum()
        / len(series)
    )
    return float(np.sqrt(between_var) / total_sd)


def separation_diagnostics(combined_features: pd.DataFrame,
                           labels: np.ndarray) -> Dict[str, float]:
    """Measure whether a partition sorted consumers by magnitude or by timing.

    Args:
        combined_features: Feature table holding both groups, one row per
            consumer, already aligned to the label order.
        labels: Cluster labels.

    Returns:
        Dictionary with scale_separation and shape_separation.
    """
    diagnostics: Dict[str, float] = {}

    scale_col = next((c for c in SCALE_METRICS if c in combined_features.columns), None)
    if scale_col is not None:
        diagnostics['scale_separation'] = _separation_ratio(
            combined_features[scale_col], labels
        )
    else:
        logger.warning(f"No magnitude column found among {SCALE_METRICS}; "
                       f"scale separation cannot be measured")
        diagnostics['scale_separation'] = float('nan')

    shape_cols = [c for c in combined_features.columns
                  if c.startswith('hour_') and c.endswith('_shape')]
    if shape_cols:
        ratios = [_separation_ratio(combined_features[c], labels) for c in shape_cols]
        diagnostics['shape_separation'] = float(np.nanmean(ratios))
    else:
        diagnostics['shape_separation'] = float('nan')

    return diagnostics


def run_one_arm(feature_set: str,
                preprocessed: pd.DataFrame,
                combined_features: pd.DataFrame,
                truth_by_consumer: Optional[pd.Series],
                k_range: Tuple[int, int],
                random_seed: int,
                stability_runs: int,
                arm_root: Path) -> dict:
    """Run the full pipeline on one feature set and collect its metrics.

    Artifacts are written under arm_root so the canonical models/ and outputs/
    directories produced by the primary analysis are never overwritten.

    Args:
        feature_set: Any key of feature_engineering.FEATURE_GROUPS.
        preprocessed: Cleaned panel data.
        combined_features: Feature table used for the separation diagnostics.
        truth_by_consumer: Hidden archetype per consumer, or None.
        k_range: Half-open range of candidate K.
        random_seed: Seed for every fit.
        stability_runs: Restarts per K.
        arm_root: Directory for this arm's figures, models and metrics.

    Returns:
        One row of the ablation table.
    """
    logger.info(f"Ablation arm: {feature_set}")

    features = engineer_all_features(preprocessed, feature_set=feature_set)
    selected = select_features(features, feature_group=feature_set)
    consumer_order = selected['consumer_id'].tolist()

    figures = arm_root / 'figures'
    models = arm_root / 'models'
    metrics = arm_root / 'metrics'
    for path in (figures, models, metrics):
        path.mkdir(parents=True, exist_ok=True)

    X_pca, pca, _, n_components = run_pca_pipeline(
        selected, output_dir=str(figures), model_dir=str(models)
    )
    clustering = run_clustering_pipeline(
        X_pca,
        k_range=k_range,
        random_state=random_seed,
        test_stability=True,
        stability_runs=stability_runs,
        output_dir=str(figures),
        model_dir=str(models),
        metrics_dir=str(metrics),
    )

    labels = clustering.labels
    k = clustering.optimal_k
    sizes = np.bincount(labels, minlength=k)
    stability = clustering.stability or {}

    aligned = (combined_features.set_index('consumer_id')
               .reindex(consumer_order)
               .reset_index())

    row = {
        'arm': feature_set,
        'n_features': selected.drop(columns=['consumer_id'], errors='ignore').shape[1],
        'n_pca_components': int(n_components),
        'cumulative_variance': float(pca.explained_variance_ratio_.sum()),
        'optimal_k': int(k),
        'silhouette': float(clustering.silhouette_by_k[k]),
        'calinski_harabasz': float(clustering.ch_by_k[k]),
        'davies_bouldin': float(clustering.db_by_k[k]),
        'stability_mean_ari': float(stability.get('mean_ari', float('nan'))),
        'stability_std_ari': float(stability.get('std_ari', float('nan'))),
        'min_cluster_share': float(sizes.min() / sizes.sum()),
        'cluster_balance': float(sizes.min() / sizes.max()),
        'cluster_sizes': str(sizes.tolist()),
    }
    row.update(separation_diagnostics(aligned, labels))

    if truth_by_consumer is not None:
        truth = truth_by_consumer.reindex(consumer_order).to_numpy()
        row['archetype_ari'] = float(adjusted_rand_score(truth, labels))
        row['archetype_nmi'] = float(normalized_mutual_info_score(truth, labels))
        row['n_true_archetypes'] = int(pd.Series(truth).nunique())
    else:
        row['archetype_ari'] = float('nan')
        row['archetype_nmi'] = float('nan')
        row['n_true_archetypes'] = 0

    logger.info(
        f"  {feature_set}: K={k}, silhouette {row['silhouette']:.4f}, "
        f"stability ARI {row['stability_mean_ari']:.4f}, "
        f"archetype ARI {row['archetype_ari']:.4f}, "
        f"scale separation {row['scale_separation']:.3f}, "
        f"shape separation {row['shape_separation']:.3f}"
    )
    return row


def choose_primary_arm(results: pd.DataFrame) -> Tuple[str, List[str]]:
    """Apply the pre-registered decision rule to the measured arms.

    The rule is stated in the module docstring and is applied here without
    reference to which arm the project happens to use. The prose returned is
    generated from the numbers, including the case where the rule selects an arm
    that loses on silhouette.

    Args:
        results: The ablation table, one row per arm.

    Returns:
        Tuple of (chosen arm, list of markdown lines explaining the choice).
    """
    lines: List[str] = []

    qualified = results[
        (results['stability_mean_ari'] >= MIN_STABILITY_ARI)
        & (results['min_cluster_share'] >= MIN_CLUSTER_SHARE)
    ]
    rejected = results[~results['arm'].isin(qualified['arm'])]

    for _, row in rejected.iterrows():
        reasons = []
        if row['stability_mean_ari'] < MIN_STABILITY_ARI:
            reasons.append(
                f"stability ARI {row['stability_mean_ari']:.4f} below {MIN_STABILITY_ARI}"
            )
        if row['min_cluster_share'] < MIN_CLUSTER_SHARE:
            reasons.append(
                f"smallest cluster {row['min_cluster_share']:.1%} below "
                f"{MIN_CLUSTER_SHARE:.0%}"
            )
        lines.append(f"- Step 1 rejected {row['arm']}: {'; '.join(reasons)}.")

    if qualified.empty:
        lines.append(
            "- Step 1 rejected every arm. No arm produced a partition worth "
            "interpreting, so the filter is relaxed and the result below is weak."
        )
        qualified = results

    has_truth = qualified['archetype_ari'].notna().any() and (qualified['n_true_archetypes'] > 0).any()
    if has_truth:
        criterion_column = 'archetype_ari'
        criterion = 'agreement with the hidden archetypes'
    else:
        criterion_column = 'shape_separation'
        criterion = 'shape separation, since no ground truth is available'

    best_value = float(qualified[criterion_column].max())
    tied = qualified[qualified[criterion_column] >= best_value - ARM_SCORE_TOLERANCE]
    chosen_row = tied.loc[tied['n_features'].idxmin()]
    chosen = str(chosen_row['arm'])

    if criterion_column == 'archetype_ari':
        chosen_value = f"ARI {chosen_row[criterion_column]:.4f}"
    else:
        chosen_value = f"shape separation {chosen_row[criterion_column]:.3f}"

    leader_row = qualified.loc[qualified[criterion_column].idxmax()]
    lines.append(
        f"- Step 2 ranked the survivors on {criterion}. The best value is "
        f"{best_value:.4f}, from {leader_row['arm']}."
    )

    if len(tied) > 1:
        tie_text = ", ".join(
            f"{row['arm']} ({row[criterion_column]:.4f}, {int(row['n_features'])} features)"
            for _, row in tied.sort_values('n_features').iterrows()
        )
        lines.append(
            f"- Step 3 found {len(tied)} arms within {ARM_SCORE_TOLERANCE} of that value: "
            f"{tie_text}. The tie-break is parsimony, so {chosen} is selected on "
            f"{int(chosen_row['n_features'])} features with {chosen_value}."
        )
    else:
        lines.append(
            f"- Step 3 found no other arm within {ARM_SCORE_TOLERANCE} of the best value, "
            f"so the parsimony tie-break does not apply and {chosen} is selected outright "
            f"with {chosen_value}."
        )

    best_sil = results.loc[results['silhouette'].idxmax()]
    if str(best_sil['arm']) != chosen:
        lines.append(
            f"- Step 4, for the record: {best_sil['arm']} has the highest silhouette "
            f"score ({best_sil['silhouette']:.4f} against {chosen_row['silhouette']:.4f} "
            f"for {chosen}). Silhouette did not decide the choice, and this is the case "
            f"the rule was written for. The {best_sil['arm']} arm separates its own "
            f"feature space more cleanly while answering a different question."
        )
    else:
        lines.append(
            f"- Step 4, for the record: {chosen} also has the highest silhouette score "
            f"({chosen_row['silhouette']:.4f}), so on this dataset the internal index "
            f"and the research question happen to agree. That agreement is a property "
            f"of this data, not a general result."
        )

    if results['scale_separation'].notna().any() and results['shape_separation'].notna().any():
        scale_leader = results.loc[results['scale_separation'].idxmax()]
        shape_leader = results.loc[results['shape_separation'].idxmax()]
        lines.append(
            f"- The diagnostics show what each arm keyed on. Magnitude separation is "
            f"highest for {scale_leader['arm']} ({scale_leader['scale_separation']:.3f}); "
            f"shape separation is highest for {shape_leader['arm']} "
            f"({shape_leader['shape_separation']:.3f})."
        )
    else:
        lines.append(
            "- The separation diagnostics could not be computed, because the feature "
            "table held no magnitude or no shape columns."
        )

    if has_truth:
        worst = results.loc[results['archetype_ari'].idxmin()]
        if float(worst['archetype_ari']) < 0.05:
            lines.append(
                f"- Worth stating plainly: the {worst['arm']} arm scores "
                f"{worst['archetype_ari']:.4f} against the archetypes. The Adjusted Rand "
                f"Index is corrected for chance, so a value at or below zero means that "
                f"partition carries no information about the groups the data was built "
                f"from, despite its silhouette score of {worst['silhouette']:.4f}."
            )

    return chosen, lines


def plot_ablation_comparison(results: pd.DataFrame,
                             output_dir: str = 'outputs/figures') -> None:
    """One figure with the three comparisons that matter.

    Left: the internal index. Middle: agreement with the hidden archetypes.
    Right: what each arm sorted consumers by. Putting them side by side is the
    point, because the left panel and the middle panel disagree.
    """
    logger.info("Plotting the ablation comparison")

    arms = results['arm'].tolist()
    positions = np.arange(len(arms))
    fig, axes = plt.subplots(1, 3, figsize=(15, 4.6))

    axes[0].bar(positions, results['silhouette'], color='steelblue', width=0.6)
    axes[0].set_title('Silhouette at the selected K\n(internal, no ground truth)')
    axes[0].set_ylabel('Silhouette')

    if results['archetype_ari'].notna().any():
        axes[1].bar(positions, results['archetype_ari'], color='darkred', width=0.6)
        axes[1].set_title('Agreement with the hidden archetypes\n(Adjusted Rand Index)')
        axes[1].set_ylabel('ARI')
        axes[1].set_ylim(0, 1.02)
    else:
        axes[1].axis('off')

    width = 0.36
    axes[2].bar(positions - width / 2, results['scale_separation'], width=width,
                label='Magnitude (mean kWh)', color='darkorange')
    axes[2].bar(positions + width / 2, results['shape_separation'], width=width,
                label='Timing (24-hour shape)', color='seagreen')
    axes[2].set_title('What each arm sorted consumers by')
    axes[2].set_ylabel('Between-cluster spread / total spread')
    axes[2].legend(fontsize=9)

    for ax in axes:
        if ax.has_data():
            ax.set_xticks(positions)
            ax.set_xticklabels(arms)
            ax.set_xlabel('Feature set')

    fig.suptitle('Ablation over feature sets, same data and same K selection rule')
    fig.tight_layout()

    path = Path(output_dir) / 'ablation_comparison.png'
    path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(path, dpi=200, bbox_inches='tight')
    plt.close(fig)
    logger.info(f"Saved the ablation comparison figure to {path}")


def generate_ablation_report(results: pd.DataFrame,
                             chosen: str,
                             reasoning: Sequence[str],
                             output_dir: str) -> None:
    """Write the ablation report as markdown."""
    logger.info("Writing the ablation report")

    display_columns = [
        'arm', 'n_features', 'n_pca_components', 'optimal_k', 'silhouette',
        'calinski_harabasz', 'davies_bouldin', 'stability_mean_ari',
        'archetype_ari', 'scale_separation', 'shape_separation', 'cluster_sizes',
    ]
    available = [c for c in display_columns if c in results.columns]

    # Which arm wins on internal quality alone. The rule deliberately does not use
    # this to decide, but whether it agrees with the selected arm is worth stating
    # either way, so it is measured rather than asserted.
    best_silhouette_arm = None
    if 'silhouette' in results.columns and results['silhouette'].notna().any():
        best_silhouette_arm = str(results.loc[results['silhouette'].idxmax(), 'arm'])

    lines = [
        "# Ablation Study",
        "",
        "THIS IS SYNTHETIC DATA. What follows shows how the pipeline behaves under",
        "different inputs. It is not evidence about real households.",
        "",
        "## The question",
        "",
        "Does the feature engineering change what the clustering finds, or would any",
        f"set of columns have produced a similar answer? {len(ARMS)} arms run on the same",
        "generated data, with the same seed and the same K selection rule, so the only",
        "thing that varies is which columns go in.",
        "",
    ]
    for _, description in ARMS:
        lines.append(f"- {description}")
    lines += [
        "",
        "## The decision rule, fixed before the run",
        "",
        "1. Reject an arm whose partition is unstable across restarts (mean pairwise "
        f"ARI below {MIN_STABILITY_ARI}) or which leaves a cluster below "
        f"{MIN_CLUSTER_SHARE:.0%} of consumers.",
        "2. Among the survivors, prefer the arm that best serves the research question:",
        "   grouping consumers by when they use energy rather than how much. On",
        "   synthetic data that is measured directly, as agreement with the hidden",
        "   archetypes. Without ground truth, fall back to shape separation.",
        f"3. Treat arms within {ARM_SCORE_TOLERANCE} of the best value as tied and prefer",
        "   the smaller feature set. A gap that size is not resolvable on this many",
        "   consumers, and every extra feature takes a share of the distance budget.",
        "4. Report silhouette for every arm but do not let it decide. Silhouette",
        "   rewards separation in whatever space it is given, so an arm that separates",
        "   cleanly on magnitude scores well while answering a different question.",
        "",
        "## Results",
        "",
        results[available].to_string(index=False),
        "",
        "### Reading the columns",
        "",
        "- silhouette, Calinski-Harabasz, Davies-Bouldin: internal quality at the",
        "  selected K. Higher, higher, lower is better.",
        "- stability_mean_ari: mean pairwise Adjusted Rand Index across restarts from",
        "  different seeds. How much the partition moves when only the seed changes.",
        "- archetype_ari: agreement with the archetypes the generator drew from. That",
        "  column is dropped before preprocessing and never reaches the model, so this",
        "  is an independent check. It exists only because the data is synthetic.",
        "- scale_separation, shape_separation: between-cluster spread of mean kWh and",
        "  of the normalized 24-hour shape, each divided by the spread across all",
        "  consumers. These say whether an arm sorted consumers by magnitude or by",
        "  timing. Both are computed from the same combined feature table for every",
        "  arm, so the arms are comparable.",
        "",
        "## Which arm the rule selects",
        "",
    ]
    lines += list(reasoning)
    lines += [
        "",
        f"Selected arm on this single dataset: {chosen}.",
        "",
        "This is the arm the rule returns on one draw of the generator (seed 42), and",
        "it is not the arm the project ships. The same rule run across 20 independent",
        "draws does not settle on one arm: it picks summary, behavioral and shape on",
        "different datasets, and on this particular draw it happens to land on "
        f"{chosen}. The pipeline's feature_set is fixed from that wider study, in",
        "outputs/reports/seed_robustness_report.md, which selects behavioral on the",
        "pooled evidence and treats any single-dataset selection here, including this",
        "one, as superseded wherever the two disagree. Read this report for the effect",
        "of the feature set on one draw, not for the choice of feature set.",
        "",
        "## What this does and does not establish",
        "",
        "It establishes that the choice of feature set changes the answer. The arms",
        "differ in K, in cluster sizes, in what they sort consumers by, and in how well",
        "they recover the groups the data was built from, all from the same 200",
        "consumers under the same rule.",
        "",
    ]

    if best_silhouette_arm is not None and best_silhouette_arm != chosen:
        lines += [
            "It also establishes that on this dataset the arm serving the stated research",
            f"question ({chosen}) is not the arm with the best internal score",
            f"({best_silhouette_arm}). That is the case worth knowing about, because a",
            "pipeline tuned on silhouette alone would have picked the other one.",
            "",
        ]
    elif best_silhouette_arm is not None:
        lines += [
            f"On this dataset the selected arm ({chosen}) also holds the best silhouette",
            "score. The two criteria agreeing is a property of this data rather than a",
            "general result, and the rule would have selected the same arm either way.",
            "",
        ]

    lines += [
        "It does not establish that behavioral features are the right choice for every",
        "energy segmentation problem. The generator built this data with timing",
        "differences in it, so an arm that reads timing is bound to do well here. On a",
        "real dataset the archetype column does not exist and the question would have to",
        "be settled on the shape separation diagnostic and on whether the resulting",
        "clusters are interpretable.",
        "",
        "It also does not establish that the selected feature set is minimal. The arms",
        f"test {len(ARMS)} specific groupings, not every subset of the columns, and a",
        "search over subsets guided by archetype agreement would be using the labels to",
        "build the model.",
        "",
    ]

    path = Path(output_dir) / 'ablation_study_report.md'
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines), encoding='utf-8')
    logger.info(f"Ablation report saved to {path}")


def run_ablation_study(n_consumers: int = 200,
                       n_days: int = 30,
                       hourly_records: bool = True,
                       random_seed: int = 42,
                       k_range: Tuple[int, int] = (2, 11),
                       stability_runs: int = 10,
                       output_dir: str = 'outputs/reports',
                       figures_dir: str = 'outputs/figures',
                       metrics_dir: str = 'outputs/metrics',
                       ablation_dir: Optional[str] = None) -> pd.DataFrame:
    """Run every arm and write the table, the figure and the report.

    Args:
        n_consumers: Consumers to generate.
        n_days: Days of hourly data.
        hourly_records: Hourly rather than daily records.
        random_seed: Seed shared by the generator and every fit.
        k_range: Half-open range of candidate K, the same for every arm.
        stability_runs: Restarts per K when measuring stability.
        output_dir: Directory for the report.
        figures_dir: Directory for the comparison figure.
        metrics_dir: Directory for the results table.
        ablation_dir: Root for per-arm artifacts. Defaults to a sibling
            'ablation' directory beside output_dir.

    Returns:
        The ablation table, one row per arm.
    """
    logger.info("Starting the ablation study")

    reports_path = Path(output_dir)
    ablation_root = Path(ablation_dir) if ablation_dir else reports_path.parent / 'ablation'
    for path in (reports_path, Path(figures_dir), Path(metrics_dir), ablation_root):
        path.mkdir(parents=True, exist_ok=True)

    raw = generate_synthetic_data(
        n_consumers=n_consumers,
        n_days=n_days,
        hourly_records=hourly_records,
        random_seed=random_seed,
    )

    truth_by_consumer = None
    if 'archetype' in raw.columns:
        truth_by_consumer = raw.groupby('consumer_id')['archetype'].first()
        raw = raw.drop(columns=['archetype'])
    else:
        logger.warning("No archetype column found, so the arms cannot be checked against ground truth")

    preprocessed = preprocess_pipeline(raw)
    combined_features = engineer_all_features(preprocessed, feature_set='combined')

    rows = []
    for feature_set, _ in ARMS:
        rows.append(run_one_arm(
            feature_set=feature_set,
            preprocessed=preprocessed,
            combined_features=combined_features,
            truth_by_consumer=truth_by_consumer,
            k_range=k_range,
            random_seed=random_seed,
            stability_runs=stability_runs,
            arm_root=ablation_root / feature_set,
        ))

    results = pd.DataFrame(rows)
    chosen, reasoning = choose_primary_arm(results)

    results.to_csv(Path(metrics_dir) / 'ablation_study_results.csv', index=False)
    plot_ablation_comparison(results, figures_dir)
    generate_ablation_report(results, chosen, reasoning, str(reports_path))

    logger.info(f"Ablation study completed, rule selected the {chosen} arm")
    return results


if __name__ == "__main__":
    from project_paths import anchor_to_project_root

    anchor_to_project_root()

    table = run_ablation_study()

    columns = ['arm', 'n_features', 'optimal_k', 'silhouette', 'stability_mean_ari',
               'archetype_ari', 'scale_separation', 'shape_separation']
    print("\n" + table[columns].to_string(index=False))

    arm, why = choose_primary_arm(table)
    print(f"\nSelected arm on this single dataset: {arm}")
    for line in why:
        print(line)
    print("\nThe shipped feature_set is fixed by the 20-dataset seed robustness study")
    print("(run_seed_robustness.py), not by this single draw.")
