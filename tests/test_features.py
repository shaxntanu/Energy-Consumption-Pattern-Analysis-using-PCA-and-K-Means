"""Unit tests for feature engineering definitions (Phase 3 / Phase 10)."""
import numpy as np
import pandas as pd
import pytest

from feature_engineering import (
    engineer_normalized_load_shape,
    engineer_temporal_features,
    engineer_load_features,
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


def test_normalized_profile_sums_to_one():
    df = _toy_panel()
    shape = engineer_normalized_load_shape(df)
    hour_cols = [c for c in shape.columns if c.startswith('hour_') and c.endswith('_shape')]
    sums = shape[hour_cols].sum(axis=1)
    np.testing.assert_allclose(sums.values, np.ones(len(shape)), rtol=1e-6)


def test_normalized_profile_independent_of_scale():
    """Two consumers with same timing but different magnitude → same shape."""
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
    # Consumer 1: weekday_mult=2, weekend_mult=0.5 → ratio = 0.25
    # Consumer 2: weekday_mult=1, weekend_mult=3 → ratio = 3.0
    r1 = temporal.loc[temporal['consumer_id'] == 1, 'weekend_ratio'].iloc[0]
    r2 = temporal.loc[temporal['consumer_id'] == 2, 'weekend_ratio'].iloc[0]
    np.testing.assert_allclose(r1, 0.25, rtol=1e-6)
    np.testing.assert_allclose(r2, 3.0, rtol=1e-6)
    # Old bug made every consumer ≈ 2/7; consumers must differ materially
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
