"""
Seed Robustness Module

The ablation study compares feature sets on one generated dataset. That is enough
to show the feature set changes the answer, and not enough to decide which
feature set the pipeline should use. A single dataset gives one draw from the
generator, and the arms are close enough on that draw that the ranking can turn
over when the draw changes. It does: on seed 42 the shape arm recovers the hidden
archetypes best, and on seed 7 it is the worst of the three behavioral arms.

This module repeats the whole ablation on many independent datasets and reports
the distribution rather than a single number. Nothing here is a new model. The
arms, the K selection rule and the arm selection rule are all the ones already
written down in clustering.py and run_ablation_study.py, applied unchanged to
each dataset.

Three things come out of it:

- Per arm, the spread of archetype agreement across datasets, so a difference of
  0.03 on one dataset can be read against the sd of that difference.
- How often the pre-registered arm rule picks each arm. If the rule picks a
  different arm on half the datasets then the rule is not identifying anything
  and saying so is more useful than reporting whichever arm won once.
- Paired significance tests across datasets. Each dataset is a block: every arm
  sees the same 200 consumers, so the arms are paired and the pairing should be
  used. Friedman first, to ask whether the arms differ at all, then exact
  Wilcoxon signed-rank on every pair with a Holm correction.

The seeds are seed 42, which the primary analysis uses, followed by seeds 1 to
19. Listing them as a range rather than as chosen values is deliberate: it is not
possible to pick a favourable subset of a stated range after seeing the results.

THIS IS SYNTHETIC DATA. Archetype agreement can only be measured because the
generator wrote the answer down. On a real dataset none of these numbers exist
and the arm would have to be chosen on the shape separation diagnostic and on
whether the clusters can be interpreted.
"""

import logging
import os
from itertools import combinations

os.environ.setdefault('MPLBACKEND', 'Agg')

from pathlib import Path
from tempfile import TemporaryDirectory
from typing import Dict, List, Optional, Sequence, Tuple

import matplotlib

matplotlib.use('Agg', force=True)

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from scipy import stats

from clustering import MIN_CLUSTER_SHARE, MIN_STABILITY_ARI
from data_loader import generate_synthetic_data
from feature_engineering import engineer_all_features
from preprocessing import preprocess_pipeline
from run_ablation_study import ARM_SCORE_TOLERANCE, ARMS, choose_primary_arm, run_one_arm

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Seed 42 is the one the primary analysis uses. The rest are a plain range so no
# subset can have been chosen to suit the result.
SEEDS: Tuple[int, ...] = (42,) + tuple(range(1, 20))

# The column the arm rule decides on when ground truth exists.
CRITERION = 'archetype_ari'

# Columns carried through to the per-seed table.
TRACKED_COLUMNS: Tuple[str, ...] = (
    'n_features', 'n_pca_components', 'optimal_k', 'silhouette',
    'stability_mean_ari', 'min_cluster_share', 'archetype_ari', 'archetype_nmi',
    'scale_separation', 'shape_separation',
)

ALPHA = 0.05


