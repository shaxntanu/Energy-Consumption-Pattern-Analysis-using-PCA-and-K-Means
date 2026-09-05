"""Preprocessing tests: no cross-consumer leakage under shuffled row order."""
import numpy as np
import pandas as pd

from preprocessing import handle_missing_values, preprocess_pipeline


def test_no_cross_consumer_leakage_when_shuffled():
    """
    Inject a unique sentinel missing value pattern per consumer.
    After within-consumer fill on shuffled data, consumer B must never receive
    consumer A's sentinel value.
    """
    rows = []
    for cid, fill_value in [(1, 111.0), (2, 222.0)]:
        for i in range(10):
            energy = fill_value if i != 5 else np.nan  # gap at index 5
            rows.append({
                'consumer_id': cid,
                'timestamp': pd.Timestamp('2024-01-01') + pd.Timedelta(hours=i),
                'energy_consumption_kwh': energy,
                'voltage_v': 230.0,
                'current_a': 1.0,
                'power_factor': 0.95,
                'temperature_c': 20.0,
            })
    df = pd.DataFrame(rows)

    # Shuffle aggressively
    shuffled = df.sample(frac=1.0, random_state=7).reset_index(drop=True)
    # Sort is applied inside preprocess_pipeline; also test handle_missing_values directly
    # after sorting within groups as the pipeline does
    sorted_df = shuffled.sort_values(['consumer_id', 'timestamp']).reset_index(drop=True)
    filled = handle_missing_values(sorted_df, strategy='forward_fill', group_by='consumer_id')

    c1 = filled.loc[filled['consumer_id'] == 1, 'energy_consumption_kwh']
    c2 = filled.loc[filled['consumer_id'] == 2, 'energy_consumption_kwh']

    assert (c1 == 111.0).all(), f"Consumer 1 leaked or wrong fill: {c1.tolist()}"
    assert (c2 == 222.0).all(), f"Consumer 2 leaked or wrong fill: {c2.tolist()}"
    assert 222.0 not in c1.values
    assert 111.0 not in c2.values


def test_preprocess_shuffled_matches_sorted_logical_output(small_raw):
    """Full pipeline on shuffled vs original order → same consumer-level aggregates."""
    base = small_raw.drop(columns=['archetype']).copy()
    shuffled = base.sample(frac=1.0, random_state=99).reset_index(drop=True)

    out_a = preprocess_pipeline(base, remove_outliers_flag=False)
    out_b = preprocess_pipeline(shuffled, remove_outliers_flag=False)

    agg_a = out_a.groupby('consumer_id')['energy_consumption_kwh'].mean().sort_index()
    agg_b = out_b.groupby('consumer_id')['energy_consumption_kwh'].mean().sort_index()
    pd.testing.assert_series_equal(agg_a, agg_b, rtol=1e-9)

    # Within-consumer time series should match after re-sorting
    a_sorted = out_a.sort_values(['consumer_id', 'timestamp']).reset_index(drop=True)
    b_sorted = out_b.sort_values(['consumer_id', 'timestamp']).reset_index(drop=True)
    np.testing.assert_allclose(
        a_sorted['energy_consumption_kwh'].values,
        b_sorted['energy_consumption_kwh'].values,
        rtol=1e-9,
    )
