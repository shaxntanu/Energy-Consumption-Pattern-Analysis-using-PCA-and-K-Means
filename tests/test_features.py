"""Unit tests for feature engineering definitions (Phase 3 / Phase 10)."""
import numpy as np
import pandas as pd
import pytest

from feature_engineering import (
    BEHAVIORAL_FEATURES,
    BEHAVIORAL_SUMMARY_FEATURES,
    DISPERSION_FEATURES,
    FEATURE_GROUPS,
    SCALE_FEATURES,
    SHAPE_DESCRIPTOR_FEATURES,
    SHAPE_FEATURES,
    engineer_all_features,
    engineer_dispersion_features,
    engineer_load_features,
    engineer_normalized_load_shape,
    engineer_shape_descriptors,
    engineer_temporal_features,
)


def _toy_panel() -> pd.DataFrame:
    """Two consumers over 7 days, known energy values including a weekend."""
    rows = []
    # Consumer 1: weekday heavy; Consumer 2: weekend heavy
    start = pd.Timestamp('2024-01-01')  # Monday
    for cid, weekend_mult, weekday_mult in [(1, 0.5, 2.0), (2, 3.0, 1.0)]:
        for h in range(24 * 7):  # full week so weekend days exist
            ts = start + pd.Timedelta(hours=h)
            is_weekend = ts.dayofweek >= 5
            base = weekend_mult if is_weekend else weekday_mult
            hour = ts.hour
            if cid == 1:
                shape = 2.0 if hour == 12 else 0.5
            else:
                shape = 2.0 if hour == 20 else 0.5
            rows.append({
                'consumer_id': cid,
                'timestamp': ts,
                'hour': hour,
                'day_of_week': ts.dayofweek,
                'is_weekend': is_weekend,
                'energy_consumption_kwh': base * shape,
                'voltage_v': 230.0,
                'current_a': 1.0,
                'power_factor': 0.9,
                'temperature_c': 20.0,
            })
    return pd.DataFrame(rows)


def _panel_from_profiles(profiles: dict, n_days: int = 14) -> pd.DataFrame:
    """Build a panel where each consumer repeats a fixed 24-hour profile.

    Args:
        profiles: consumer_id -> 24 hourly kWh values, repeated every day.
        n_days: Days to repeat, starting on a Monday so weekends exist.

    Returns:
        Panel with the columns the feature functions need.
    """
    rows = []
    start = pd.Timestamp('2024-01-01')  # Monday
    for cid, profile in profiles.items():
        assert len(profile) == 24
        for h in range(24 * n_days):
            ts = start + pd.Timedelta(hours=h)
            rows.append({
                'consumer_id': cid,
                'timestamp': ts,
                'hour': ts.hour,
                'day_of_week': ts.dayofweek,
                'is_weekend': ts.dayofweek >= 5,
                'energy_consumption_kwh': float(profile[ts.hour]),
                'voltage_v': 230.0,
                'current_a': 1.0,
                'power_factor': 0.9,
                'temperature_c': 20.0,
            })
    return pd.DataFrame(rows)


def test_normalized_profile_sums_to_one():
    df = _toy_panel()
    shape = engineer_normalized_load_shape(df)
    hour_cols = [c for c in shape.columns if c.startswith('hour_') and c.endswith('_shape')]
    sums = shape[hour_cols].sum(axis=1)
    np.testing.assert_allclose(sums.values, np.ones(len(shape)), rtol=1e-6)


def test_normalized_profile_independent_of_scale():
    """Two consumers with same timing but different magnitude -> same shape."""
    rows = []
    for cid, scale in [(1, 1.0), (2, 10.0)]:
        for hour in range(24):
            energy = scale * (2.0 if hour == 18 else 0.5)
            rows.append({
                'consumer_id': cid,
                'hour': hour,
                'energy_consumption_kwh': energy,
            })
    df = pd.DataFrame(rows)
    shape = engineer_normalized_load_shape(df)
    hour_cols = [c for c in shape.columns if c.endswith('_shape')]
    s1 = shape.loc[shape['consumer_id'] == 1, hour_cols].values.ravel()
    s2 = shape.loc[shape['consumer_id'] == 2, hour_cols].values.ravel()
    np.testing.assert_allclose(s1, s2, rtol=1e-6)