def run_one_seed(seed: int,
                 n_consumers: int = 200,
                 n_days: int = 30,
                 k_range: Tuple[int, int] = (2, 11),
                 stability_runs: int = 10) -> pd.DataFrame:
    """Run every ablation arm on one generated dataset.

    Per-arm figures, models and metrics go to a temporary directory and are
    discarded. Twenty datasets times five arms would otherwise leave several
    hundred figures in the repository that nobody will ever open, and the
    canonical artifacts belong to the primary run.

    Args:
        seed: Seed for the generator and for every fit on this dataset.
        n_consumers: Consumers to generate.
        n_days: Days of hourly data.
        k_range: Half-open range of candidate K, the same for every arm.
        stability_runs: Restarts per K when measuring stability.

    Returns:
        One row per arm, with a seed column and the arm the rule selected.
    """
    logger.info(f"Seed {seed}: generating data and running {len(ARMS)} arms")

    raw = generate_synthetic_data(n_consumers=n_consumers, n_days=n_days,
                                 hourly_records=True, random_seed=seed)

    truth_by_consumer = None
    if 'archetype' in raw.columns:
        truth_by_consumer = raw.groupby('consumer_id')['archetype'].first()
        # Drop both hidden truth columns before preprocessing, mirroring
        # energy_analysis: the archetype labels and the hidden seasonal_phase
        # column must never reach the scaler, PCA or K-Means.
        raw = raw.drop(columns=['archetype', 'seasonal_phase'], errors='ignore')

    preprocessed = preprocess_pipeline(raw)
    combined_features = engineer_all_features(preprocessed, feature_set='combined')

    rows = []
    with TemporaryDirectory(prefix=f'seed_robustness_{seed}_') as scratch:
        for feature_set, _ in ARMS:
            rows.append(run_one_arm(
                feature_set=feature_set,
                preprocessed=preprocessed,
                combined_features=combined_features,
                truth_by_consumer=truth_by_consumer,
                k_range=k_range,
                random_seed=seed,
                stability_runs=stability_runs,
                arm_root=Path(scratch) / feature_set,
            ))

    results = pd.DataFrame(rows)
    chosen, _ = choose_primary_arm(results)
    results['seed'] = seed
    results['rule_selected'] = results['arm'] == chosen

    logger.info(f"Seed {seed}: the rule selected {chosen}")
    return results


def collect_seeds(seeds: Sequence[int] = SEEDS, **kwargs) -> pd.DataFrame:
    """Run every arm on every dataset and stack the results.

    Args:
        seeds: Generator seeds, one independent dataset each.
        **kwargs: Passed through to run_one_seed.

    Returns:
        Long table with one row per (seed, arm).
    """
    logger.info(f"Running {len(ARMS)} arms on {len(seeds)} datasets")

    frames = [run_one_seed(seed, **kwargs) for seed in seeds]
    long = pd.concat(frames, ignore_index=True)

    front = ['seed', 'arm', 'rule_selected']
    ordered = front + [c for c in long.columns if c not in front]
    return long[ordered]


def summarize_arms(long: pd.DataFrame, criterion: str = CRITERION) -> pd.DataFrame:
    """Aggregate each arm across datasets.

    Args:
        long: Table from collect_seeds.
        criterion: Column the arm rule decides on.

    Returns:
        One row per arm, ordered by mean criterion value, descending.
    """
    arm_order = [name for name, _ in ARMS]
    n_seeds = long['seed'].nunique()

    rows = []
    for arm in arm_order:
        block = long[long['arm'] == arm]
        values = block[criterion].to_numpy(dtype=float)
        ks = block['optimal_k'].to_numpy(dtype=int)
        rows.append({
            'arm': arm,
            'n_features': int(block['n_features'].iloc[0]),
            f'{criterion}_mean': float(np.mean(values)),
            f'{criterion}_sd': float(np.std(values, ddof=1)),
            f'{criterion}_min': float(np.min(values)),
            f'{criterion}_max': float(np.max(values)),
            'silhouette_mean': float(block['silhouette'].mean()),
            'stability_mean': float(block['stability_mean_ari'].mean()),
            'shape_separation_mean': float(block['shape_separation'].mean()),
            'scale_separation_mean': float(block['scale_separation'].mean()),
            'k_median': float(np.median(ks)),
            'k_modal': int(pd.Series(ks).mode().iat[0]),
            'k_range': f"{ks.min()} to {ks.max()}",
            'times_rule_selected': int(block['rule_selected'].sum()),
            'selection_share': float(block['rule_selected'].sum() / n_seeds),
        })

    summary = pd.DataFrame(rows)
    return summary.sort_values(f'{criterion}_mean', ascending=False).reset_index(drop=True)


def _pivot(long: pd.DataFrame, criterion: str) -> pd.DataFrame:
    """Seeds as rows, arms as columns, so the arms stay paired by dataset."""
    wide = long.pivot(index='seed', columns='arm', values=criterion)
    return wide[[name for name, _ in ARMS if name in wide.columns]]


