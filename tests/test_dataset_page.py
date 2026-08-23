"""Tests for the dataset explorer's charts.

The explorer shows the user a consumer and then tells them which cluster that
consumer landed in. That claim is only worth making if the mapping comes from
the same rows the model was fitted on, so these tests check the mapping against
the fitted model's own prediction rather than against a re-derived guess.
"""
import numpy as np
import pytest

import dashboard_charts as ch
from energy_analysis import AnalysisConfig, EnergyAnalysis


@pytest.fixture(scope='module')
def results(tmp_path_factory):
    config = AnalysisConfig(
        n_consumers=40,
        n_days=14,
        feature_set='behavioral',
        test_stability=False,
        output_dir=str(tmp_path_factory.mktemp('out')),
        model_dir=str(tmp_path_factory.mktemp('models')),
        experiment_name='dataset_page_test',
        k_range=(2, 5),
    )
    return EnergyAnalysis(config).run()


def test_consumer_ids_match_the_panel(results):
    ids = ch.consumer_ids(results)
    assert len(ids) == results.config.n_consumers
    assert sorted(ids) == ids
    assert set(ids) == set(results.preprocessed_data['consumer_id'].unique())


def test_cluster_map_covers_every_consumer(results):
    mapping = ch.consumer_cluster_map(results)
    assert set(mapping) == set(ch.consumer_ids(results))
    assert set(mapping.values()) == set(range(results.optimal_k))


def test_cluster_map_agrees_with_the_fitted_model(results):
    """The page must not invent an assignment of its own.

    Re-predicting from the saved model and PCA scores is an independent route to
    the same answer; if the map were built from a different row order the two
    would disagree.
    """
    mapping = ch.consumer_cluster_map(results)
    predicted = results.kmeans_model.predict(results.pca_transformed)
    frame = results.features_combined
    for consumer_id, label in zip(frame['consumer_id'].to_numpy(), predicted):
        assert mapping[int(consumer_id)] == int(label)


def test_cluster_map_sizes_match_the_profiles(results):
    mapping = ch.consumer_cluster_map(results)
    counts = {k: sum(1 for v in mapping.values() if v == k) for k in set(mapping.values())}
    for _, prof in results.cluster_profiles.iterrows():
        assert counts[int(prof['cluster'])] == int(prof['size'])


def test_profile_chart_plots_that_consumer_and_the_population(results):
    consumer_id = ch.consumer_ids(results)[0]
    fig = ch.consumer_profile_chart(results, consumer_id)
    assert len(fig.data) == 2
    mine = results.preprocessed_data
    mine = mine.loc[mine['consumer_id'] == consumer_id]
    expected = mine.groupby('hour')['energy_consumption_kwh'].mean()
    plotted = next(t for t in fig.data if str(consumer_id) in str(t.name))
    assert len(plotted.y) == 24
    np.testing.assert_allclose(np.asarray(plotted.y, dtype=float),
                               expected.reindex(range(24)).to_numpy(), rtol=1e-9)


def test_shape_chart_is_normalised(results):
    """Every line on the shape chart is a share of the day, so each sums to one."""
    fig = ch.consumer_shape_chart(results, ch.consumer_ids(results)[0])
    assert len(fig.data) == 3
    for trace in fig.data:
        assert abs(float(np.nansum(np.asarray(trace.y, dtype=float))) - 1.0) < 1e-6


def test_day_heatmap_is_a_categorical_grid(results):
    """One row per recorded day, hours across, on a category axis.

    Most of the row labels parse as dates, so an inferred axis type would thin
    the ticks and misplace the rows marked as weekends.
    """
    fig = ch.consumer_day_heatmap(results, ch.consumer_ids(results)[0])
    heat = fig.data[0]
    assert fig.layout.yaxis.type == 'category'
    assert len(heat.y) == results.config.n_days
    assert np.asarray(heat.z).shape == (results.config.n_days, 24)
    assert any('weekend' in str(label) for label in heat.y)
    assert list(heat.x) == list(range(24))


def test_cluster_size_chart_matches_the_profiles(results):
    fig = ch.cluster_size_chart(results)
    bar = fig.data[0]
    assert sum(int(v) for v in bar.x) == results.config.n_consumers
    expected = results.cluster_profiles.sort_values('cluster')
    assert [int(v) for v in bar.x] == [int(s) for s in expected['size']]
    assert list(bar.y) == [str(n) for n in expected['cluster_name']]


def test_charts_carry_no_emoji(results):
    consumer_id = ch.consumer_ids(results)[0]
    figs = [ch.consumer_profile_chart(results, consumer_id),
            ch.consumer_shape_chart(results, consumer_id),
            ch.consumer_day_heatmap(results, consumer_id),
            ch.cluster_size_chart(results)]
    import re
    for fig in figs:
        assert not re.search(r'[\U0001F000-\U0001FAFF]', fig.to_json())