def test_weekend_ratio_is_energy_based():
    df = _toy_panel()
    temporal = engineer_temporal_features(df)
    # Consumer 1: weekday_mult=2, weekend_mult=0.5 -> ratio = 0.25
    # Consumer 2: weekday_mult=1, weekend_mult=3 -> ratio = 3.0
    r1 = temporal.loc[temporal['consumer_id'] == 1, 'weekend_ratio'].iloc[0]
    r2 = temporal.loc[temporal['consumer_id'] == 2, 'weekend_ratio'].iloc[0]
    np.testing.assert_allclose(r1, 0.25, rtol=1e-6)
    np.testing.assert_allclose(r2, 3.0, rtol=1e-6)
    # Old bug made every consumer ~ 2/7; consumers must differ materially
    assert abs(r1 - r2) > 1.0
    assert not np.isclose(r1, r2)


def test_peak_to_average_ratio():
    df = _toy_panel()
    load = engineer_load_features(df)
    for _, row in load.iterrows():
        assert row['peak_to_avg_ratio'] >= 1.0
    # Manual check for consumer 1
    c1 = df[df['consumer_id'] == 1]['energy_consumption_kwh']
    expected = c1.max() / c1.mean()
    actual = load.loc[load['consumer_id'] == 1, 'peak_to_avg_ratio'].iloc[0]
    np.testing.assert_allclose(actual, expected, rtol=1e-6)


def test_coefficient_of_variation():
    df = _toy_panel()
    load = engineer_load_features(df)
    c1 = df[df['consumer_id'] == 1]['energy_consumption_kwh']
    expected = c1.std() / c1.mean()
    actual = load.loc[load['consumer_id'] == 1, 'coefficient_of_variation'].iloc[0]
    np.testing.assert_allclose(actual, expected, rtol=1e-6)


def test_shape_descriptors_at_the_two_extremes():
    """Flat and single-spike profiles pin every descriptor to a known value."""
    flat = [1.0] * 24
    spike = [0.0] * 24
    spike[3] = 6.0

    descriptors = engineer_shape_descriptors(
        _panel_from_profiles({1: flat, 2: spike})
    ).set_index('consumer_id')

    # A flat day is maximum entropy, zero inequality, all base load, no harmonics
    # and no wavelet detail at any scale.
    np.testing.assert_allclose(descriptors.loc[1, 'shape_entropy'], 1.0, atol=1e-9)
    np.testing.assert_allclose(descriptors.loc[1, 'shape_gini'], 0.0, atol=1e-9)
    np.testing.assert_allclose(descriptors.loc[1, 'base_load_share'], 1.0, atol=1e-9)
    for order in (1, 2, 3):
        np.testing.assert_allclose(
            descriptors.loc[1, f'harmonic_{order}_amplitude'], 0.0, atol=1e-9
        )
    for level in (1, 2, 3):
        np.testing.assert_allclose(
            descriptors.loc[1, f'haar_detail_l{level}'], 0.0, atol=1e-9
        )

    # One hour holding the whole day is the opposite end. Gini tops out at
    # (n - 1) / n = 23/24, not 1, and every Fourier amplitude equals the DC term.
    np.testing.assert_allclose(descriptors.loc[2, 'shape_entropy'], 0.0, atol=1e-9)
    np.testing.assert_allclose(descriptors.loc[2, 'shape_gini'], 23.0 / 24.0, atol=1e-9)
    np.testing.assert_allclose(descriptors.loc[2, 'base_load_share'], 0.0, atol=1e-9)
    for order in (1, 2, 3):
        np.testing.assert_allclose(
            descriptors.loc[2, f'harmonic_{order}_amplitude'], 1.0, atol=1e-9
        )
    # Orthonormal Haar on a unit spike halves the remaining energy each level.
    np.testing.assert_allclose(descriptors.loc[2, 'haar_detail_l1'], 0.500, atol=1e-9)
    np.testing.assert_allclose(descriptors.loc[2, 'haar_detail_l2'], 0.250, atol=1e-9)
    np.testing.assert_allclose(descriptors.loc[2, 'haar_detail_l3'], 0.125, atol=1e-9)