def friedman_across_arms(long: pd.DataFrame,
                         criterion: str = CRITERION) -> Dict[str, float]:
    """Friedman test on the criterion, blocking on dataset.

    Every arm is measured on the same datasets, so the arms are paired. Friedman
    is the paired, rank-based test for more than two related groups and makes no
    assumption that the criterion is normally distributed, which matters because
    the Adjusted Rand Index is bounded above by 1 and piles up near its ceiling.

    Args:
        long: Table from collect_seeds.
        criterion: Column to test.

    Returns:
        Statistic, p-value, number of blocks and number of arms.
    """
    wide = _pivot(long, criterion).dropna()
    columns = [wide[c].to_numpy(dtype=float) for c in wide.columns]

    statistic, p_value = stats.friedmanchisquare(*columns)
    return {
        'statistic': float(statistic),
        'p_value': float(p_value),
        'n_blocks': int(len(wide)),
        'n_arms': int(wide.shape[1]),
    }


def _holm(p_values: Sequence[float]) -> List[float]:
    """Holm step-down adjustment, order preserved.

    Holm rather than Bonferroni because it controls the same family-wise error
    rate while rejecting at least as much, and rather than Benjamini-Hochberg
    because with ten tests the interesting question is whether any single pair
    survives, not what share of rejections are false.

    Args:
        p_values: Raw p-values.

    Returns:
        Adjusted p-values in the input order, each capped at 1.
    """
    n = len(p_values)
    order = sorted(range(n), key=lambda i: p_values[i])

    adjusted = [0.0] * n
    running = 0.0
    for rank, index in enumerate(order):
        candidate = (n - rank) * p_values[index]
        running = max(running, candidate)
        adjusted[index] = min(1.0, running)
    return adjusted


def pairwise_arm_tests(long: pd.DataFrame,
                       criterion: str = CRITERION) -> pd.DataFrame:
    """Exact Wilcoxon signed-rank on every pair of arms, Holm corrected.

    Every pair is tested and reported. Testing only the pair that looks
    interesting after seeing the means would make the p-value meaningless.

    Args:
        long: Table from collect_seeds.
        criterion: Column to test.

    Returns:
        One row per pair, sorted by adjusted p-value.
    """
    wide = _pivot(long, criterion).dropna()

    rows = []
    for left, right in combinations(wide.columns, 2):
        a = wide[left].to_numpy(dtype=float)
        b = wide[right].to_numpy(dtype=float)
        difference = a - b

        if np.allclose(difference, 0.0):
            statistic, p_value, method = float('nan'), 1.0, 'none, arms identical'
        else:
            # The criterion is a continuous score, so exact ties are vanishingly
            # unlikely and the exact test should apply. Falling back rather than
            # failing keeps the table complete if a pair ever does tie.
            try:
                statistic, p_value = stats.wilcoxon(a, b, method='exact')
                method = 'exact'
            except ValueError:
                statistic, p_value = stats.wilcoxon(a, b, method='auto')
                method = 'auto'

        rows.append({
            'arm_a': left,
            'arm_b': right,
            'mean_difference': float(np.mean(difference)),
            'median_difference': float(np.median(difference)),
            'wins_a': int((difference > 0).sum()),
            'wins_b': int((difference < 0).sum()),
            'ties': int((difference == 0).sum()),
            'statistic': float(statistic),
            'method': method,
            'p_raw': float(p_value),
        })

    tests = pd.DataFrame(rows)
    tests['p_holm'] = _holm(tests['p_raw'].tolist())
    tests['significant'] = tests['p_holm'] < ALPHA
    return tests.sort_values('p_holm').reset_index(drop=True)


