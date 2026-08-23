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

BEHAVIORAL_SUMMARY_FEATURES: List[str] = [
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
    'peak_to_avg_ratio',
    'coefficient_of_variation',
    'skewness',
    'kurtosis',
]

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
}


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

    shape = _normalize_rows(_hourly_mean_profile(df))
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

    profile = _hourly_mean_profile(df)
    shape = _normalize_rows(profile)

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
        weekend_shape = _normalize_rows(_hourly_mean_profile(df[df['is_weekend']]))
        weekday_shape = _normalize_rows(_hourly_mean_profile(df[~df['is_weekend']]))
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
        feature_set: 'behavioral', 'scale' or 'combined'.

    Returns:
        DataFrame with one row per consumer, including consumer_id.
    """
    if feature_set not in FEATURE_GROUPS:
        raise ValueError(f"Unknown feature_set: {feature_set}. Known: {list(FEATURE_GROUPS)}")

    logger.info(f"Starting feature engineering pipeline (feature_set: {feature_set})")

    behavioral = engineer_normalized_load_shape(df)
    behavioral = behavioral.merge(engineer_temporal_features(df), on='consumer_id', how='left')
    behavioral = behavioral.merge(engineer_load_features(df), on='consumer_id', how='left')
    scale = engineer_scale_features(df)

    if feature_set == 'behavioral':
        features = behavioral
    elif feature_set == 'scale':
        features = scale
    else:
        features = behavioral.merge(scale, on='consumer_id', how='left')

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
        feature_group: 'behavioral', 'scale', 'combined' or 'all'.

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

    for group in ('behavioral', 'scale', 'combined'):
        all_features = engineer_all_features(preprocessed, feature_set=group)
        chosen = select_features(all_features, feature_group=group)
        print(f"\n{group}: {chosen.shape[1] - 1} features")
        print(f"  {chosen.columns.tolist()[1:8]} ...")
