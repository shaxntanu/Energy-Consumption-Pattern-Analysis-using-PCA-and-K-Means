"""
Feature Engineering Module

Builds one row per consumer from the hourly panel, with a strict separation
between three groups of features:

- behavioral: how energy is used. Every feature is invariant to how much the
  consumer uses in total: normalized load shape, period shares, peak timing,
  weekend behaviour, variability ratios.
- scale: how much energy is used. Absolute kWh statistics and current.
- context: neither behaviour nor scale. Voltage, power factor and temperature.
  Excluded from clustering because they describe the grid and the weather, not
  the consumer's usage pattern.

The behavioral group is the primary experiment. The other two exist so the
ablation study can show what happens when the question changes from "how does
this consumer use energy?" to "how much does this consumer use?".

Two narrower views of the behavioral group are also declared, 'shape' (the 24
raw hour bins) and 'summary' (the scalars derived from them). They exist so the
ablation study can separate the contribution of the raw profile from the
contribution of the descriptors, rather than reporting the two together and
assuming both earn their place.

Every behavioral feature must be invariant to multiplying a consumer's whole
series by a constant. That is not a style rule, it is the property the research
question depends on, and tests/test_features.py checks it directly.
"""

from typing import List, Optional

import logging
import numpy as np
import pandas as pd

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

ENERGY_COL = 'energy_consumption_kwh'

# Hour blocks used for the period shares. Half-open intervals.
PERIOD_BLOCKS = {
    'night': (0, 6),
    'morning': (6, 12),
    'afternoon': (12, 18),
    'evening': (18, 24),
}

SHAPE_FEATURES: List[str] = [f'hour_{h}_shape' for h in range(24)]

# When the consumer uses energy, and whether the weekend routine differs.
TIMING_FEATURES: List[str] = [
    'morning_share',
    'afternoon_share',
    'evening_share',
    'night_share',
    'night_day_ratio',
    'peak_hour_sin',
    'peak_hour_cos',
    'peak_concentration',
    'profile_ramp',
    'weekend_ratio',
    'weekend_shape_distance',
]

# Scalars computed from the normalized 24-hour shape. Each is a function of a
# vector that already sums to 1, so none of them can carry magnitude. They
# describe how the day's energy is distributed, in ways the 24 individual bins
# do not express directly: how concentrated it is, how much of it is a constant
# floor, and which periodicities it contains.
SHAPE_DESCRIPTOR_FEATURES: List[str] = [
    'shape_entropy',
    'shape_gini',
    'base_load_share',
    'harmonic_1_amplitude',
    'harmonic_2_amplitude',
    'harmonic_3_amplitude',
    'haar_detail_l1',
    'haar_detail_l2',
    'haar_detail_l3',
]

# Variability of the record-level series around the consumer's own level.
VARIABILITY_FEATURES: List[str] = [
    'peak_to_avg_ratio',
    'coefficient_of_variation',
    'skewness',
    'kurtosis',
]

# Variability measured across days and in the upper tail rather than across the
# hours of the mean day. coefficient_of_variation mixes within-day and
# between-day variation together; daily_total_cv isolates the second.
DISPERSION_FEATURES: List[str] = [
    'daily_total_cv',
    'p90_median_ratio',
    'weekend_cv_ratio',
]

BEHAVIORAL_SUMMARY_FEATURES: List[str] = (
    TIMING_FEATURES + SHAPE_DESCRIPTOR_FEATURES + VARIABILITY_FEATURES + DISPERSION_FEATURES
)

BEHAVIORAL_FEATURES: List[str] = SHAPE_FEATURES + BEHAVIORAL_SUMMARY_FEATURES

SCALE_FEATURES: List[str] = [
    f'{ENERGY_COL}_mean',
    f'{ENERGY_COL}_max',
    f'{ENERGY_COL}_min',
    f'{ENERGY_COL}_median',
    f'{ENERGY_COL}_std',
    f'{ENERGY_COL}_sum',
    'current_a_mean',
]

CONTEXT_FEATURES: List[str] = [
    'voltage_v_mean',
    'power_factor_mean',
    'temperature_c_mean',
]

