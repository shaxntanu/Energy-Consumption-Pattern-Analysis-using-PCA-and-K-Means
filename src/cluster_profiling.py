"""
Cluster Profiling Module

Describes each cluster in the original feature units, always next to the
population baseline. A cluster mean on its own is not interpretable: 0.31 of
daily energy in the evening only means something once you know the population
figure is 0.26.

Two rules are applied throughout:

- Profiling reports behaviour first and magnitude second. Magnitude is included
  because it is useful context, but it did not take part in the behavioral
  clustering and is never used to name a cluster.
- Names are derived from measured quantities (peak hour of the cluster mean load
  shape, flatness, weekend ratio against the population). Clusters keep integer
  IDs internally; the name is a label for reading, not a key.
"""

import json
import logging
from pathlib import Path
from typing import Dict, Optional, Tuple

import numpy as np
import pandas as pd

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

SHAPE_COLUMNS = [f'hour_{h}_shape' for h in range(24)]

# Profile column -> source feature column. Only entries whose source exists in
# the supplied feature frame are reported.
PROFILE_METRICS: Dict[str, str] = {
    'morning_share': 'morning_share',
    'afternoon_share': 'afternoon_share',
    'evening_share': 'evening_share',
    'night_share': 'night_share',
    'night_day_ratio': 'night_day_ratio',
    'peak_concentration': 'peak_concentration',
    'profile_ramp': 'profile_ramp',
    'weekend_ratio': 'weekend_ratio',
    'weekend_shape_distance': 'weekend_shape_distance',
    'peak_to_avg_ratio': 'peak_to_avg_ratio',
    'coefficient_of_variation': 'coefficient_of_variation',
    'mean_kwh': 'energy_consumption_kwh_mean',
    'max_kwh': 'energy_consumption_kwh_max',
    'total_kwh': 'energy_consumption_kwh_sum',
}

# Metrics whose deviation from the population is worth reporting as a column.
COMPARED_METRICS = [
    'morning_share', 'afternoon_share', 'evening_share', 'night_share',
    'weekend_ratio', 'peak_to_avg_ratio', 'coefficient_of_variation', 'mean_kwh',
]

PERIOD_LABELS = {
    'night': 'Night-Peaking',
    'morning': 'Morning-Peaking',
    'afternoon': 'Midday-Peaking',
    'evening': 'Evening-Peaking',
}

# A perfectly flat 24-hour profile puts 3/24 = 0.125 of its energy in its three
# busiest hours. Anything below this stays close enough to flat that naming it
# after a peak hour would overstate what the data shows.
FLAT_CONCENTRATION_LIMIT = 0.16

# Relative gaps against the population before a qualifier is added to a name.
WEEKEND_HIGH = 1.10
WEEKEND_LOW = 0.90


def _period_of_hour(hour: int) -> str:
    """Map an hour of day to its period block."""
    if 0 <= hour < 6:
        return 'night'
    if 6 <= hour < 12:
        return 'morning'
    if 12 <= hour < 18:
        return 'afternoon'
    return 'evening'


def cluster_load_shapes(features: pd.DataFrame, labels: np.ndarray) -> pd.DataFrame:
    """Mean normalized 24-hour load shape per cluster, plus the population mean.

    Args:
        features: Per-consumer feature frame containing the hour_<h>_shape columns.
        labels: Cluster label per row, in the same order as features.

    Returns:
        DataFrame indexed by cluster ID with 24 columns named 0..23. The
        population mean is included under the index label 'population'.
    """
    available = [c for c in SHAPE_COLUMNS if c in features.columns]
    if len(available) != 24:
        raise ValueError(
            f"Expected 24 shape columns for load-shape profiling, found {len(available)}"
        )

    shapes = features[available].copy()
    shapes.columns = list(range(24))

    by_cluster = shapes.groupby(np.asarray(labels)).mean()
    by_cluster.index.name = 'cluster'

    population = shapes.mean().to_frame().T
    population.index = ['population']

    return pd.concat([by_cluster, population])