def test_shape_descriptors_are_scale_free():
    """Multiplying a consumer's whole series by a constant changes nothing."""
    profile = [0.4, 0.3, 0.3, 0.2, 0.2, 0.3, 0.9, 1.4, 1.1, 0.6, 0.5, 0.5,
               0.7, 0.6, 0.5, 0.5, 0.8, 1.6, 2.4, 2.2, 1.7, 1.1, 0.7, 0.5]
    descriptors = engineer_shape_descriptors(_panel_from_profiles({
        1: profile,
        2: [value * 37.0 for value in profile],
    })).set_index('consumer_id')

    np.testing.assert_allclose(
        descriptors.loc[1].to_numpy(dtype=float),
        descriptors.loc[2].to_numpy(dtype=float),
        rtol=1e-9,
    )


def test_fourier_harmonics_identify_the_dominant_periodicity():
    """A pure one-cycle day loads harmonic 1, a two-cycle day loads harmonic 2.

    For a profile 1 + a * cos(2 * pi * k * (h - phase) / 24), normalizing by the
    daily total of 24 makes the k-th rFFT amplitude exactly a / 2 and every other
    harmonic zero, so the expected values here are arithmetic rather than fitted.
    """
    amplitude = 0.6
    one_cycle = [1 + amplitude * np.cos(2 * np.pi * (hour - 19) / 24) for hour in range(24)]
    two_cycle = [1 + amplitude * np.cos(2 * np.pi * 2 * (hour - 7) / 24) for hour in range(24)]

    descriptors = engineer_shape_descriptors(
        _panel_from_profiles({1: one_cycle, 2: two_cycle})
    ).set_index('consumer_id')

    np.testing.assert_allclose(
        descriptors.loc[1, 'harmonic_1_amplitude'], amplitude / 2, atol=1e-9)
    np.testing.assert_allclose(
        descriptors.loc[1, 'harmonic_2_amplitude'], 0.0, atol=1e-9)
    np.testing.assert_allclose(
        descriptors.loc[2, 'harmonic_2_amplitude'], amplitude / 2, atol=1e-9)
    np.testing.assert_allclose(
        descriptors.loc[2, 'harmonic_1_amplitude'], 0.0, atol=1e-9)
    for cid in (1, 2):
        np.testing.assert_allclose(
            descriptors.loc[cid, 'harmonic_3_amplitude'], 0.0, atol=1e-9)


def test_haar_bands_see_variation_the_first_harmonics_miss():
    """The wavelet bands and the Fourier amplitudes are not redundant.

    A profile alternating hour by hour repeats twelve times a day, so harmonics
    1 to 3 are exactly zero and the Fourier features cannot see it at all. The
    finest wavelet band is where that variation shows up. This is the reason both
    families are included rather than one standing in for the other.
    """
    high, low = 3.0, 0.5
    alternating = [high if hour % 2 == 0 else low for hour in range(24)]

    descriptors = engineer_shape_descriptors(
        _panel_from_profiles({1: alternating})
    ).set_index('consumer_id')

    for order in (1, 2, 3):
        np.testing.assert_allclose(
            descriptors.loc[1, f'harmonic_{order}_amplitude'], 0.0, atol=1e-9)

    # Hand computation. The normalized profile alternates between 1/14 and 1/84,
    # so each of the twelve level-1 detail coefficients is (1/14 - 1/84)/sqrt(2)
    # and the coarser bands are exactly zero because every 2-hour block average
    # is identical.
    top, bottom = 1.0 / 14.0, 1.0 / 84.0
    detail_energy = 12 * ((top - bottom) / np.sqrt(2)) ** 2
    total_energy = 12 * top ** 2 + 12 * bottom ** 2
    np.testing.assert_allclose(
        descriptors.loc[1, 'haar_detail_l1'], detail_energy / total_energy, rtol=1e-9)
    np.testing.assert_allclose(descriptors.loc[1, 'haar_detail_l2'], 0.0, atol=1e-12)
    np.testing.assert_allclose(descriptors.loc[1, 'haar_detail_l3'], 0.0, atol=1e-12)


