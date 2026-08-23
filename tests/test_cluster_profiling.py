"""Unit tests for cluster naming and interpretation (Phase 11 / Phase 12)."""
import numpy as np
import pandas as pd
import pytest

from cluster_profiling import (
    COMPARED_METRICS,
    FLAT_CONCENTRATION_LIMIT,
    PROFILE_METRICS,
    cluster_load_shapes,
    interpret_cluster,
    name_cluster,
    population_baseline,
    profile_clusters,
)


def _feature_frame() -> pd.DataFrame:
    """Four consumers with hand-set shapes: two evening, one midday, one flat."""
    evening = np.zeros(24)
    evening[18:21] = 1.0
    midday = np.zeros(24)
    midday[12:15] = 1.0
    flat = np.full(24, 1.0)

    rows = []
    for cid, profile, weekend_ratio, mean_kwh in [
        (1, evening, 1.30, 1.0),
        (2, evening, 1.25, 3.0),
        (3, midday, 0.80, 2.0),
        (4, flat, 1.00, 2.0),
    ]:
        shape = profile / profile.sum()
        row = {'consumer_id': cid}
        row.update({f'hour_{h}_shape': shape[h] for h in range(24)})
        row['peak_concentration'] = float(np.sort(shape)[-3:].sum())
        row['weekend_ratio'] = weekend_ratio
        row['morning_share'] = float(shape[6:12].sum())
        row['afternoon_share'] = float(shape[12:18].sum())
        row['evening_share'] = float(shape[18:24].sum())
        row['night_share'] = float(shape[0:6].sum())
        row['shape_entropy'] = 0.9
        row['base_load_share'] = float(24 * shape.min())
        row['coefficient_of_variation'] = 0.5
        row['peak_to_avg_ratio'] = 4.0
        row['energy_consumption_kwh_mean'] = mean_kwh
        rows.append(row)
    return pd.DataFrame(rows)


def test_compared_metrics_are_all_profiled():
    """A metric can only be compared against the population if it is reported."""
    missing = [name for name in COMPARED_METRICS if name not in PROFILE_METRICS]
    assert not missing, f"COMPARED_METRICS entries with no profile column: {missing}"


def test_profile_clusters_reports_sizes_and_population_ratios():
    features = _feature_frame()
    labels = np.array([0, 0, 1, 2])

    profiles, baseline = profile_clusters(features, labels)

    assert profiles['size'].tolist() == [2, 1, 1]
    np.testing.assert_allclose(profiles['size_share'].to_numpy(), [0.5, 0.25, 0.25])

    # Cluster 0 is the two evening consumers, so its peak hour must be in the
    # evening block and its ratio column must equal value / population.
    evening_row = profiles[profiles['cluster'] == 0].iloc[0]
    assert 18 <= int(evening_row['peak_hour']) <= 20
    np.testing.assert_allclose(
        evening_row['weekend_ratio_vs_population'],
        evening_row['weekend_ratio'] / baseline['weekend_ratio'],
        rtol=1e-12,
    )


def test_population_baseline_is_the_mean_over_consumers():
    features = _feature_frame()
    baseline = population_baseline(features)

    np.testing.assert_allclose(baseline['weekend_ratio'],
                               features['weekend_ratio'].mean(), rtol=1e-12)
    np.testing.assert_allclose(baseline['mean_kwh'],
                               features['energy_consumption_kwh_mean'].mean(), rtol=1e-12)
    assert baseline['size'] == 4.0


def test_cluster_load_shapes_includes_the_population_row():
    features = _feature_frame()
    shapes = cluster_load_shapes(features, np.array([0, 0, 1, 2]))

    assert 'population' in shapes.index
    np.testing.assert_allclose(shapes.sum(axis=1).to_numpy(), np.ones(len(shapes)), rtol=1e-9)