def plot_seed_robustness(long: pd.DataFrame,
                         summary: pd.DataFrame,
                         output_dir: str = 'outputs/figures',
                         criterion: str = CRITERION) -> None:
    """Three panels: the criterion per arm, the K it picks, and how often it wins.

    Args:
        long: Table from collect_seeds.
        summary: Table from summarize_arms.
        output_dir: Directory for the figure.
        criterion: Column plotted in the first panel.
    """
    logger.info("Plotting the seed robustness comparison")

    arm_order = [name for name, _ in ARMS]
    wide = _pivot(long, criterion)
    n_seeds = len(wide)

    fig, axes = plt.subplots(1, 3, figsize=(16, 5.2))

    ax = axes[0]
    data = [wide[arm].to_numpy(dtype=float) for arm in arm_order]
    ax.boxplot(data, tick_labels=arm_order, showmeans=True, widths=0.55,
               medianprops={'color': '#c44e52'},
               meanprops={'marker': 'D', 'markerfacecolor': '#4c72b0',
                          'markeredgecolor': '#4c72b0', 'markersize': 5})
    # Deterministic offsets rather than random jitter, so the figure is
    # byte-identical on a rerun.
    offsets = np.linspace(-0.22, 0.22, n_seeds)
    for position, arm in enumerate(arm_order, start=1):
        ax.scatter(position + offsets, wide[arm].to_numpy(dtype=float),
                   s=14, alpha=0.55, color='#555555', zorder=3)
    ax.axhline(0.0, color='#999999', linewidth=0.8, linestyle=':')
    ax.set_ylabel('Adjusted Rand Index against hidden archetypes')
    ax.set_title(f'Archetype agreement over {n_seeds} datasets')
    ax.tick_params(axis='x', rotation=20)

    ax = axes[1]
    ks = long.pivot(index='seed', columns='arm', values='optimal_k')[arm_order]
    k_values = sorted(long['optimal_k'].unique())
    counts = np.array([[int((ks[arm] == k).sum()) for k in k_values] for arm in arm_order])
    image = ax.imshow(counts, cmap='Blues', aspect='auto', vmin=0, vmax=n_seeds)
    ax.set_xticks(range(len(k_values)), [str(k) for k in k_values])
    ax.set_yticks(range(len(arm_order)), arm_order)
    ax.set_xlabel('K selected by the rule')
    ax.set_title('How often each arm lands on each K')
    for i in range(counts.shape[0]):
        for j in range(counts.shape[1]):
            if counts[i, j]:
                ax.text(j, i, str(counts[i, j]), ha='center', va='center',
                        fontsize=9,
                        color='white' if counts[i, j] > n_seeds / 2 else '#333333')
    fig.colorbar(image, ax=ax, label='datasets')

    ax = axes[2]
    ordered = summary.set_index('arm').reindex(arm_order)
    ax.barh(arm_order, ordered['times_rule_selected'], color='#4c72b0')
    ax.set_xlabel(f'datasets where the rule chose this arm (of {n_seeds})')
    ax.set_title('Arm selected by the pre-registered rule')
    ax.set_xlim(0, n_seeds)
    for position, value in enumerate(ordered['times_rule_selected']):
        ax.text(value + 0.15, position, str(int(value)), va='center', fontsize=9)
    ax.invert_yaxis()

    fig.suptitle('Feature set comparison across independent synthetic datasets',
                 fontsize=13)
    fig.tight_layout()

    path = Path(output_dir)
    path.mkdir(parents=True, exist_ok=True)
    fig.savefig(path / 'seed_robustness.png', dpi=200, bbox_inches='tight')
    plt.close(fig)
    logger.info(f"Saved the seed robustness figure to {path / 'seed_robustness.png'}")