def test_haar_bands_are_sensitive_to_where_a_block_starts():
    """Pins a known limitation of these three features rather than hiding it.

    The Haar basis is not shift invariant. A block that lines up with the dyadic
    grid produces no detail coefficients at all, while the same block shifted by
    one hour does. Two consumers with the same routine an hour apart can
    therefore get different wavelet features, which is a weakness of the
    representation and a reason not to read these three features on their own.
    The Fourier amplitudes, which are shift invariant in magnitude, are
    unaffected, which is the other half of why both families are kept.
    """
    aligned = [3.0 if 8 <= hour < 16 else 0.5 for hour in range(24)]
    shifted = [3.0 if 9 <= hour < 17 else 0.5 for hour in range(24)]

    descriptors = engineer_shape_descriptors(
        _panel_from_profiles({1: aligned, 2: shifted})
    ).set_index('consumer_id')

    bands = ['haar_detail_l1', 'haar_detail_l2', 'haar_detail_l3']
    np.testing.assert_allclose(descriptors.loc[1, bands].to_numpy(dtype=float),
                               [0.0, 0.0, 0.0], atol=1e-12)
    assert descriptors.loc[2, 'haar_detail_l1'] > 0.01

    harmonics = ['harmonic_1_amplitude', 'harmonic_2_amplitude', 'harmonic_3_amplitude']
    np.testing.assert_allclose(descriptors.loc[1, harmonics].to_numpy(dtype=float),
                               descriptors.loc[2, harmonics].to_numpy(dtype=float),
                               rtol=1e-9)


def test_daily_total_cv_measures_variation_between_days():
    df = _toy_panel()
    dispersion = engineer_dispersion_features(df).set_index('consumer_id')

    daily = (df.groupby(['consumer_id', df['timestamp'].dt.floor('D')])
               ['energy_consumption_kwh'].sum())
    for cid in (1, 2):
        totals = daily.loc[cid]
        expected = totals.std() / totals.mean()
        np.testing.assert_allclose(
            dispersion.loc[cid, 'daily_total_cv'], expected, rtol=1e-9
        )

    # This is not the record-level coefficient of variation. The toy consumers
    # vary both within the day and between weekday and weekend, so the two
    # numbers must differ.
    load = engineer_load_features(df).set_index('consumer_id')
    assert not np.isclose(
        dispersion.loc[1, 'daily_total_cv'], load.loc[1, 'coefficient_of_variation']
    )


def test_daily_total_cv_is_zero_for_an_identical_routine():
    """A consumer repeating the same day exactly has no between-day variation."""
    profile = [0.5 + 0.1 * hour for hour in range(24)]
    dispersion = engineer_dispersion_features(
        _panel_from_profiles({1: profile})
    ).set_index('consumer_id')
    np.testing.assert_allclose(dispersion.loc[1, 'daily_total_cv'], 0.0, atol=1e-12)


def test_p90_median_and_weekend_cv_ratio_match_manual_values():
    df = _toy_panel()
    dispersion = engineer_dispersion_features(df).set_index('consumer_id')

    for cid in (1, 2):
        series = df.loc[df['consumer_id'] == cid, 'energy_consumption_kwh']
        np.testing.assert_allclose(
            dispersion.loc[cid, 'p90_median_ratio'],
            series.quantile(0.90) / series.median(),
            rtol=1e-9,
        )

        weekend = df[(df['consumer_id'] == cid) & df['is_weekend']]['energy_consumption_kwh']
        weekday = df[(df['consumer_id'] == cid) & ~df['is_weekend']]['energy_consumption_kwh']
        expected = (weekend.std() / weekend.mean()) / (weekday.std() / weekday.mean())
        np.testing.assert_allclose(
            dispersion.loc[cid, 'weekend_cv_ratio'], expected, rtol=1e-9
        )

    # Both toy consumers scale their whole day by a single weekend multiplier, so
    # the weekend and weekday series have the same relative spread and the ratio
    # would be exactly 1 if both were measured on the same number of records. The
    # panel has 120 weekday and 48 weekend records and both coefficients use the
    # sample standard deviation, so the ratio carries the ddof=1 correction
    # sqrt((48/47) / (120/119)) = 1.0064. The offset is identical for every
    # consumer here, but it is a real property of the feature: comparing two
    # coefficients of variation computed on different sample sizes is not exact.
    n_weekend, n_weekday = 48, 120
    correction = np.sqrt((n_weekend / (n_weekend - 1)) / (n_weekday / (n_weekday - 1)))
    np.testing.assert_allclose(dispersion['weekend_cv_ratio'].to_numpy(),
                               [correction, correction], rtol=1e-9)
    assert abs(correction - 1.0) < 0.01