def population_baseline(features: pd.DataFrame) -> Dict[str, float]:
    """Population mean of every profile metric present in the feature frame.

    This is the mean over consumers, not the median of the cluster means. The
    median of cluster means changes when clusters change size and is not a
    property of the population.

    Args:
        features: Per-consumer feature frame.

    Returns:
        Mapping of profile metric name to population mean.
    """
    baseline = {
        name: float(features[source].mean())
        for name, source in PROFILE_METRICS.items()
        if source in features.columns
    }

    shape_columns = [c for c in SHAPE_COLUMNS if c in features.columns]
    if len(shape_columns) == 24:
        mean_shape = features[shape_columns].mean().to_numpy()
        baseline['peak_hour'] = float(int(np.argmax(mean_shape)))

    baseline['size'] = float(len(features))
    return baseline


def profile_clusters(features: pd.DataFrame,
                     labels: np.ndarray) -> Tuple[pd.DataFrame, Dict[str, float]]:
    """Summarize every cluster in original feature units against the population.

    Args:
        features: Per-consumer feature frame, ideally the combined set so that
            magnitude context is available alongside behaviour.
        labels: Cluster label per row, in the same order as features.

    Returns:
        Tuple of (profiles frame, population baseline dict). The profiles frame
        has one row per cluster and, for the metrics in COMPARED_METRICS, an
        extra <metric>_vs_population column holding the cluster value divided by
        the population value.
    """
    labels = np.asarray(labels)
    if len(labels) != len(features):
        raise ValueError(
            f"Got {len(labels)} labels for {len(features)} consumers; they must match"
        )

    logger.info(f"Profiling {len(np.unique(labels))} clusters over {len(features)} consumers")

    baseline = population_baseline(features)
    shape_columns = [c for c in SHAPE_COLUMNS if c in features.columns]
    has_shape = len(shape_columns) == 24

    rows = []
    for cluster_id in sorted(np.unique(labels)):
        members = features[labels == cluster_id]

        row = {
            'cluster': int(cluster_id),
            'size': int(len(members)),
            'size_share': float(len(members) / len(features)),
        }

        if has_shape:
            mean_shape = members[shape_columns].mean().to_numpy()
            row['peak_hour'] = int(np.argmax(mean_shape))

        for name, source in PROFILE_METRICS.items():
            if source in members.columns:
                row[name] = float(members[source].mean())

        for name in COMPARED_METRICS:
            if name in row and baseline.get(name):
                row[f'{name}_vs_population'] = float(row[name] / baseline[name])

        rows.append(row)

    profiles = pd.DataFrame(rows)
    logger.info(f"Profiled clusters with sizes {profiles['size'].tolist()}")
    return profiles, baseline


def name_cluster(profile: dict, baseline: Optional[Dict[str, float]] = None) -> str:
    """Build a readable name from the measured behaviour of one cluster.

    The name answers "when does this group use energy, and how evenly", because
    that is what the behavioral features encode. It deliberately says nothing
    about how much energy the group uses: magnitude was excluded from the
    clustering, so putting it in the name would misdescribe the result.

    Args:
        profile: One row of the profiles frame as a dictionary.
        baseline: Population baseline. Without it, only the flatness and peak
            hour parts of the name can be built.

    Returns:
        Name string, for example "Evening-Peaking Weekend-Heavy".
    """
    baseline = baseline or {}
    parts = []

    concentration = profile.get('peak_concentration')
    peak_hour = profile.get('peak_hour')

    is_flat = concentration is not None and float(concentration) < FLAT_CONCENTRATION_LIMIT

    if is_flat:
        parts.append('Flat All-Day')
    elif peak_hour is not None and not pd.isna(peak_hour):
        parts.append(PERIOD_LABELS[_period_of_hour(int(peak_hour))])
    else:
        parts.append('Unclassified-Timing')

    ratio = profile.get('weekend_ratio')
    reference = baseline.get('weekend_ratio')
    if ratio is not None and reference:
        relative = float(ratio) / float(reference)
        if relative >= WEEKEND_HIGH:
            parts.append('Weekend-Heavy')
        elif relative <= WEEKEND_LOW:
            parts.append('Weekday-Heavy')

    return ' '.join(parts)


def _describe(label: str, value: float, reference: Optional[float], unit: str = '') -> str:
    """Format one metric next to its population value."""
    if reference is None or not np.isfinite(reference) or reference == 0:
        return f"{label} {value:.3f}{unit}"
    return f"{label} {value:.3f}{unit} against a population {reference:.3f}{unit}"