FEATURE_GROUPS = {
    'behavioral': BEHAVIORAL_FEATURES,
    'scale': SCALE_FEATURES,
    'combined': BEHAVIORAL_FEATURES + SCALE_FEATURES,
    # Subsets of the behavioral group, for the ablation study only. They are not
    # alternatives to it in the pipeline.
    'shape': SHAPE_FEATURES,
    'summary': BEHAVIORAL_SUMMARY_FEATURES,
}

# load_factor, the ratio of mean to peak, is deliberately absent: it is the exact
# reciprocal of peak_to_avg_ratio, so it would add a column without adding
# information and would give that one distinction two of the standardized
# dimensions K-Means measures distance in.


def _hourly_mean_profile(df: pd.DataFrame) -> pd.DataFrame:
    """Mean energy per (consumer, hour), as a consumer x 24 wide frame.

    Args:
        df: Preprocessed panel with consumer_id, hour and the energy column.

    Returns:
        DataFrame indexed by consumer_id with columns 0..23. Hours a consumer
        never records are filled with 0.
    """
    profile = (df.groupby(['consumer_id', 'hour'])[ENERGY_COL]
                 .mean()
                 .unstack('hour'))
    profile = profile.reindex(columns=range(24)).fillna(0.0)
    profile.columns = [int(h) for h in profile.columns]
    return profile


def _normalize_rows(frame: pd.DataFrame) -> pd.DataFrame:
    """Scale each row to sum to 1, leaving all-zero rows as zeros."""
    totals = frame.sum(axis=1)
    safe = totals.replace(0.0, np.nan)
    return frame.div(safe, axis=0).fillna(0.0)


def _shape_matrix(df: pd.DataFrame) -> pd.DataFrame:
    """Normalized 24-hour shape per consumer, as a consumer x 24 wide frame."""
    return _normalize_rows(_hourly_mean_profile(df))


def _normalized_entropy(shape: np.ndarray) -> np.ndarray:
    """Shannon entropy of each row, divided by the entropy of a flat profile.

    The rows are already probability distributions over the 24 hours, so the
    entropy is defined directly on them. Dividing by log(24) puts the result on
    a fixed scale: a perfectly flat day scores 1, a day whose energy all falls
    in one hour scores 0. Nothing in between has a single interpretation, which
    is why this is reported alongside peak_concentration rather than instead of
    it.

    Args:
        shape: Array of (n_consumers, 24) rows summing to 1.

    Returns:
        Array of length n_consumers.
    """
    hours = shape.shape[1]
    with np.errstate(divide='ignore', invalid='ignore'):
        logs = np.where(shape > 0, np.log(np.where(shape > 0, shape, 1.0)), 0.0)
    return -(shape * logs).sum(axis=1) / np.log(hours)


def _gini(shape: np.ndarray) -> np.ndarray:
    """Gini coefficient of each row.

    Measures inequality between the 24 hours. A flat day scores 0. A day with
    everything in one hour scores (n - 1) / n, which is 23/24 for 24 hours, not
    1: the Gini coefficient reaches 1 only in the limit of infinitely many
    categories. Entropy and Gini both answer "how unevenly is the day
    distributed", but Gini responds mostly to the gap between the busiest and
    quietest hours while entropy responds to the whole distribution, so they
    disagree on profiles with several moderate peaks.

    Args:
        shape: Array of (n_consumers, 24) rows summing to 1.

    Returns:
        Array of length n_consumers, nan for all-zero rows.
    """
    hours = shape.shape[1]
    ordered = np.sort(shape, axis=1)
    ranks = np.arange(1, hours + 1)
    totals = ordered.sum(axis=1)
    safe = np.where(totals > 0, totals, np.nan)
    weighted = (ordered * ranks).sum(axis=1)
    return 2.0 * weighted / (hours * safe) - (hours + 1) / hours