def choose_arm_on_pooled_evidence(long: pd.DataFrame,
                                  summary: pd.DataFrame,
                                  tests: pd.DataFrame,
                                  criterion: str = CRITERION) -> Tuple[str, List[str]]:
    """Apply the pre-registered arm rule to all datasets at once.

    run_ablation_study applies the same rule to a single dataset, which is what
    it can do with one dataset in hand. That turns out not to be enough: the rule
    picks different arms on different draws, so a single-dataset selection is a
    property of the draw. The rule itself is unchanged here. The only difference
    is that step 2 ranks arms on their mean across datasets instead of on one
    value, and step 1 has to say what "passes the filter" means when there are
    many datasets to pass it on.

    Step 1 is reported under both readings, all datasets and a majority of them,
    so the choice between them cannot quietly carry the decision.

    Args:
        long: Table from collect_seeds.
        summary: Table from summarize_arms.
        tests: Table from pairwise_arm_tests, used to say whether the winning
            margin is actually supported.
        criterion: Column the rule decides on.

    Returns:
        Tuple of (chosen arm, markdown lines generated from the numbers).
    """
    lines: List[str] = []
    n_seeds = long['seed'].nunique()
    mean_column = f'{criterion}_mean'

    passes = long.assign(
        ok=(long['stability_mean_ari'] >= MIN_STABILITY_ARI)
        & (long['min_cluster_share'] >= MIN_CLUSTER_SHARE)
    ).groupby('arm')['ok'].sum()

    strict = {arm for arm, count in passes.items() if count == n_seeds}
    lenient = {arm for arm, count in passes.items() if count > n_seeds / 2}

    lines.append(
        f"- Step 1 filtered on stability ARI at least {MIN_STABILITY_ARI} and a smallest "
        f"cluster of at least {MIN_CLUSTER_SHARE:.0%}. Datasets passed per arm: "
        + ", ".join(f"{arm} {int(count)}/{n_seeds}" for arm, count in passes.items()) + "."
    )
    if strict == lenient:
        lines.append(
            "  Requiring every dataset and requiring a majority give the same set, so "
            "nothing rests on which reading is used."
        )
        qualified_arms = strict
    else:
        lines.append(
            "  The two readings disagree: requiring every dataset admits "
            f"{sorted(strict)}, a majority admits {sorted(lenient)}. The stricter "
            "reading is used, and the difference is stated here because it affects "
            "which arms reach step 2."
        )
        qualified_arms = strict

    qualified = summary[summary['arm'].isin(qualified_arms)]
    if qualified.empty:
        lines.append("- No arm survived step 1, so the rule cannot select one.")
        return 'none', lines

    best_value = float(qualified[mean_column].max())
    tied = qualified[qualified[mean_column] >= best_value - ARM_SCORE_TOLERANCE]

    lines.append(
        f"- Step 2 ranked the survivors on mean {criterion} across {n_seeds} datasets. "
        f"The best value is {best_value:.4f}, from "
        f"{qualified.loc[qualified[mean_column].idxmax(), 'arm']}."
    )

    if len(tied) == 1:
        chosen_row = tied.iloc[0]
        lines.append(
            f"- Step 3 found no other arm within {ARM_SCORE_TOLERANCE} of that value, so "
            f"the parsimony tie-break does not apply and {chosen_row['arm']} is selected "
            f"outright with mean {criterion} {best_value:.4f}."
        )
    else:
        chosen_row = tied.loc[tied['n_features'].idxmin()]
        lines.append(
            f"- Step 3 treated {len(tied)} arms as tied within {ARM_SCORE_TOLERANCE} ("
            + ", ".join(f"{row['arm']} {int(row['n_features'])} features"
                        for _, row in tied.iterrows())
            + f") and preferred the smallest, {chosen_row['arm']}."
        )

    chosen = str(chosen_row['arm'])

    best_silhouette = summary.loc[summary['silhouette_mean'].idxmax()]
    if str(best_silhouette['arm']) != chosen:
        lines.append(
            f"- Step 4, for the record: {best_silhouette['arm']} has the highest mean "
            f"silhouette ({best_silhouette['silhouette_mean']:.4f} against "
            f"{float(chosen_row['silhouette_mean']):.4f} for {chosen}). Silhouette did "
            f"not decide the choice."
        )

    # The rule produces a decision. Whether the margin behind it is supported is a
    # separate question, and answering it in the same place stops the decision from
    # being read as a demonstration.
    rivals = [row['arm'] for _, row in qualified.iterrows() if row['arm'] != chosen]
    against_chosen = tests[
        ((tests['arm_a'] == chosen) & (tests['arm_b'].isin(rivals)))
        | ((tests['arm_b'] == chosen) & (tests['arm_a'].isin(rivals)))
    ]
    beaten = against_chosen[against_chosen['significant']]
    lines.append("")
    lines.append(
        f"The rule selects {chosen}. Of the {len(against_chosen)} pairwise tests "
        f"involving it, {len(beaten)} reject the hypothesis that the two arms perform "
        f"alike after Holm correction"
        + (": " + ", ".join(
            f"against {row['arm_b'] if row['arm_a'] == chosen else row['arm_a']} "
            f"(adjusted p {row['p_holm']:.3g})"
            for _, row in beaten.iterrows()) + "."
           if len(beaten) else ".")
    )

    unbeaten = against_chosen[~against_chosen['significant']]
    if len(unbeaten):
        lines.append(
            f"The remaining {len(unbeaten)} are not separated by the evidence: "
            + ", ".join(
                f"{row['arm_b'] if row['arm_a'] == chosen else row['arm_a']} "
                f"(adjusted p {row['p_holm']:.3g})"
                for _, row in unbeaten.iterrows())
            + f". So {chosen} is the arm the rule returns and the arm with the best mean, "
            f"but it has not been shown to beat those. Reporting it as the demonstrated "
            f"best feature set would overstate the result."
        )

    return chosen, lines


