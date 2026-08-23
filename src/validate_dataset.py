"""
Dataset Validation Module

Checks whether the generated dataset actually contains the structure the
generator was designed to put in. Three questions:

1. Are the four archetypes distinguishable by the shape of their load, and by how
   much? Not "do they look different on a plot" but a number: between-archetype
   spread against within-archetype spread.
2. Does magnitude leak archetype identity? The generator draws each consumer's
   amplitude from the same distribution regardless of archetype, so a consumer's
   mean kWh should carry no information about which archetype it came from. If it
   does, the ablation study comparing behavioral against scale features is
   measuring the wrong thing.
3. Does each behavioral feature carry any of that structure? Standardization gives
   every feature the same weight in the distance K-Means measures, so a feature
   that carries nothing is not free.

Everything here is measured from the data. Nothing is asserted about the
generator that is not computed from its output, because the two can drift apart:
an earlier version of this file described perturbation strengths and amplitude
ranges that the generator had stopped using.

THIS IS SYNTHETIC DATA. The archetype column exists only because the data was
generated. It is dropped before preprocessing and never reaches the scaler, PCA
or K-Means. On a real dataset none of the checks below are available.
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
import seaborn as sns

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

sns.set_style('whitegrid')

ARCHETYPE_COL = 'archetype'
ENERGY_COL = 'energy_consumption_kwh'

# Below this, a between-archetype distance is not meaningfully larger than the
# scatter of consumers around their own archetype mean.
DISTINCT_RATIO_FLOOR = 1.0

# An eta squared above this on mean kWh would mean magnitude carries archetype
# information, which the generator is designed to avoid.
MAGNITUDE_LEAK_LIMIT = 0.05

# Below this, a single feature explains so little of the archetype structure that
# it is worth naming in the report. It is a reporting threshold, not a filter: no
# feature is dropped on the strength of a statistic computed from the labels.
WEAK_FEATURE_ETA = 0.05


def consumer_normalized_shapes(df: pd.DataFrame) -> Tuple[pd.DataFrame, pd.Series]:
    """Build each consumer's normalized 24-hour load shape and its archetype.

    Normalizing to sum 1 removes magnitude, which is what the clustering sees.
    Comparing raw kWh profiles instead would confound timing with amplitude.

    Args:
        df: Panel data with consumer_id, hour, the energy column and archetype.

    Returns:
        Tuple of (shapes, archetypes). Shapes is indexed by consumer_id with 24
        columns named 0 to 23. Archetypes is indexed the same way.
    """
    profile = (df.groupby(['consumer_id', 'hour'])[ENERGY_COL]
                 .mean()
                 .unstack('hour')
                 .reindex(columns=range(24))
                 .fillna(0.0))
    totals = profile.sum(axis=1).replace(0.0, np.nan)
    shapes = profile.div(totals, axis=0).fillna(1.0 / 24.0)

    archetypes = df.groupby('consumer_id')[ARCHETYPE_COL].first().reindex(shapes.index)
    return shapes, archetypes


def archetype_consumer_counts(df: pd.DataFrame) -> pd.Series:
    """Count consumers per archetype.

    Counting rows and dividing by the number of archetypes, as an earlier version
    did, gives the right answer only when every archetype has the same number of
    consumers and every consumer the same number of records. It silently reports
    nonsense otherwise.

    Args:
        df: Panel data with consumer_id and archetype.

    Returns:
        Consumer count per archetype, largest first.
    """
    counts = df.groupby(ARCHETYPE_COL)['consumer_id'].nunique().sort_values(ascending=False)
    counts.name = 'n_consumers'
    return counts


def eta_squared(values: Sequence[float], groups: Sequence) -> float:
    """Share of a variable's variance that sits between groups.

    Zero means the grouping explains nothing about the variable; one means it
    explains everything. Used here in both directions: it should be high for
    shape features and near zero for magnitude.

    Args:
        values: One value per observation.
        groups: Group label per observation, in the same order.

    Returns:
        Eta squared, or nan when the variable does not vary.
    """
    series = pd.Series(np.asarray(values, dtype=float))
    labels = pd.Series(np.asarray(groups))

    total_ss = float(((series - series.mean()) ** 2).sum())
    if total_ss == 0 or not np.isfinite(total_ss):
        return float('nan')

    grand_mean = series.mean()
    between_ss = 0.0
    for _, group in series.groupby(labels.to_numpy()):
        between_ss += len(group) * (group.mean() - grand_mean) ** 2

    return float(between_ss / total_ss)


def shape_separation_by_hour(shapes: pd.DataFrame, archetypes: pd.Series) -> pd.DataFrame:
    """Measure how much of the variation at each hour sits between archetypes.

    Args:
        shapes: Consumer by hour normalized shapes.
        archetypes: Archetype per consumer.

    Returns:
        One row per hour with the between-archetype spread of the archetype
        means, the mean within-archetype spread, their ratio, and eta squared.
    """
    logger.info("Measuring shape separation hour by hour")

    rows = []
    for hour in shapes.columns:
        column = shapes[hour]
        by_archetype = column.groupby(archetypes.to_numpy())
        rows.append({
            'hour': int(hour),
            'between_archetype_sd': float(by_archetype.mean().std()),
            'within_archetype_sd': float(by_archetype.std().mean()),
            'eta_squared': eta_squared(column, archetypes),
        })

    frame = pd.DataFrame(rows)
    frame['separation_ratio'] = frame['between_archetype_sd'] / frame['within_archetype_sd']
    return frame


def pairwise_archetype_distance(shapes: pd.DataFrame,
                               archetypes: pd.Series) -> Tuple[pd.DataFrame, pd.Series, pd.DataFrame]:
    """Compare distances between archetype mean shapes with within-archetype scatter.

    The distance used is the sum of absolute differences over the 24 hours, which
    on two profiles that each sum to 1 is twice the share of daily energy that
    would have to move from one hour to another to turn one profile into the
    other. That makes it readable: a distance of 0.20 means about 10 percent of
    the day's energy sits in different hours.

    Args:
        shapes: Consumer by hour normalized shapes.
        archetypes: Archetype per consumer.

    Returns:
        Tuple of (distance between archetype means, mean within-archetype
        distance to own mean, distance divided by the pair's mean within spread).
        A ratio above 1 means the archetypes are further apart than their members
        are from their own centre.
    """
    logger.info("Measuring pairwise archetype distances")

    names = sorted(archetypes.dropna().unique())
    means = {name: shapes.loc[archetypes == name].mean() for name in names}

    within = {}
    for name in names:
        members = shapes.loc[archetypes == name]
        within[name] = float((members - means[name]).abs().sum(axis=1).mean())
    within_series = pd.Series(within, name='within_archetype_distance')

    distance = pd.DataFrame(index=names, columns=names, dtype=float)
    ratio = pd.DataFrame(index=names, columns=names, dtype=float)
    for a in names:
        for b in names:
            d = float((means[a] - means[b]).abs().sum())
            distance.loc[a, b] = d
            pair_within = 0.5 * (within[a] + within[b])
            ratio.loc[a, b] = d / pair_within if pair_within > 0 else np.nan
        ratio.loc[a, a] = np.nan

    return distance, within_series, ratio


def nearest_centroid_agreement(shapes: pd.DataFrame,
                               archetypes: pd.Series) -> Dict[str, object]:
    """Assign every consumer to the nearest archetype mean shape and score it.

    This is the cleanest single number for how separable the dataset is. It uses
    the true labels to build the centroids, so it is an upper bound on what any
    unsupervised method could achieve, not a performance claim. A score of 1.0
    would mean the archetypes do not overlap at all and the clustering problem is
    trivial; a score near chance would mean the generator produced no usable
    structure.

    Args:
        shapes: Consumer by hour normalized shapes.
        archetypes: Archetype per consumer.

    Returns:
        Dictionary with the overall agreement, per-archetype agreement, the
        confusion table, and the chance level.
    """
    logger.info("Scoring nearest-centroid assignment against the true archetypes")

    names = sorted(archetypes.dropna().unique())
    centroids = pd.DataFrame({name: shapes.loc[archetypes == name].mean() for name in names})

    distances = pd.DataFrame(
        {name: (shapes - centroids[name]).abs().sum(axis=1) for name in names},
        index=shapes.index,
    )
    assigned = distances.idxmin(axis=1)

    correct = assigned.to_numpy() == archetypes.to_numpy()
    per_archetype = (pd.Series(correct, index=shapes.index)
                     .groupby(archetypes.to_numpy())
                     .mean()
                     .sort_values())

    confusion = pd.crosstab(
        pd.Series(archetypes.to_numpy(), name='true_archetype'),
        pd.Series(assigned.to_numpy(), name='nearest_centroid'),
    )

    return {
        'agreement': float(np.mean(correct)),
        'per_archetype': per_archetype,
        'confusion': confusion,
        'chance_level': float(1.0 / len(names)),
    }


def magnitude_leakage(df: pd.DataFrame) -> Dict[str, object]:
    """Test the generator's claim that magnitude carries no archetype identity.

    Args:
        df: Panel data with consumer_id, the energy column and archetype.

    Returns:
        Dictionary with eta squared of archetype on mean kWh, the per-archetype
        summary, and whether the leak stays under MAGNITUDE_LEAK_LIMIT.
    """
    logger.info("Checking whether magnitude leaks archetype identity")

    per_consumer = (df.groupby(['consumer_id', ARCHETYPE_COL])[ENERGY_COL]
                      .mean()
                      .reset_index()
                      .rename(columns={ENERGY_COL: 'mean_kwh'}))

    leak = eta_squared(per_consumer['mean_kwh'], per_consumer[ARCHETYPE_COL])
    summary = (per_consumer.groupby(ARCHETYPE_COL)['mean_kwh']
               .agg(['mean', 'std', 'min', 'max'])
               .sort_index())

    return {
        'eta_squared': leak,
        'summary': summary,
        'within_limit': bool(np.isfinite(leak) and leak <= MAGNITUDE_LEAK_LIMIT),
        'limit': MAGNITUDE_LEAK_LIMIT,
    }


def weekend_ratio_by_archetype(df: pd.DataFrame) -> Tuple[pd.DataFrame, float]:
    """Mean weekend to weekday energy ratio per archetype, and its eta squared.

    Included because one archetype is defined mainly through this single axis,
    which is worth knowing when reading the clustering result: a difference
    carried by one feature out of many is easy for a distance-based method to
    miss once every feature is standardized to the same weight. The eta squared
    makes that comparable with the shape numbers in check 1.

    Args:
        df: Panel data with consumer_id, timestamp or is_weekend, energy, archetype.

    Returns:
        Tuple of (per-archetype mean, spread and consumer count; share of the
        variation in the ratio that archetype explains). Returns an empty frame
        and nan when the panel does not cover both weekdays and weekends.
    """
    frame = df.copy()
    if 'is_weekend' not in frame.columns:
        frame['is_weekend'] = pd.to_datetime(frame['timestamp']).dt.dayofweek >= 5

    per_consumer = (frame.groupby(['consumer_id', ARCHETYPE_COL, 'is_weekend'])[ENERGY_COL]
                         .mean()
                         .unstack('is_weekend'))
    if True not in per_consumer.columns or False not in per_consumer.columns:
        logger.warning("The panel does not cover both weekdays and weekends; "
                       "the weekend ratio cannot be measured")
        return pd.DataFrame(), float('nan')

    per_consumer['weekend_ratio'] = per_consumer[True] / per_consumer[False]
    per_consumer = per_consumer.reset_index()

    summary = (per_consumer.groupby(ARCHETYPE_COL)['weekend_ratio']
               .agg(['mean', 'std', 'count'])
               .sort_values('mean'))
    leak = eta_squared(per_consumer['weekend_ratio'], per_consumer[ARCHETYPE_COL])

    return summary, leak


def plot_archetype_shapes(shapes: pd.DataFrame,
                          archetypes: pd.Series,
                          output_dir: str = 'outputs/figures',
                          n_examples: int = 15) -> None:
    """Plot each archetype's mean normalized shape over a sample of its members.

    Normalized shapes, not kWh, because that is what the clustering sees. The
    grey lines are the point of the figure: they show the overlap that makes the
    clustering problem non-trivial.
    """
    logger.info("Plotting archetype load shapes")

    names = sorted(archetypes.dropna().unique())
    n_cols = 2
    n_rows = int(np.ceil(len(names) / n_cols))
    fig, axes = plt.subplots(n_rows, n_cols, figsize=(13, 4.4 * n_rows), sharey=True)
    axes = np.atleast_1d(axes).ravel()

    population_mean = shapes.mean()

    for ax, name in zip(axes, names):
        members = shapes.loc[archetypes == name]
        for _, row in members.head(n_examples).iterrows():
            ax.plot(row.index, row.to_numpy(), color='gray', alpha=0.35, linewidth=1)
        ax.plot(population_mean.index, population_mean.to_numpy(), color='black',
                linestyle=':', linewidth=2, label='Population mean')
        ax.plot(members.mean().index, members.mean().to_numpy(), color='darkred',
                linewidth=2.5, label=f'{name} mean')
        ax.set_title(f'{name}: {len(members)} consumers, {n_examples} shown')
        ax.set_xlabel('Hour of day')
        ax.set_ylabel('Share of daily energy')
        ax.set_xticks(range(0, 24, 3))
        ax.legend(fontsize=9)

    for ax in axes[len(names):]:
        ax.axis('off')

    fig.suptitle('Normalized load shapes by archetype, with individual consumers behind')
    fig.tight_layout()

    path = Path(output_dir) / 'archetype_profiles.png'
    path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(path, dpi=200, bbox_inches='tight')
    plt.close(fig)
    logger.info(f"Saved archetype shapes to {path}")


def plot_archetype_separation(ratio: pd.DataFrame,
                              output_dir: str = 'outputs/figures') -> None:
    """Heatmap of between-archetype distance divided by within-archetype spread."""
    logger.info("Plotting the archetype separation matrix")

    fig, ax = plt.subplots(figsize=(7.5, 6))
    sns.heatmap(ratio.astype(float), annot=True, fmt='.2f', cmap='YlGnBu',
                cbar_kws={'label': 'Between distance / within spread'}, ax=ax)
    ax.set_title('How far apart the archetypes are, relative to their own scatter\n'
                 'Values near 1 mean the pair overlaps')
    ax.set_xlabel('Archetype')
    ax.set_ylabel('Archetype')

    fig.tight_layout()
    path = Path(output_dir) / 'archetype_separation.png'
    path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(path, dpi=200, bbox_inches='tight')
    plt.close(fig)
    logger.info(f"Saved the separation matrix to {path}")


def plot_magnitude_check(df: pd.DataFrame,
                         leak: Dict[str, object],
                         output_dir: str = 'outputs/figures') -> None:
    """Show that mean consumption does not separate the archetypes.

    This figure is meant to look boring. Four overlapping distributions is the
    result: it is what makes the behavioral against scale ablation a fair test.
    """
    logger.info("Plotting the magnitude leakage check")

    per_consumer = (df.groupby(['consumer_id', ARCHETYPE_COL])[ENERGY_COL]
                      .mean()
                      .reset_index()
                      .rename(columns={ENERGY_COL: 'mean_kwh'}))

    fig, ax = plt.subplots(figsize=(9, 5.5))
    order = sorted(per_consumer[ARCHETYPE_COL].unique())
    sns.boxplot(data=per_consumer, x=ARCHETYPE_COL, y='mean_kwh', order=order,
                color='lightsteelblue', ax=ax)
    sns.stripplot(data=per_consumer, x=ARCHETYPE_COL, y='mean_kwh', order=order,
                  color='black', alpha=0.4, size=3.5, ax=ax)

    eta = leak['eta_squared']
    ax.set_title(f'Mean consumption by archetype\n'
                 f'Archetype explains {eta:.1%} of the variation in magnitude '
                 f'(design target: under {leak["limit"]:.0%})')
    ax.set_xlabel('Archetype')
    ax.set_ylabel('Mean kWh per record')

    fig.tight_layout()
    path = Path(output_dir) / 'archetype_magnitude_check.png'
    path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(path, dpi=200, bbox_inches='tight')
    plt.close(fig)
    logger.info(f"Saved the magnitude check to {path}")


def plot_archetype_overlap_in_pca(df: pd.DataFrame,
                                  output_dir: str = 'outputs/figures') -> None:
    """Scatter the first two components of the behavioral features by true archetype.

    The archetype column is dropped before preprocessing, so this shows where the
    true groups fall in the space the clustering actually works in.
    """
    logger.info("Plotting archetype overlap in PCA space")

    from feature_engineering import engineer_all_features, select_features
    from pca_analysis import standardize_features
    from preprocessing import preprocess_pipeline
    from sklearn.decomposition import PCA

    truth = df.groupby('consumer_id')[ARCHETYPE_COL].first()

    preprocessed = preprocess_pipeline(df.drop(columns=[ARCHETYPE_COL]))
    features = engineer_all_features(preprocessed, feature_set='behavioral')
    selected = select_features(features, feature_group='behavioral')
    order = selected['consumer_id'].tolist()

    # consumer_id is an identifier, not a feature. run_pca_pipeline drops it; this
    # plot has to do the same or the arbitrary ID ends up loaded onto a component.
    feature_only = selected.drop(columns=['consumer_id']).select_dtypes(include=[np.number])
    X_scaled, _ = standardize_features(feature_only)
    pca = PCA(n_components=2, random_state=42)
    X_pca = pca.fit_transform(X_scaled)
    labels = truth.reindex(order).to_numpy()

    fig, ax = plt.subplots(figsize=(9, 7))
    palette = sns.color_palette('deep', len(np.unique(labels)))
    for color, name in zip(palette, sorted(np.unique(labels))):
        mask = labels == name
        ax.scatter(X_pca[mask, 0], X_pca[mask, 1], label=name, color=color,
                   alpha=0.75, s=42, edgecolors='black', linewidth=0.4)

    variance = pca.explained_variance_ratio_
    ax.set_xlabel(f'PC1 ({variance[0]:.1%} of variance)')
    ax.set_ylabel(f'PC2 ({variance[1]:.1%} of variance)')
    ax.set_title('True archetypes in the first two components of the behavioral features\n'
                 f'These two components hold {variance.sum():.1%} of the variance, so '
                 f'overlap here overstates the real overlap')
    ax.legend(title='Archetype')

    fig.tight_layout()
    path = Path(output_dir) / 'cross_archetype_overlap.png'
    path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(path, dpi=200, bbox_inches='tight')
    plt.close(fig)
    logger.info(f"Saved the PCA overlap plot to {path}")


def feature_informativeness(df: pd.DataFrame) -> pd.DataFrame:
    """Rank every behavioral feature by how much archetype information it carries.

    Two numbers per feature, both measured on the engineered feature table:

    - eta_squared: the share of the feature's variance that sits between
      archetypes. This is the same statistic used elsewhere in this file, applied
      one feature at a time. A feature near zero contributes a standardized
      dimension to the distance K-Means measures without contributing any of the
      structure the data was built with.
    - magnitude_correlation: Pearson correlation with mean kWh per consumer. Every
      behavioral feature is scale free by construction, so this is not a leak: it
      says whether shape and amplitude happen to move together in this population.
      It is reported because a reader is entitled to check rather than trust.

    This does not decide which features to keep. A feature can be individually
    uninformative and still matter in combination, and eta squared measures a
    single feature against a grouping rather than its contribution to a partition.
    It does tell you which features to be sceptical about.

    Args:
        df: Panel data with the archetype column attached.

    Returns:
        One row per feature, most informative first, with the feature's declared
        group.
    """
    logger.info("Measuring per-feature archetype informativeness")

    from feature_engineering import (
        BEHAVIORAL_FEATURES,
        DISPERSION_FEATURES,
        SHAPE_DESCRIPTOR_FEATURES,
        SHAPE_FEATURES,
        TIMING_FEATURES,
        VARIABILITY_FEATURES,
        engineer_all_features,
    )
    from preprocessing import preprocess_pipeline

    group_of = {}
    for name, group in (('shape bins', SHAPE_FEATURES),
                        ('timing', TIMING_FEATURES),
                        ('shape descriptors', SHAPE_DESCRIPTOR_FEATURES),
                        ('variability', VARIABILITY_FEATURES),
                        ('dispersion', DISPERSION_FEATURES)):
        for feature in group:
            group_of[feature] = name

    truth = df.groupby('consumer_id')[ARCHETYPE_COL].first()
    preprocessed = preprocess_pipeline(df.drop(columns=[ARCHETYPE_COL]))
    features = engineer_all_features(preprocessed, feature_set='combined')

    order = features['consumer_id'].tolist()
    labels = truth.reindex(order).to_numpy()
    magnitude = features[f'{ENERGY_COL}_mean']

    rows = []
    for feature in BEHAVIORAL_FEATURES:
        if feature not in features.columns:
            continue
        values = features[feature]
        rows.append({
            'feature': feature,
            'group': group_of.get(feature, 'unassigned'),
            'eta_squared': eta_squared(values, labels),
            'magnitude_correlation': float(values.corr(magnitude)),
        })

    table = pd.DataFrame(rows).sort_values('eta_squared', ascending=False)
    return table.reset_index(drop=True)


def plot_feature_informativeness(table: pd.DataFrame,
                                 output_dir: str = 'outputs/figures') -> None:
    """Bar chart of per-feature archetype eta squared, coloured by feature group."""
    logger.info("Plotting per-feature archetype informativeness")

    ordered = table.sort_values('eta_squared', ascending=True)
    groups = sorted(ordered['group'].unique())
    palette = dict(zip(groups, sns.color_palette('deep', len(groups))))
    colors = [palette[group] for group in ordered['group']]

    fig, ax = plt.subplots(figsize=(10, max(6.0, 0.22 * len(ordered))))
    ax.barh(ordered['feature'], ordered['eta_squared'], color=colors,
            edgecolor='black', linewidth=0.3)
    ax.set_xlabel('Share of the feature\'s variance explained by archetype (eta squared)')
    ax.set_ylabel('')
    ax.set_title('How much archetype information each behavioral feature carries\n'
                 'Measured on the engineered features, not on the model')
    ax.tick_params(axis='y', labelsize=7)

    handles = [plt.Rectangle((0, 0), 1, 1, facecolor=palette[group],
                             edgecolor='black', linewidth=0.3) for group in groups]
    ax.legend(handles, groups, title='Feature group', fontsize=8, loc='lower right')

    fig.tight_layout()
    path = Path(output_dir) / 'feature_informativeness.png'
    path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(path, dpi=200, bbox_inches='tight')
    plt.close(fig)
    logger.info(f"Saved the feature informativeness plot to {path}")


def _closest_pair(ratio: pd.DataFrame) -> Tuple[str, str, float]:
    """Return the pair of archetypes with the smallest separation ratio."""
    stacked = ratio.astype(float).stack().dropna()
    pairs = {tuple(sorted(index)): value for index, value in stacked.items()}
    (a, b), value = min(pairs.items(), key=lambda item: item[1])
    return a, b, float(value)


def generate_validation_report(df: pd.DataFrame,
                               output_dir: str = 'outputs/reports',
                               metrics_dir: Optional[str] = None) -> Dict[str, object]:
    """Measure everything, write the tables and write the report.

    Args:
        df: Panel data with archetype attached.
        output_dir: Directory for the markdown report.
        metrics_dir: Directory for the CSV tables. Defaults to a sibling
            'metrics' directory beside output_dir.

    Returns:
        Dictionary holding every measurement, so callers do not have to reparse
        the report.
    """
    logger.info("Generating the dataset validation report")

    reports_path = Path(output_dir)
    metrics_path = Path(metrics_dir) if metrics_dir else reports_path.parent / 'metrics'
    reports_path.mkdir(parents=True, exist_ok=True)
    metrics_path.mkdir(parents=True, exist_ok=True)

    shapes, archetypes = consumer_normalized_shapes(df)
    counts = archetype_consumer_counts(df)
    hourly = shape_separation_by_hour(shapes, archetypes)
    distance, within, ratio = pairwise_archetype_distance(shapes, archetypes)
    nearest = nearest_centroid_agreement(shapes, archetypes)
    leak = magnitude_leakage(df)
    weekend, weekend_eta = weekend_ratio_by_archetype(df)
    informative = feature_informativeness(df)

    hourly.to_csv(metrics_path / 'archetype_shape_separation.csv', index=False)
    ratio.astype(float).to_csv(metrics_path / 'archetype_separation_ratio.csv')
    leak['summary'].to_csv(metrics_path / 'archetype_magnitude_summary.csv')
    informative.to_csv(metrics_path / 'feature_informativeness.csv', index=False)

    closest_a, closest_b, closest_ratio = _closest_pair(ratio)
    strongest_hours = hourly.nlargest(3, 'eta_squared')
    mean_eta = float(hourly['eta_squared'].mean())

    lines = [
        "# Dataset Validation",
        "",
        "THIS IS SYNTHETIC DATA. Every consumer below was generated by",
        "src/data_loader.py. Nothing here is a measurement of real household or",
        "building behaviour.",
        "",
        "This file checks the dataset, not the analysis. It asks whether the data",
        "contains the structure the generator was designed to put in, and it answers",
        "with numbers measured from the generator's output rather than with a",
        "description of the generator's settings. The two can drift apart, and in an",
        "earlier version of this project they had.",
        "",
        "## What is in the dataset",
        "",
        f"- Consumers: {df['consumer_id'].nunique()}",
        f"- Records: {len(df):,}",
    ]
    if 'timestamp' in df.columns:
        lines.append(f"- Covering: {df['timestamp'].min()} to {df['timestamp'].max()}")
    lines += [
        f"- Archetypes: {len(counts)}",
        "",
        "### Consumers per archetype",
        "",
    ]
    for name, count in counts.items():
        lines.append(f"- {name}: {count} consumers ({count / counts.sum():.1%})")

    lines += [
        "",
        "## Check 1: are the archetypes distinguishable by load shape?",
        "",
        "Each consumer's 24-hour profile is normalized to sum to 1, which removes",
        "magnitude and leaves timing. Two spreads are then compared at every hour: how",
        "much the archetype means differ from each other, and how much consumers of one",
        "archetype differ among themselves.",
        "",
        f"Averaged over the 24 hours, archetype membership explains {mean_eta:.1%} of the",
        "variation in the normalized shape. The three hours where the archetypes differ",
        "most:",
        "",
    ]
    for _, row in strongest_hours.iterrows():
        lines.append(
            f"- Hour {int(row['hour']):02d}: archetype explains {row['eta_squared']:.1%} of "
            f"the variation, between-archetype spread {row['between_archetype_sd']:.4f} "
            f"against within-archetype spread {row['within_archetype_sd']:.4f} "
            f"(ratio {row['separation_ratio']:.2f})"
        )

    lines += [
        "",
        "### Distance between archetype mean shapes",
        "",
        "The distance is the sum of absolute differences over the 24 hours. Because both",
        "profiles sum to 1, a distance of 0.20 means about 10 percent of the day's energy",
        "sits in different hours. The ratio divides that distance by how far the members",
        "of the pair sit from their own archetype mean, so a ratio near or below",
        f"{DISTINCT_RATIO_FLOOR:.1f} means the pair overlaps rather than separates.",
        "",
        "Absolute distance between archetype means:",
        "",
        "```",
        distance.astype(float).round(4).to_string(),
        "```",
        "",
        "Distance divided by within-archetype spread:",
        "",
        "```",
        ratio.astype(float).round(2).to_string(),
        "```",
        "",
        "Mean distance from a consumer to its own archetype mean:",
        "",
    ]
    for name, value in within.items():
        lines.append(f"- {name}: {value:.4f}")

    tightest = str(within.idxmin())
    loosest = str(within.idxmax())

    # Each archetype's nearest neighbour in the ratio matrix. This, rather than an
    # archetype's own spread, is what should predict whether it survives as a
    # separate cluster: an archetype can be internally loose and still distinct if
    # nothing else sits near it.
    ratio_float = ratio.astype(float)
    nearest_other = {}
    for name in ratio_float.index:
        row = ratio_float.loc[name].drop(labels=[name])
        nearest_other[name] = (str(row.idxmin()), float(row.min()))

    lines += [
        "",
        f"Those spreads are not equal. {tightest} is the tightest at {within.min():.4f} and "
        f"{loosest} the loosest at {within.max():.4f}, a factor of "
        f"{within.max() / within.min():.1f}. A near-uniform profile has less room to vary "
        f"than a peaked one. On its own, though, a wide spread does not make an archetype "
        f"hard to identify: what matters is how close the nearest other archetype is "
        f"relative to that spread, which is the smallest value in each row above.",
        "",
        "Nearest other archetype, by that ratio:",
        "",
    ]
    for name, (other, value) in sorted(nearest_other.items(), key=lambda item: item[1][1]):
        lines.append(f"- {name}: closest to {other} at {value:.2f}")

    weak_pairs = []
    stacked = ratio.astype(float).stack().dropna()
    seen = set()
    for (a, b), value in stacked.items():
        key = tuple(sorted((a, b)))
        if key in seen:
            continue
        seen.add(key)
        if value < DISTINCT_RATIO_FLOOR:
            weak_pairs.append((a, b, float(value)))

    lines += [
        "",
        f"The closest pair is {closest_a} and {closest_b}, at a ratio of {closest_ratio:.2f}. "
        f"That is a prediction about the clustering, made here from the dataset alone and "
        f"before any model is fitted: if a method recovers fewer groups than the "
        f"{len(counts)} that were generated, {closest_a} and {closest_b} are the pair it "
        f"should be expected to merge, because they are the pair with the least room "
        f"between them relative to their own scatter.",
        "",
    ]
    if weak_pairs:
        lines.append(
            f"{len(weak_pairs)} pair(s) fall below {DISTINCT_RATIO_FLOOR:.1f}, meaning they "
            f"are not further from each other than their own members are from their centre:"
        )
        lines.append("")
        for a, b, value in sorted(weak_pairs, key=lambda item: item[2]):
            lines.append(f"- {a} and {b}: {value:.2f}")
        lines += [
            "",
            "Any clustering method should be expected to merge those pairs. That is a"
            " property of the dataset, not a fault in the pipeline.",
            "",
        ]
    else:
        lines += [
            f"Every pair separates by more than {DISTINCT_RATIO_FLOOR:.1f}, so all "
            f"{len(counts)} archetypes are distinguishable in principle. Whether an "
            f"unsupervised method finds all of them is a separate question, answered in "
            f"outputs/reports/validation_report.md.",
            "",
        ]

    lines += [
        "## Check 2: how separable is the dataset in practice?",
        "",
        "Every consumer is assigned to the nearest archetype mean shape. The true labels",
        "build the centroids, so this is an upper bound on what any unsupervised method",
        "could reach on this data, not a performance claim.",
        "",
        f"- Agreement with the true archetype: {nearest['agreement']:.1%}",
        f"- Chance level with {len(counts)} archetypes: {nearest['chance_level']:.1%}",
        "",
        "By archetype, weakest first:",
        "",
    ]
    for name, value in nearest['per_archetype'].items():
        lines.append(f"- {name}: {value:.1%} assigned to their own archetype")

    # Ties here are structural, not incidental: the two members of the closest pair
    # are always each other's nearest neighbour at the same ratio, so they cannot be
    # ordered against each other. Grouping by value keeps the prediction honest
    # instead of letting dictionary order invent a ranking.
    groups: Dict[float, List[str]] = {}
    for name, (_, value) in nearest_other.items():
        groups.setdefault(round(value, 2), []).append(str(name))

    tiers = sorted(groups)
    ranked = [sorted(groups[value]) for value in tiers]

    predicted_parts = []
    for value, group in zip(tiers, ranked):
        if len(group) == 1:
            predicted_parts.append(f"{group[0]} ({value:.2f})")
        else:
            predicted_parts.append(f"{' and '.join(group)} (tied at {value:.2f})")
    predicted_text = ", ".join(predicted_parts)

    observed_order = [str(name) for name in nearest['per_archetype'].index]

    lines += [
        "",
        "Check 1 predicted this ordering from the distance matrix alone, hardest first: "
        + predicted_text + ". The measured ordering is: " + ", ".join(observed_order) + ".",
        "",
    ]

    hits, misses = [], []
    (hits if observed_order[0] in ranked[0] else misses).append(
        f"the hardest archetype ({observed_order[0]})"
    )
    (hits if observed_order[-1] in ranked[-1] else misses).append(
        f"the easiest archetype ({observed_order[-1]})"
    )

    caveat = (
        "The matrix compares archetype means while the assignment works consumer by "
        "consumer, so an archetype whose members scatter unevenly around its mean can do "
        "better or worse than its mean-to-mean distance implies."
    )

    if not misses:
        lines += [
            "The prediction holds at both ends: " + " and ".join(hits) + " are the ones the "
            "distance matrix pointed at. The middle of the ordering is not predicted, and "
            "should not be. " + caveat,
            "",
        ]
    elif hits:
        lines += [
            "The prediction gets " + " and ".join(hits) + " right but misses "
            + " and ".join(misses) + ". " + caveat + " Treat the matrix as a guide to which "
            "distinctions are fragile, not as a forecast.",
            "",
        ]
    else:
        lines += [
            "The prediction misses " + " and ".join(misses) + ", so on this dataset the "
            "distance matrix is not a reliable guide. " + caveat + " The recovery results "
            "should be read from the measurements rather than anticipated from the geometry.",
            "",
        ]

    lines += [
        "Where the mistakes go:",
        "",
        "```",
        nearest['confusion'].to_string(),
        "```",
        "",
        f"An agreement of {nearest['agreement']:.1%} rather than 100 percent is the",
        "intended outcome. The generator blends a random fraction of the",
        "population-average shape into every consumer, so a tail of consumers genuinely",
        "sits between archetypes. A dataset where every consumer was unambiguous would",
        "make the clustering problem trivial and the results meaningless.",
        "",
        "## Check 3: does magnitude leak archetype identity?",
        "",
        "The generator draws each consumer's amplitude from one distribution shared by",
        "all archetypes, and mean-corrects every multiplicative effect, so mean",
        "consumption should carry no information about which archetype a consumer came",
        "from. This matters because the ablation study compares behavioral features",
        "against magnitude features. If magnitude leaked archetype identity, that",
        "comparison would be rigged.",
        "",
        f"- Archetype explains {leak['eta_squared']:.2%} of the variation in mean kWh "
        f"per consumer.",
        f"- Design target: at most {leak['limit']:.0%}.",
        f"- Within target: {'yes' if leak['within_limit'] else 'no'}.",
        "",
        "Mean kWh per record, by archetype:",
        "",
        "```",
        leak['summary'].round(4).to_string(),
        "```",
        "",
    ]
    if not leak['within_limit']:
        lines += [
            "This check failed. Magnitude carries archetype information, so the scale arm",
            "of the ablation study has an unfair advantage and its result cannot be read",
            "as evidence that magnitude features are uninformative in general. The",
            "generator's mean corrections need review.",
            "",
        ]

    if not weekend.empty:
        from feature_engineering import BEHAVIORAL_FEATURES

        n_behavioral = len(BEHAVIORAL_FEATURES)
        lines += [
            "## Check 4: the weekend axis",
            "",
            f"The ratio of weekend to weekday energy is one feature out of the "
            f"{n_behavioral} the clustering uses, and it is worth measuring on its own "
            f"because of how much archetype information it carries.",
            "",
            f"- Archetype explains {weekend_eta:.1%} of the variation in the weekend ratio.",
            f"- For comparison, it explains {mean_eta:.1%} of the variation in the "
            f"normalized shape, averaged over the 24 hours, and {leak['eta_squared']:.1%} "
            f"of the variation in magnitude.",
            "",
            "```",
            weekend.round(4).to_string(),
            "```",
            "",
            "So a single feature carries more archetype information than the average hour of",
            "the load shape. Standardization gives it the same weight as every other",
            f"feature, which means the distinction it encodes occupies 1 of the "
            f"{n_behavioral} dimensions K-Means measures distance in. An archetype that "
            "differs mainly along this axis is therefore easy to lose, and the closest "
            f"pair found above, {closest_a} and {closest_b}, is where that would show up.",
            "",
        ]

    lines += [
        "## Check 5: does every behavioral feature carry archetype information?",
        "",
        f"The clustering standardizes {len(informative)} behavioral features and gives",
        "each of them equal weight in the distance it measures. A feature that carries",
        "no archetype information does not average out: it adds a dimension of noise",
        "that the structure has to compete with. This check measures each feature on",
        "its own, before any model is fitted.",
        "",
        "Two caveats on how to read it. Eta squared measures one feature against the",
        "grouping, not its contribution to a partition, so a feature can be weak here",
        "and still useful in combination with others. And a high value does not make a",
        "feature necessary, since several features can carry the same information.",
        "",
        "Strongest ten:",
        "",
        "```",
        informative.head(10).round(4).to_string(index=False),
        "```",
        "",
        "Weakest ten:",
        "",
        "```",
        informative.tail(10).round(4).to_string(index=False),
        "```",
        "",
        "By feature group, mean eta squared:",
        "",
    ]
    by_group = (informative.groupby('group')['eta_squared']
                           .agg(['mean', 'max', 'count'])
                           .sort_values('mean', ascending=False))
    for group_name, row in by_group.iterrows():
        lines.append(
            f"- {group_name}: mean {row['mean']:.3f}, best {row['max']:.3f}, "
            f"{int(row['count'])} features"
        )

    weak = informative[informative['eta_squared'] < WEAK_FEATURE_ETA]
    strongest = informative.iloc[0]
    lines += [
        "",
        f"The single most informative feature is {strongest['feature']} at "
        f"{strongest['eta_squared']:.3f}.",
        "",
    ]
    if not weak.empty:
        lines += [
            f"{len(weak)} of {len(informative)} features fall below "
            f"{WEAK_FEATURE_ETA:.2f}: " + ", ".join(weak['feature'].tolist()) + ".",
            "",
            "Those are the features to be sceptical about. They are kept because eta",
            "squared judges one feature at a time against one grouping, which is not the",
            "same question as whether a feature helps a partition, and because dropping",
            "features on the strength of a supervised statistic would use the archetype",
            "labels to build the model. The ablation study in",
            "outputs/reports/ablation_study_report.md is where their contribution is",
            "tested without that circularity.",
            "",
        ]
    else:
        lines += [
            f"Every feature reaches at least {WEAK_FEATURE_ETA:.2f}, so none of them is",
            "pure noise with respect to the generated structure.",
            "",
        ]

    entangled = informative.reindex(
        informative['magnitude_correlation'].abs().sort_values(ascending=False).index
    ).head(3)
    lines += [
        "On the magnitude column: every behavioral feature is scale free by",
        "construction, which tests/test_features.py verifies by multiplying a",
        "consumer's whole series by a constant and checking that nothing moves. A",
        "correlation with mean kWh is therefore a fact about this population rather",
        "than a leak. The three largest are:",
        "",
    ]
    for _, row in entangled.iterrows():
        lines.append(
            f"- {row['feature']}: correlation {row['magnitude_correlation']:+.3f} with mean kWh"
        )
    lines += [
        "",
    ]

    lines += [
        "## What this file does and does not establish",
        "",
        "It establishes that the dataset contains measurable, overlapping shape structure",
        f"with {len(counts)} latent groups, that magnitude does not encode that structure,",
        f"and that the fragile distinction is between {closest_a} and {closest_b}, which is",
        "where a method recovering too few groups should be expected to merge first.",
        "",
        "It establishes nothing about real energy consumers. The archetypes were designed",
        "by hand. They are a controlled test bed for the pipeline, which is the only",
        "claim made for them anywhere in this repository.",
        "",
    ]

    (reports_path / 'dataset_validation_report.md').write_text("\n".join(lines), encoding='utf-8')
    logger.info(f"Validation report saved to {reports_path / 'dataset_validation_report.md'}")

    return {
        'consumer_counts': counts,
        'hourly_separation': hourly,
        'distance': distance,
        'within': within,
        'separation_ratio': ratio,
        'nearest_centroid': nearest,
        'magnitude_leak': leak,
        'weekend_ratio': weekend,
        'weekend_eta_squared': weekend_eta,
        'closest_pair': (closest_a, closest_b, closest_ratio),
        'mean_eta_squared': mean_eta,
        'feature_informativeness': informative,
    }


def run_dataset_validation(df: pd.DataFrame,
                           output_dir: str = 'outputs') -> Dict[str, object]:
    """Run every check, write five figures, the tables and the report.

    Args:
        df: Panel data with the archetype column attached.
        output_dir: Root output directory.

    Returns:
        The measurement dictionary from generate_validation_report.
    """
    logger.info("Starting dataset validation")

    if ARCHETYPE_COL not in df.columns:
        raise ValueError(
            "Dataset validation needs the archetype column. It is available only on "
            "generated data, since it is the generator's own record of which group each "
            "consumer was drawn from."
        )

    frame = df.copy()
    if 'hour' not in frame.columns:
        frame['hour'] = pd.to_datetime(frame['timestamp']).dt.hour

    figures = f"{output_dir}/figures"
    shapes, archetypes = consumer_normalized_shapes(frame)
    _, _, ratio = pairwise_archetype_distance(shapes, archetypes)
    leak = magnitude_leakage(frame)

    plot_archetype_shapes(shapes, archetypes, figures)
    plot_archetype_separation(ratio, figures)
    plot_magnitude_check(frame, leak, figures)
    plot_archetype_overlap_in_pca(frame, figures)

    measurements = generate_validation_report(
        frame,
        output_dir=f"{output_dir}/reports",
        metrics_dir=f"{output_dir}/metrics",
    )
    plot_feature_informativeness(measurements['feature_informativeness'], figures)

    logger.info("Dataset validation completed")
    return measurements


if __name__ == "__main__":
    from project_paths import anchor_to_project_root

    anchor_to_project_root()

    from data_loader import generate_synthetic_data_archetype_based

    raw = generate_synthetic_data_archetype_based(
        n_consumers=200, n_days=30, hourly_records=True, random_seed=42
    )
    results = run_dataset_validation(raw)

    print(f"\nConsumers per archetype:\n{results['consumer_counts'].to_string()}")
    print(f"\nArchetype explains {results['mean_eta_squared']:.1%} of the shape variation")
    print(f"Nearest-centroid agreement: {results['nearest_centroid']['agreement']:.1%}")
    print(f"Magnitude leakage (eta squared): {results['magnitude_leak']['eta_squared']:.4f}")
    closest = results['closest_pair']
    print(f"Closest archetype pair: {closest[0]} and {closest[1]} at ratio {closest[2]:.2f}")

    informative = results['feature_informativeness']
    print("\nMost informative behavioral features:")
    print(informative.head(8).round(4).to_string(index=False))
    print("\nLeast informative behavioral features:")
    print(informative.tail(8).round(4).to_string(index=False))