def _haar_detail_energy(shape: np.ndarray, levels: int = 3) -> np.ndarray:
    """Share of each row's energy held in each Haar detail band.

    A 3-level orthonormal Haar decomposition splits 24 hourly values into detail
    bands of 12, 6 and 3 coefficients plus a 3-coefficient approximation. Level 1
    measures change between neighbouring hours, level 2 change between
    neighbouring 2-hour blocks, level 3 change between neighbouring 4-hour
    blocks. The transform is orthonormal, so the four band energies sum to the
    energy of the input and each detail band can be reported as a fraction of it.

    24 factors as 3 * 2^3, so three levels divide exactly. No padding is needed
    and no wavelet library is required.

    This separates two profiles that a single variability number treats alike: a
    profile that alternates hour by hour puts its energy in level 1, while a
    profile with one broad daytime block puts its energy in level 3.

    Limitation worth knowing before reading these features: the Haar basis is not
    shift invariant. A block that lines up with the dyadic grid produces no detail
    coefficients at all, and the same block shifted by one hour produces several,
    so two consumers with the same routine an hour apart can score differently.
    tests/test_features.py pins that behaviour. The Fourier amplitudes are shift
    invariant in magnitude, which is why both families are kept rather than one
    standing in for the other.

    Args:
        shape: Array of (n_consumers, 24) rows.
        levels: Number of decomposition levels.

    Returns:
        Array of (n_consumers, levels), finest band first. All-zero rows come
        back as nan, since a row with no energy has no distribution of it.
    """
    root_two = np.sqrt(2.0)
    approx = np.asarray(shape, dtype=float)

    if approx.shape[1] % (2 ** levels):
        raise ValueError(
            f"A {levels}-level Haar decomposition needs a length divisible by "
            f"{2 ** levels}, got {approx.shape[1]}"
        )

    total_energy = (approx ** 2).sum(axis=1)
    bands = []
    for _ in range(levels):
        even = approx[:, 0::2]
        odd = approx[:, 1::2]
        detail = (even - odd) / root_two
        bands.append((detail ** 2).sum(axis=1))
        approx = (even + odd) / root_two

    safe_total = np.where(total_energy > 0, total_energy, np.nan)
    return np.column_stack(bands) / safe_total[:, None]


def engineer_normalized_load_shape(df: pd.DataFrame) -> pd.DataFrame:
    """Build the normalized 24-hour load shape, the core behavioral feature.

    Dividing each consumer's mean hourly profile by its own total removes
    magnitude completely. Two consumers with the same routine and a tenfold
    difference in consumption get identical shape features.

    Args:
        df: Preprocessed panel with consumer_id, hour and the energy column.

    Returns:
        DataFrame with consumer_id and 24 hour_<h>_shape columns summing to 1.
    """
    logger.info("Engineering normalized load shape (24-hour profile)")

    shape = _shape_matrix(df)
    shape.columns = [f'hour_{h}_shape' for h in shape.columns]
    shape = shape.reset_index()

    logger.info(f"Created 24-hour shape features. Shape: {shape.shape}")
    return shape


def engineer_temporal_features(df: pd.DataFrame) -> pd.DataFrame:
    """Build timing features: period shares, peak hour, weekend behaviour.

    Period usage is expressed as a SHARE of the consumer's daily energy, not as
    an absolute mean. An absolute mean would make these features proxies for
    total consumption and would pull magnitude back into the behavioral set.

    Peak hour is encoded as a sine and cosine pair because hour 23 and hour 0
    are one hour apart, not twenty-three.

    Args:
        df: Preprocessed panel with consumer_id, hour, is_weekend and energy.

    Returns:
        DataFrame with consumer_id and the timing features.
    """
    logger.info("Engineering temporal features")

    shape = _shape_matrix(df)

    out = pd.DataFrame(index=shape.index)

    for period, (start, end) in PERIOD_BLOCKS.items():
        out[f'{period}_share'] = shape.loc[:, start:end - 1].sum(axis=1)

    day_share = shape.loc[:, 6:17].sum(axis=1)
    out['night_day_ratio'] = out['night_share'] / day_share.replace(0.0, np.nan)

    peak_hour = shape.values.argmax(axis=1).astype(float)
    out['peak_hour_sin'] = np.sin(2 * np.pi * peak_hour / 24.0)
    out['peak_hour_cos'] = np.cos(2 * np.pi * peak_hour / 24.0)

    top3 = np.sort(shape.values, axis=1)[:, -3:].sum(axis=1)
    out['peak_concentration'] = top3

    # Mean absolute hour-to-hour change of the shape, wrapping midnight.
    # Smooth industrial profiles score low, spiky household profiles score high.
    wrapped = np.hstack([shape.values, shape.values[:, [0]]])
    out['profile_ramp'] = np.abs(np.diff(wrapped, axis=1)).mean(axis=1)

    # Energy-based weekend ratio: weekend mean energy over weekday mean energy.
    # Not the share of records that fall on a weekend.
    has_weekend = bool(df['is_weekend'].any())
    has_weekday = bool((~df['is_weekend']).any())

    if has_weekend and has_weekday:
        weekend_energy = df[df['is_weekend']].groupby('consumer_id')[ENERGY_COL].mean()
        weekday_energy = df[~df['is_weekend']].groupby('consumer_id')[ENERGY_COL].mean()
        out['weekend_ratio'] = (weekend_energy / weekday_energy.replace(0.0, np.nan))

        # How much the weekday and weekend routines differ in timing, independent
        # of how much energy each day uses. Expressed as the share of daily
        # energy that moves between hours.
        weekend_shape = _shape_matrix(df[df['is_weekend']])
        weekday_shape = _shape_matrix(df[~df['is_weekend']])
        aligned_weekend = weekend_shape.reindex(index=shape.index).fillna(0.0)
        aligned_weekday = weekday_shape.reindex(index=shape.index).fillna(0.0)
        out['weekend_shape_distance'] = (
            0.5 * (aligned_weekend - aligned_weekday).abs().sum(axis=1)
        )
    else:
        # The window contains only weekdays or only weekend days, so neither
        # feature is defined. They are left empty and dropped downstream rather
        # than filled with a made-up value.
        logger.warning(
            "Time window does not contain both weekdays and weekend days. "
            "weekend_ratio and weekend_shape_distance are undefined and will be dropped."
        )
        out['weekend_ratio'] = np.nan
        out['weekend_shape_distance'] = np.nan

    return out.reset_index()