def _verdict_lines(summary: pd.DataFrame,
                   tests: pd.DataFrame,
                   friedman: Dict[str, float],
                   criterion: str) -> List[str]:
    """State what the numbers support about the arm choice, and what they do not."""
    best = summary.iloc[0]
    runner_up = summary.iloc[1]
    n_seeds = friedman['n_blocks']

    lines = [
        f"Ranked on mean {criterion}, the order is "
        + ", ".join(f"{row['arm']} {row[f'{criterion}_mean']:.4f}"
                    for _, row in summary.iterrows()) + ".",
        "",
    ]

    if friedman['p_value'] < ALPHA:
        lines.append(
            f"Friedman rejects the hypothesis that all {friedman['n_arms']} arms perform "
            f"alike (statistic {friedman['statistic']:.3f}, p {friedman['p_value']:.3g} "
            f"over {n_seeds} datasets), so the arms are not interchangeable."
        )
    else:
        lines.append(
            f"Friedman does not reject the hypothesis that the arms perform alike "
            f"(statistic {friedman['statistic']:.3f}, p {friedman['p_value']:.3g} over "
            f"{n_seeds} datasets). On this evidence the feature set does not measurably "
            f"change archetype agreement, and any ranking below is within noise."
        )
    lines.append("")

    pair = tests[
        ((tests['arm_a'] == best['arm']) & (tests['arm_b'] == runner_up['arm']))
        | ((tests['arm_a'] == runner_up['arm']) & (tests['arm_b'] == best['arm']))
    ]
    if len(pair):
        row = pair.iloc[0]
        gap = abs(row['mean_difference'])
        if row['significant']:
            lines.append(
                f"The gap between the top two arms, {best['arm']} and {runner_up['arm']}, "
                f"survives correction: mean difference {gap:.4f}, Holm-adjusted p "
                f"{row['p_holm']:.3g}. The better arm wins on "
                f"{max(row['wins_a'], row['wins_b'])} of {n_seeds} datasets."
            )
        else:
            lines.append(
                f"The gap between the top two arms, {best['arm']} and {runner_up['arm']}, "
                f"does not survive correction: mean difference {gap:.4f}, Holm-adjusted p "
                f"{row['p_holm']:.3g}, with the leader ahead on only "
                f"{max(row['wins_a'], row['wins_b'])} of {n_seeds} datasets. Choosing "
                f"between those two on this evidence is not supported."
            )
        lines.append("")

    winners = summary[summary['times_rule_selected'] > 0]
    if len(winners) > 1:
        lines.append(
            f"The pre-registered arm rule did not settle on one answer either. Over "
            f"{n_seeds} datasets it selected "
            + ", ".join(f"{row['arm']} {int(row['times_rule_selected'])} times"
                        for _, row in winners.iterrows())
            + ". A rule that changes its mind between draws of the same generator is not"
            " identifying a property of the feature sets, and reporting the arm that won"
            " once would overstate what was measured."
        )
    else:
        lines.append(
            f"The pre-registered arm rule selected {winners.iloc[0]['arm']} on all "
            f"{n_seeds} datasets, so the choice is not an artifact of the seed."
        )
    lines.append("")

    return lines