def interpret_cluster(profile: dict, baseline: Optional[Dict[str, float]] = None) -> str:
    """Describe a cluster in plain sentences, each backed by a number.

    Every clause states a measured value and the population value it is being
    compared with, so the description can be checked against the profile table.

    Args:
        profile: One row of the profiles frame as a dictionary.
        baseline: Population baseline.

    Returns:
        Multi-sentence description.
    """
    baseline = baseline or {}
    sentences = []

    size = profile.get('size')
    share = profile.get('size_share')
    if size is not None and share is not None:
        sentences.append(f"Holds {int(size)} consumers, {share:.1%} of the population.")

    peak_hour = profile.get('peak_hour')
    concentration = profile.get('peak_concentration')
    if peak_hour is not None and not pd.isna(peak_hour):
        if concentration is not None and float(concentration) < FLAT_CONCENTRATION_LIMIT:
            sentences.append(
                f"The mean load shape is close to flat: its three busiest hours hold "
                f"{float(concentration):.1%} of daily energy, against "
                f"{baseline.get('peak_concentration', float('nan')):.1%} for the population, "
                f"so the nominal peak at hour {int(peak_hour)} is weak."
            )
        else:
            sentences.append(
                f"The mean load shape peaks at hour {int(peak_hour)}, with "
                f"{float(concentration):.1%} of daily energy in its three busiest hours."
            )

    shares = {
        period: profile.get(f'{period}_share')
        for period in ('night', 'morning', 'afternoon', 'evening')
    }
    shares = {k: v for k, v in shares.items() if v is not None}
    if shares:
        strongest = max(shares, key=lambda k: shares[k])
        sentences.append(
            "Period shares are " + ", ".join(
                f"{period} {value:.1%}" for period, value in shares.items()
            ) + f"; {strongest} is the largest."
        )

    ratio = profile.get('weekend_ratio')
    reference = baseline.get('weekend_ratio')
    if ratio is not None:
        direction = "more" if reference and ratio > reference else "less"
        sentences.append(
            "Weekend energy is " + f"{float(ratio):.2f}" +
            " times weekday energy" +
            (f", {direction} weekend-oriented than the population figure of {reference:.2f}."
             if reference else ".")
        )

    cv = profile.get('coefficient_of_variation')
    p2a = profile.get('peak_to_avg_ratio')
    if cv is not None and p2a is not None:
        sentences.append(
            "Hour-to-hour variability is " +
            _describe("a coefficient of variation of", float(cv), baseline.get('coefficient_of_variation')) +
            ", and " +
            _describe("a peak-to-average ratio of", float(p2a), baseline.get('peak_to_avg_ratio')) + "."
        )

    mean_kwh = profile.get('mean_kwh')
    if mean_kwh is not None:
        sentences.append(
            "For context only, since magnitude was not clustered on: " +
            _describe("mean consumption", float(mean_kwh), baseline.get('mean_kwh'), " kWh per record") + "."
        )

    return " ".join(sentences)


def save_cluster_profiles(profiles: pd.DataFrame,
                          baseline: Dict[str, float],
                          output_dir: str = 'outputs/reports') -> pd.DataFrame:
    """Add names to the profiles frame and write it out with the baseline.

    Args:
        profiles: Frame from profile_clusters.
        baseline: Population baseline from profile_clusters.
        output_dir: Directory for the CSV and JSON files.

    Returns:
        The profiles frame with a cluster_name column inserted after cluster.
    """
    logger.info("Saving cluster profiles")

    path = Path(output_dir)
    path.mkdir(parents=True, exist_ok=True)

    named = profiles.copy()
    named['cluster_name'] = named.apply(lambda row: name_cluster(row.to_dict(), baseline), axis=1)

    columns = ['cluster', 'cluster_name'] + [c for c in named.columns
                                             if c not in ('cluster', 'cluster_name')]
    named = named[columns]

    duplicates = named['cluster_name'].duplicated(keep=False)
    if duplicates.any():
        # Two clusters can legitimately share a description. Numbering keeps the
        # labels unique for display without pretending they differ behaviourally.
        logger.warning("Some clusters share a name; appending the cluster ID to keep labels unique")
        named.loc[duplicates, 'cluster_name'] = (
            named.loc[duplicates, 'cluster_name'] + ' ' +
            named.loc[duplicates, 'cluster'].astype(str)
        )

    named.to_csv(path / 'cluster_profiles.csv', index=False)
    (path / 'population_baseline.json').write_text(
        json.dumps(baseline, indent=2), encoding='utf-8'
    )

    logger.info(f"Cluster profiles saved to {path}")
    return named