def engineer_load_features(df: pd.DataFrame) -> pd.DataFrame:
    """Build variability features from the record-level series.

    All four are scale free: two are ratios to the consumer's own mean, two are
    standardized moments.

    Args:
        df: Preprocessed panel with consumer_id and the energy column.

    Returns:
        DataFrame with consumer_id, peak_to_avg_ratio, coefficient_of_variation,
        skewness and kurtosis.
    """
    logger.info("Engineering load variability features")

    grouped = df.groupby('consumer_id')[ENERGY_COL]
    mean = grouped.mean()
    safe_mean = mean.replace(0.0, np.nan)

    out = pd.DataFrame({
        'peak_to_avg_ratio': grouped.max() / safe_mean,
        'coefficient_of_variation': grouped.std() / safe_mean,
        'skewness': grouped.skew(),
        'kurtosis': grouped.apply(lambda x: x.kurt() if len(x) > 3 else np.nan),
    })
    return out.reset_index()


def engineer_shape_descriptors(df: pd.DataFrame) -> pd.DataFrame:
    """Summarize the normalized 24-hour shape with concentration and frequency measures.

    The 24 hour bins already contain everything these features describe, but they
    contain it in a form K-Means cannot use well. Euclidean distance between two
    24-vectors is dominated by hour-by-hour disagreement, so two consumers with
    the same routine shifted by one hour look far apart, and a consumer with a
    flat profile looks similar to anyone whose peak happens to fall where the
    flat consumer has average usage. These nine scalars state the properties
    directly:

    - shape_entropy, shape_gini: how evenly the day's energy is spread.
    - base_load_share: the fraction of the day's energy that would be used if
      every hour matched the quietest hour. This is the always-on floor, and it
      is the de-min idea from Jin et al. (2016) expressed as a feature rather
      than applied as a preprocessing step, so nothing is subtracted from the
      data and the choice stays visible.
    - harmonic_1..3_amplitude: the first three Fourier amplitudes of the profile.
      One cycle per day, two cycles per day (the morning-plus-evening double
      peak), three cycles per day. Because the profile sums to 1, the zero
      frequency term is exactly 1, so these amplitudes are already relative to
      the daily total.
    - haar_detail_l1..l3: how much of the profile's energy sits at the 2-hour,
      4-hour and 8-hour scale. Fourier amplitudes say which periodicities are
      present; the wavelet bands say how sharp the transitions are.

    Args:
        df: Preprocessed panel with consumer_id, hour and the energy column.

    Returns:
        DataFrame with consumer_id and the nine descriptors.
    """
    logger.info("Engineering shape descriptors (concentration, base load, frequency content)")

    shape = _shape_matrix(df)
    values = shape.to_numpy(dtype=float)

    out = pd.DataFrame(index=shape.index)
    out['shape_entropy'] = _normalized_entropy(values)
    out['shape_gini'] = _gini(values)
    out['base_load_share'] = values.shape[1] * values.min(axis=1)

    spectrum = np.abs(np.fft.rfft(values, axis=1))
    for order in (1, 2, 3):
        out[f'harmonic_{order}_amplitude'] = spectrum[:, order]

    detail = _haar_detail_energy(values, levels=3)
    for level in (1, 2, 3):
        out[f'haar_detail_l{level}'] = detail[:, level - 1]

    return out.reset_index()