def generate_seed_robustness_report(long: pd.DataFrame,
                                    summary: pd.DataFrame,
                                    tests: pd.DataFrame,
                                    friedman: Dict[str, float],
                                    output_dir: str = 'outputs/reports',
                                    criterion: str = CRITERION) -> str:
    """Write the seed robustness report as markdown.

    Args:
        long: Table from collect_seeds.
        summary: Table from summarize_arms.
        tests: Table from pairwise_arm_tests.
        friedman: Result from friedman_across_arms.
        output_dir: Directory for the report.
        criterion: Column the comparison decides on.

    Returns:
        The arm the pooled rule selected.
    """
    logger.info("Writing the seed robustness report")

    n_seeds = friedman['n_blocks']
    seeds = sorted(long['seed'].unique())

    summary_columns = [
        'arm', 'n_features', f'{criterion}_mean', f'{criterion}_sd',
        f'{criterion}_min', f'{criterion}_max', 'silhouette_mean',
        'stability_mean', 'shape_separation_mean', 'k_modal', 'k_range',
        'times_rule_selected',
    ]
    test_columns = ['arm_a', 'arm_b', 'mean_difference', 'wins_a', 'wins_b',
                    'ties', 'method', 'p_raw', 'p_holm', 'significant']

    lines = [
        "# Seed Robustness of the Feature Set Choice",
        "",
        "THIS IS SYNTHETIC DATA. Agreement with the hidden archetypes can only be",
        "measured because the generator recorded which archetype each consumer was drawn",
        "from. None of these numbers exist on a real dataset.",
        "",
        "## Why this exists",
        "",
        "The ablation study compares feature sets on one generated dataset. That is",
        "enough to show the feature set changes what the clustering finds. It is not",
        "enough to decide which feature set to use, because a single dataset is a single",
        "draw and the arms are close enough that the ranking can turn over between draws.",
        "",
        f"Here the same {len(ARMS)} arms, the same K selection rule and the same arm",
        f"selection rule are applied unchanged to {n_seeds} independent datasets, each",
        "with its own generator seed. Nothing is refitted or retuned per dataset.",
        "",
        f"Seeds: {', '.join(str(s) for s in seeds)}. Seed 42 is the one the primary",
        "analysis uses; the rest are a plain range, so no favourable subset can have been",
        "chosen after the fact.",
        "",
        "## Per-arm results across datasets",
        "",
        summary[[c for c in summary_columns if c in summary.columns]].to_string(index=False),
        "",
        "### Reading the columns",
        "",
        f"- {criterion}_mean, _sd, _min, _max: agreement with the hidden archetypes,",
        "  summarized over datasets. The sd is the number to read a single-dataset gap",
        "  against.",
        "- silhouette_mean, stability_mean: internal quality and restart stability,",
        "  averaged over datasets, at whichever K the rule chose on each.",
        "- shape_separation_mean: how strongly the arm sorted consumers by the shape of",
        "  their day rather than by how much they used.",
        "- k_modal, k_range: the K the rule most often chose, and the full spread. An arm",
        "  whose K moves between datasets is describing a less stable structure.",
        "- times_rule_selected: datasets on which the pre-registered arm rule picked this",
        f"  arm, out of {n_seeds}.",
        "",
        "## Does the feature set matter at all",
        "",
        f"Friedman test on {criterion}, blocking on dataset: statistic "
        f"{friedman['statistic']:.4f}, p {friedman['p_value']:.4g}, "
        f"{friedman['n_blocks']} blocks, {friedman['n_arms']} arms.",
        "",
        "## Pairwise comparisons",
        "",
        "Wilcoxon signed-rank on every pair, Holm corrected across all "
        f"{len(tests)} tests. Every pair is listed, not only the interesting ones. The",
        "method column records whether the exact distribution was used.",
        "",
        tests[test_columns].to_string(index=False),
        "",
        "wins_a and wins_b count the datasets on which each arm of the pair came out",
        "ahead. A large mean difference carried by a minority of datasets is a different",
        "finding from a small one that holds on almost all of them, and the two columns",
        "are there so those cases can be told apart.",
        "",
        "## Which arm the project uses",
        "",
        "The pre-registered arm rule, applied to all of these datasets at once rather",
        "than to one of them.",
        "",
    ]
    chosen, decision_lines = choose_arm_on_pooled_evidence(long, summary, tests, criterion)
    lines += decision_lines
    lines += [
        "",
        f"The pipeline's feature_set is therefore {chosen}, and the ablation study's",
        "single-dataset selection is superseded by this one wherever the two disagree.",
        "",
        "## What this supports",
        "",
    ]
    lines += _verdict_lines(summary, tests, friedman, criterion)
    lines += [
        "## Limits",
        "",
        f"{n_seeds} datasets from one generator is not {n_seeds} datasets from the world.",
        "Every draw shares the same four archetypes, the same noise model and the same",
        "200 consumers over 30 days, so this measures how much the arm ranking moves",
        "under resampling of that generator and nothing wider. A feature set that wins",
        "here has been shown to suit this generator, which is a weaker claim than suiting",
        "household electricity data.",
        "",
        "The tests are paired across datasets, which is the right structure, but the",
        f"blocks are {n_seeds} draws from one process rather than independent studies, so",
        "the p-values describe sampling variation inside the simulation.",
        "",
        "Archetype agreement is used as the criterion because the labels exist. It is not",
        "available on real data, and an arm cannot be chosen this way outside a",
        "simulation. The shape separation column is reported for exactly that reason: it",
        "is the diagnostic that survives the move to real data.",
        "",
    ]

    path = Path(output_dir)
    path.mkdir(parents=True, exist_ok=True)
    (path / 'seed_robustness_report.md').write_text("\n".join(lines), encoding='utf-8')
    logger.info(f"Seed robustness report saved to {path / 'seed_robustness_report.md'}")
    return chosen