def test_dispersion_features_are_undefined_without_the_columns_they_need():
    """Missing inputs produce nan, not a substituted value."""
    df = _toy_panel()

    no_weekend = df[~df['is_weekend']].copy()
    assert engineer_dispersion_features(no_weekend)['weekend_cv_ratio'].isna().all()

    no_timestamp = df.drop(columns=['timestamp'])
    assert engineer_dispersion_features(no_timestamp)['daily_total_cv'].isna().all()


def test_feature_group_declarations_are_consistent():
    """The declared groups must compose without overlap or duplication."""
    assert BEHAVIORAL_FEATURES == SHAPE_FEATURES + BEHAVIORAL_SUMMARY_FEATURES
    assert FEATURE_GROUPS['shape'] == SHAPE_FEATURES
    assert FEATURE_GROUPS['summary'] == BEHAVIORAL_SUMMARY_FEATURES
    assert FEATURE_GROUPS['combined'] == BEHAVIORAL_FEATURES + SCALE_FEATURES

    for name, group in FEATURE_GROUPS.items():
        assert len(group) == len(set(group)), f"{name} declares a duplicate feature"

    # Nothing may be in both the behavioral and the scale group, or the ablation
    # study would not be comparing two different questions.
    assert not set(BEHAVIORAL_FEATURES) & set(SCALE_FEATURES)

    # load_factor is mean / peak, the reciprocal of peak_to_avg_ratio, and is
    # deliberately not declared.
    assert 'load_factor' not in BEHAVIORAL_FEATURES


def test_every_declared_behavioral_feature_is_actually_produced():
    """Guards against a name in the declared list that no function computes."""
    from data_loader import generate_synthetic_data
    from preprocessing import preprocess_pipeline

    raw = generate_synthetic_data(n_consumers=16, n_days=14, hourly_records=True,
                                  random_seed=7)
    preprocessed = preprocess_pipeline(raw.drop(columns=['archetype']))
    features = engineer_all_features(preprocessed, feature_set='behavioral')

    missing = [name for name in BEHAVIORAL_FEATURES if name not in features.columns]
    assert not missing, f"declared but not produced: {missing}"
    assert features[BEHAVIORAL_FEATURES].notna().all().all()


def test_whole_behavioral_set_is_invariant_to_consumer_scale():
    """The property the research question rests on, checked end to end.

    Consumers 1 and 2 have identical timing and differ only in magnitude, so
    every behavioral feature must agree between them. Consumer 3 has different
    timing, which keeps the columns from being constant and dropped.
    """
    from preprocessing import preprocess_pipeline

    evening = [0.4, 0.3, 0.3, 0.2, 0.2, 0.3, 0.9, 1.4, 1.1, 0.6, 0.5, 0.5,
               0.7, 0.6, 0.5, 0.5, 0.8, 1.6, 2.4, 2.2, 1.7, 1.1, 0.7, 0.5]
    daytime = [0.3, 0.2, 0.2, 0.2, 0.3, 0.6, 1.0, 1.2, 1.8, 2.1, 2.3, 2.2,
               2.0, 1.9, 1.6, 1.2, 0.9, 0.8, 0.7, 0.6, 0.5, 0.4, 0.3, 0.3]

    panel = _panel_from_profiles({
        1: evening,
        2: [value * 12.5 for value in evening],
        3: daytime,
    })
    features = engineer_all_features(preprocess_pipeline(panel),
                                     feature_set='behavioral').set_index('consumer_id')

    behavioral = [c for c in BEHAVIORAL_FEATURES if c in features.columns]
    assert len(behavioral) > 24, "too many columns were dropped for this test to mean anything"

    np.testing.assert_allclose(
        features.loc[1, behavioral].to_numpy(dtype=float),
        features.loc[2, behavioral].to_numpy(dtype=float),
        rtol=1e-8,
        atol=1e-10,
    )

    # And the two must not be identical to a consumer with different timing,
    # otherwise the assertion above would pass trivially.
    with pytest.raises(AssertionError):
        np.testing.assert_allclose(
            features.loc[1, behavioral].to_numpy(dtype=float),
            features.loc[3, behavioral].to_numpy(dtype=float),
            rtol=1e-8,
        )