def save_cluster_insights(profiles: pd.DataFrame,
                          baseline: Dict[str, float],
                          output_dir: str = 'outputs/reports') -> pd.DataFrame:
    """Write the per-cluster descriptions.

    Args:
        profiles: Named profiles frame.
        baseline: Population baseline.
        output_dir: Directory for the CSV file.

    Returns:
        DataFrame with cluster, cluster_name and interpretation.
    """
    logger.info("Generating cluster insights")

    path = Path(output_dir)
    path.mkdir(parents=True, exist_ok=True)

    insights = pd.DataFrame([
        {
            'cluster': int(row['cluster']),
            'cluster_name': row.get('cluster_name', f"Cluster {int(row['cluster'])}"),
            'interpretation': interpret_cluster(row.to_dict(), baseline),
        }
        for _, row in profiles.iterrows()
    ])

    insights.to_csv(path / 'cluster_insights.csv', index=False)
    logger.info(f"Cluster insights saved to {path}")
    return insights


def run_cluster_profiling(features: pd.DataFrame,
                          labels: np.ndarray,
                          output_dir: str = 'outputs/reports',
                          metrics_dir: Optional[str] = None
                          ) -> Tuple[pd.DataFrame, pd.DataFrame, Dict[str, float]]:
    """Profile, name and describe every cluster, and write the artifacts.

    Args:
        features: Per-consumer feature frame. Pass the combined set so that
            magnitude context is reported alongside behaviour.
        labels: Cluster label per row, in the same order as features.
        output_dir: Directory for the report CSV and JSON files.
        metrics_dir: Directory for the cluster load-shape table. Defaults to a
            sibling 'metrics' directory next to output_dir.

    Returns:
        Tuple of (named profiles frame, insights frame, population baseline).
    """
    logger.info("Starting cluster profiling pipeline")

    profiles, baseline = profile_clusters(features, labels)
    named = save_cluster_profiles(profiles, baseline, output_dir)
    insights = save_cluster_insights(named, baseline, output_dir)

    metrics_path = Path(metrics_dir) if metrics_dir else Path(output_dir).parent / 'metrics'
    metrics_path.mkdir(parents=True, exist_ok=True)
    try:
        shapes = cluster_load_shapes(features, labels)
        shapes.to_csv(metrics_path / 'cluster_load_shapes.csv', index_label='cluster')
    except ValueError as error:
        logger.warning(f"Skipping cluster load-shape table: {error}")

    logger.info("Cluster profiling pipeline completed")
    return named, insights, baseline


if __name__ == "__main__":
    from project_paths import anchor_to_project_root

    anchor_to_project_root()

    from clustering import run_clustering_pipeline
    from data_loader import generate_synthetic_data
    from feature_engineering import engineer_all_features, select_features
    from pca_analysis import run_pca_pipeline
    from preprocessing import preprocess_pipeline

    raw = generate_synthetic_data(n_consumers=200, n_days=30, hourly_records=True)
    preprocessed = preprocess_pipeline(raw.drop(columns=['archetype']))
    behavioral = select_features(
        engineer_all_features(preprocessed, feature_set='behavioral'),
        feature_group='behavioral',
    )

    X_pca, pca, scaler, n_components = run_pca_pipeline(behavioral)
    clustering = run_clustering_pipeline(X_pca, test_stability=False)

    combined = engineer_all_features(preprocessed, feature_set='combined')
    profiles, insights, baseline = run_cluster_profiling(combined, clustering.labels)

    print(f"\nSelected K: {clustering.optimal_k}")
    print("\nCluster profiles:")
    print(profiles.to_string(index=False))
    print("\nCluster descriptions:")
    for _, row in insights.iterrows():
        print(f"\nCluster {row['cluster']} - {row['cluster_name']}")
        print(f"  {row['interpretation']}")