def run_seed_robustness(seeds: Sequence[int] = SEEDS,
                        n_consumers: int = 200,
                        n_days: int = 30,
                        k_range: Tuple[int, int] = (2, 11),
                        stability_runs: int = 10,
                        output_dir: str = 'outputs/reports',
                        figures_dir: str = 'outputs/figures',
                        metrics_dir: str = 'outputs/metrics'
                        ) -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, Dict[str, float], str]:
    """Run every arm on every dataset, then write the tables, figure and report.

    Args:
        seeds: Generator seeds, one independent dataset each.
        n_consumers: Consumers per dataset.
        n_days: Days of hourly data per dataset.
        k_range: Half-open range of candidate K.
        stability_runs: Restarts per K when measuring stability.
        output_dir: Directory for the report.
        figures_dir: Directory for the figure.
        metrics_dir: Directory for the tables.

    Returns:
        Tuple of (per-seed table, per-arm summary, pairwise tests, Friedman result,
        arm selected on the pooled evidence).
    """
    logger.info("Starting the seed robustness study")

    long = collect_seeds(seeds, n_consumers=n_consumers, n_days=n_days,
                         k_range=k_range, stability_runs=stability_runs)
    summary = summarize_arms(long)
    friedman = friedman_across_arms(long)
    tests = pairwise_arm_tests(long)

    metrics_path = Path(metrics_dir)
    metrics_path.mkdir(parents=True, exist_ok=True)
    long.to_csv(metrics_path / 'seed_robustness_by_seed.csv', index=False)
    summary.to_csv(metrics_path / 'seed_robustness_summary.csv', index=False)
    tests.to_csv(metrics_path / 'seed_robustness_tests.csv', index=False)

    plot_seed_robustness(long, summary, figures_dir)
    chosen = generate_seed_robustness_report(long, summary, tests, friedman, output_dir)

    logger.info(f"Seed robustness study completed, pooled rule selected {chosen}")
    return long, summary, tests, friedman, chosen


if __name__ == "__main__":
    from project_paths import anchor_to_project_root

    anchor_to_project_root()

    long, summary, tests, friedman, chosen = run_seed_robustness()

    print("\nPer-arm summary across datasets:")
    print(summary.to_string(index=False))
    print(f"\nFriedman: statistic {friedman['statistic']:.4f}, p {friedman['p_value']:.4g}")
    print("\nPairwise tests:")
    print(tests.to_string(index=False))
    print(f"\nArm selected on the pooled evidence: {chosen}")