def test_names_come_from_the_peak_hour_and_the_weekend_gap():
    baseline = {'weekend_ratio': 1.0}

    assert name_cluster({'peak_hour': 20, 'peak_concentration': 0.4}, baseline) == 'Evening-Peaking'
    assert name_cluster({'peak_hour': 13, 'peak_concentration': 0.4}, baseline) == 'Midday-Peaking'
    assert name_cluster({'peak_hour': 8, 'peak_concentration': 0.4}, baseline) == 'Morning-Peaking'
    assert name_cluster({'peak_hour': 3, 'peak_concentration': 0.4}, baseline) == 'Night-Peaking'

    heavy = name_cluster(
        {'peak_hour': 20, 'peak_concentration': 0.4, 'weekend_ratio': 1.4}, baseline)
    light = name_cluster(
        {'peak_hour': 20, 'peak_concentration': 0.4, 'weekend_ratio': 0.6}, baseline)
    assert heavy == 'Evening-Peaking Weekend-Heavy'
    assert light == 'Evening-Peaking Weekday-Heavy'


def test_a_near_flat_cluster_is_not_named_after_its_nominal_peak():
    """A flat profile has a peak hour, but naming it after one would overstate it."""
    below = FLAT_CONCENTRATION_LIMIT - 0.01
    assert name_cluster({'peak_hour': 20, 'peak_concentration': below}) == 'Flat All-Day'

    above = FLAT_CONCENTRATION_LIMIT + 0.01
    assert name_cluster({'peak_hour': 20, 'peak_concentration': above}) == 'Evening-Peaking'


def test_a_name_never_mentions_magnitude():
    """Magnitude was excluded from the clustering, so it cannot enter the name."""
    baseline = {'weekend_ratio': 1.0, 'mean_kwh': 1.0}
    profile = {'peak_hour': 20, 'peak_concentration': 0.4, 'weekend_ratio': 1.4,
               'mean_kwh': 99.0, 'total_kwh': 12345.0}

    name = name_cluster(profile, baseline).lower()
    for banned in ('high', 'low', 'kwh', 'large', 'small', 'heavy-user'):
        assert banned not in name, f"the name leaked magnitude through '{banned}'"


def test_interpretation_does_not_claim_a_direction_it_cannot_show():
    """Guards a real bug: 1.0449 against 1.0351 both print as 1.04.

    The earlier version compared the full-precision values and then printed both
    rounded to two decimals, producing "1.04 times weekday energy, more
    weekend-oriented than the population figure of 1.04". A reader checking the
    sentence against its own numbers would find it contradicting itself.
    """
    text = interpret_cluster({'weekend_ratio': 1.0449}, {'weekend_ratio': 1.0351})

    assert '1.04 times weekday energy' in text
    assert 'more weekend-oriented' not in text
    assert 'less weekend-oriented' not in text
    assert 'indistinguishable from the population figure of 1.04' in text


def test_interpretation_still_states_a_direction_when_the_gap_is_visible():
    higher = interpret_cluster({'weekend_ratio': 1.30}, {'weekend_ratio': 1.00})
    lower = interpret_cluster({'weekend_ratio': 0.70}, {'weekend_ratio': 1.00})

    assert 'more weekend-oriented' in higher
    assert 'less weekend-oriented' in lower


def test_interpretation_reports_flatness_through_entropy_and_base_load():
    text = interpret_cluster(
        {'shape_entropy': 0.9972, 'base_load_share': 0.7710},
        {'shape_entropy': 0.9801, 'base_load_share': 0.5390},
    )

    assert 'normalized entropy of 0.997' in text
    assert 'population 0.980' in text
    assert '77.1%' in text
    assert '53.9%' in text


def test_interpretation_flags_magnitude_as_context_only():
    text = interpret_cluster({'mean_kwh': 1.35}, {'mean_kwh': 1.30})
    assert 'magnitude was not clustered on' in text


def test_interpretation_survives_a_profile_with_almost_nothing_in_it():
    """Missing metrics are skipped rather than printed as nan."""
    text = interpret_cluster({'size': 12, 'size_share': 0.06}, {})

    assert 'Holds 12 consumers' in text
    assert 'nan' not in text.lower()


def test_profile_clusters_rejects_a_label_count_mismatch():
    features = _feature_frame()
    with pytest.raises(ValueError, match='they must match'):
        profile_clusters(features, np.array([0, 1]))