def engineer_dispersion_features(df: pd.DataFrame) -> pd.DataFrame:
    """Build variability features that the mean day and the record-level CV miss.

    coefficient_of_variation is computed over every record a consumer has, so it
    mixes two different things: how much usage moves within a day, and how much
    one day differs from the next. A consumer with an identical routine every day
    and a consumer whose total swings by a factor of three can reach the same
    value. These three features separate that:

    - daily_total_cv: variability of daily totals across days. Routine regularity.
    - p90_median_ratio: the 90th percentile of the record-level series over its
      median. How far the busy records sit above the typical one. Less sensitive
      to a single extreme record than peak_to_avg_ratio, which uses the maximum.
    - weekend_cv_ratio: weekend coefficient of variation over weekday
      coefficient of variation. Whether the weekend routine is more or less
      regular than the weekday one, independent of whether it uses more energy.

    All three are ratios, so all three are invariant to the consumer's scale.

    Args:
        df: Preprocessed panel with consumer_id, the energy column and, for the
            first and third features, timestamp and is_weekend.

    Returns:
        DataFrame with consumer_id and the three features. A feature whose input
        is unavailable is returned as nan rather than as a substitute value.
    """
    logger.info("Engineering dispersion features (day to day, upper tail, weekend regularity)")

    grouped = df.groupby('consumer_id')[ENERGY_COL]
    out = pd.DataFrame(index=grouped.mean().index)

    if 'timestamp' in df.columns:
        daily = df[['consumer_id', ENERGY_COL]].copy()
        daily['day'] = pd.to_datetime(df['timestamp']).dt.floor('D')
        totals = daily.groupby(['consumer_id', 'day'])[ENERGY_COL].sum()
        by_consumer = totals.groupby(level='consumer_id')
        out['daily_total_cv'] = by_consumer.std() / by_consumer.mean().replace(0.0, np.nan)
    else:
        logger.warning(
            "No timestamp column, so daily totals cannot be formed and "
            "daily_total_cv is undefined. It will be dropped or median-filled downstream."
        )
        out['daily_total_cv'] = np.nan

    out['p90_median_ratio'] = (
        grouped.quantile(0.90) / grouped.median().replace(0.0, np.nan)
    )

    has_weekend = 'is_weekend' in df.columns and bool(df['is_weekend'].any())
    has_weekday = 'is_weekend' in df.columns and bool((~df['is_weekend']).any())

    if has_weekend and has_weekday:
        weekend = df[df['is_weekend']].groupby('consumer_id')[ENERGY_COL]
        weekday = df[~df['is_weekend']].groupby('consumer_id')[ENERGY_COL]
        weekend_cv = weekend.std() / weekend.mean().replace(0.0, np.nan)
        weekday_cv = weekday.std() / weekday.mean().replace(0.0, np.nan)
        out['weekend_cv_ratio'] = weekend_cv / weekday_cv.replace(0.0, np.nan)
    else:
        logger.warning(
            "Time window does not contain both weekdays and weekend days, so "
            "weekend_cv_ratio is undefined."
        )
        out['weekend_cv_ratio'] = np.nan

    return out.reset_index()


def engineer_scale_features(df: pd.DataFrame) -> pd.DataFrame:
    """Build magnitude and context features.

    Args:
        df: Preprocessed panel.

    Returns:
        DataFrame with consumer_id, the scale features and the context features
        that are present in the input.
    """
    logger.info("Engineering scale and context features")

    aggregations = {ENERGY_COL: ['mean', 'max', 'min', 'median', 'std', 'sum']}
    for column in ('voltage_v', 'current_a', 'power_factor', 'temperature_c'):
        if column in df.columns:
            aggregations[column] = ['mean']

    features = df.groupby('consumer_id').agg(aggregations)
    features.columns = ['_'.join(col) for col in features.columns]

    logger.info(f"Scale and context features shape: {features.shape}")
    return features.reset_index()


def engineer_all_features(df: pd.DataFrame, feature_set: str = 'behavioral') -> pd.DataFrame:
    """Run the full per-consumer feature engineering pipeline.

    Every feature that exists is computed regardless of feature_set, so the
    profiling step always has magnitude available for reporting even when
    clustering only saw behavioral features. feature_set decides what is
    returned, and select_features decides what reaches PCA.

    Args:
        df: Preprocessed panel.
        feature_set: Any key of FEATURE_GROUPS. 'shape' and 'summary' are subsets
            of 'behavioral' and return the behavioral table for select_features
            to narrow.

    Returns:
        DataFrame with one row per consumer, including consumer_id.
    """
    if feature_set not in FEATURE_GROUPS:
        raise ValueError(f"Unknown feature_set: {feature_set}. Known: {list(FEATURE_GROUPS)}")

    logger.info(f"Starting feature engineering pipeline (feature_set: {feature_set})")

    behavioral = engineer_normalized_load_shape(df)
    for step in (engineer_temporal_features, engineer_shape_descriptors,
                 engineer_load_features, engineer_dispersion_features):
        behavioral = behavioral.merge(step(df), on='consumer_id', how='left')
    scale = engineer_scale_features(df)

    if feature_set == 'scale':
        features = scale
    elif feature_set == 'combined':
        features = behavioral.merge(scale, on='consumer_id', how='left')
    else:
        # behavioral, shape and summary all live in the behavioral table.
        features = behavioral

    # A feature that is identical for every consumer carries no information and
    # would divide by zero during standardization.
    constant = [c for c in features.columns
                if c != 'consumer_id' and features[c].nunique(dropna=False) <= 1]
    if constant:
        logger.info(f"Dropping constant features: {constant}")
        features = features.drop(columns=constant)

    missing = features.isnull().sum().sum()
    if missing:
        logger.info(f"Filling {missing} missing feature values with the column median")
        numeric = features.columns.drop('consumer_id')
        features[numeric] = features[numeric].fillna(features[numeric].median())

    logger.info(f"Feature engineering complete. Shape: {features.shape}")
    return features


def select_features(df: pd.DataFrame,
                    exclude_cols: Optional[List[str]] = None,
                    feature_group: str = 'behavioral') -> pd.DataFrame:
    """Select the columns of one feature group, by explicit name.

    Selection is by membership in a declared list, never by substring matching.
    Substring matching is what previously pulled voltage_v_mean and
    temperature_c_mean into the scale group.

    Args:
        df: Frame produced by engineer_all_features.
        exclude_cols: Columns to drop from the result. Defaults to none.
        feature_group: Any key of FEATURE_GROUPS, or 'all'.

    Returns:
        DataFrame with consumer_id followed by the selected features, in the
        declared order.
    """
    exclude = set(exclude_cols or [])

    if feature_group == 'all':
        wanted = [c for c in df.columns if c != 'consumer_id']
    elif feature_group in FEATURE_GROUPS:
        wanted = [c for c in FEATURE_GROUPS[feature_group] if c in df.columns]
    else:
        raise ValueError(
            f"Unknown feature_group: {feature_group}. Known: {list(FEATURE_GROUPS)} plus 'all'"
        )

    selected = [c for c in wanted if c not in exclude]
    if not selected:
        raise ValueError(f"No features left after selecting group '{feature_group}'")

    columns = (['consumer_id'] if 'consumer_id' in df.columns else []) + selected
    logger.info(f"Selected {len(selected)} features for analysis (group: {feature_group})")
    return df[columns]


if __name__ == "__main__":
    from data_loader import generate_synthetic_data
    from preprocessing import preprocess_pipeline

    raw = generate_synthetic_data(n_consumers=50, n_days=14, hourly_records=True)
    preprocessed = preprocess_pipeline(raw.drop(columns=['archetype']))

    for group in FEATURE_GROUPS:
        all_features = engineer_all_features(preprocessed, feature_set=group)
        chosen = select_features(all_features, feature_group=group)
        print(f"\n{group}: {chosen.shape[1] - 1} features")
        print(f"  {chosen.columns.tolist()[1:8]} ...")
