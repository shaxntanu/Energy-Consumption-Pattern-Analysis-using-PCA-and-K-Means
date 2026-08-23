"""Tests for the dashboard's narrative layer.

The story and the beginner's guide quote figures from the run. That makes them a
place where the interface can quietly start disagreeing with the analysis: a
renamed attribute, a metric read from the wrong object, a number typed in by
hand. These tests run the real pipeline once and then check that every quoted
figure comes from that object and matches it.
"""
import re

import pytest

import dashboard_content as content
from energy_analysis import AnalysisConfig, EnergyAnalysis


@pytest.fixture(scope='module')
def results(tmp_path_factory):
    """One small but complete run, with stability on so the guide can quote it."""
    out = tmp_path_factory.mktemp('out')
    models = tmp_path_factory.mktemp('models')
    config = AnalysisConfig(
        n_consumers=40,
        n_days=14,
        feature_set='behavioral',
        test_stability=True,
        output_dir=str(out),
        model_dir=str(models),
        experiment_name='content_test',
        k_range=(2, 5),
    )
    return EnergyAnalysis(config).run()


def test_references_are_complete_and_use_dois(results):
    """Every reference carries the fields a reader needs to find the paper."""
    required = {'title', 'authors', 'year', 'venue', 'method', 'dataset', 'why', 'url'}
    assert len(content.REFERENCES) >= 7
    for ref in content.REFERENCES:
        assert required <= set(ref), f"{ref.get('title')} is missing fields"
        assert all(str(ref[k]).strip() for k in required), f"{ref.get('title')} has a blank field"
        assert ref['url'].startswith('https://doi.org/'), f"{ref['title']} is not a DOI link"
        assert re.fullmatch(r'(19|20)\d{2}', ref['year']), f"{ref['title']} has an odd year"


def test_reference_titles_are_unique():
    titles = [r['title'] for r in content.REFERENCES]
    assert len(titles) == len(set(titles))


def test_story_steps_are_well_formed(results):
    steps = content.story_steps(results)
    assert len(steps) == 8
    for step in steps:
        assert step['kicker'] and step['title'] and step['body']
        for tile in step.get('tiles', []):
            assert tile['label'] and str(tile['value']).strip()


def test_story_quotes_the_run_not_a_constant(results):
    """The headline figures in the prose must be the run's own figures."""
    steps = content.story_steps(results)
    blob = ' '.join(s['title'] + ' ' + s['body'] for s in steps)
    n_features = len(results.feature_names)

    assert f'{n_features} ways to describe a curve' in blob
    assert f'{n_features} behavioural features' in blob
    assert f'{results.n_pca_components} components' in blob
    assert f'{results.silhouette_for_k(results.optimal_k):.2f}' in blob

    features_step = next(s for s in steps if s['kicker'] == 'The features')
    values = [str(t['value']) for t in features_step['tiles']]
    assert str(n_features) in values


def test_story_never_hard_codes_the_reference_run(results):
    """A different run must not still be describing the committed one.

    The committed reference run has 51 features and 14 components. This run is
    smaller, so those strings appearing here would mean a number was typed in
    rather than read.
    """
    small = content.story_steps(results)
    blob = ' '.join(s['title'] + ' ' + s['body'] for s in small)
    if len(results.feature_names) != 51:
        assert '51 behavioural features' not in blob
    if results.n_pca_components != 14:
        assert '14 components' not in blob


def test_how_to_use_covers_the_brief(results):
    """The guide has to answer all fifteen beginner questions, in order."""
    chapters = content.how_to_use_chapters(results)
    assert len(chapters) == 15
    for chap in chapters:
        assert chap['title'] and len(chap['body']) > 120
    heads = [c['title'].lower() for c in chapters]
    for topic in ('what this project is', 'load profile', 'features are', 'pca does',
                  'k-means does', 'cluster means', 'graphs mean', 'metrics mean',
                  'limitations are'):
        assert any(topic in h for h in heads), f"no chapter covers {topic}"


def test_how_to_use_quotes_live_metrics(results):
    chapters = content.how_to_use_chapters(results)
    blob = ' '.join(c['body'] for c in chapters)
    assert f'{results.silhouette_for_k(results.optimal_k):.3f}' in blob
    assert f'K = {results.optimal_k}' in blob
    assert results.config.config_hash() in blob
    for _, prof in results.cluster_profiles.iterrows():
        assert str(prof['cluster_name']) in blob


def test_no_unfilled_placeholders(results):
    """Nothing should reach the page as a leftover format slot or a missing value.

    Both patterns are matched narrowly on purpose. 'dominant' contains 'nan',
    and "None of them is the consumer's total size" is good prose - so the test
    looks for the shapes a stringified Python ``None``/``nan`` actually takes
    when it lands in a sentence: inside emphasis, in parentheses, or against
    punctuation where a figure was expected.
    """
    texts = [s['title'] + s['body'] for s in content.story_steps(results)]
    texts += [c['title'] + c['body'] for c in content.how_to_use_chapters(results)]
    leaked = re.compile(r'\*\*(None|nan)|[(\[=]\s*(None|nan)\b|\b(None|nan)[).,;]',
                        re.IGNORECASE)
    for text in texts:
        assert '{' not in text and '}' not in text, f"unfilled format slot in: {text[:80]}"
        assert not leaked.search(text), f"a missing value reached the page in: {text[:80]}"


def test_synthetic_provenance_is_stated(results):
    """The guide must not let a reader forget the data is generated."""
    blob = ' '.join(c['body'] for c in content.how_to_use_chapters(results)).lower()
    assert 'synthetic' in blob
    assert 'not real' in blob or 'do not exist' in blob or 'nothing here' in blob


def test_no_emoji_in_narrative(results):
    """House rule: no emoji anywhere in the application text."""
    blob = ' '.join(
        [s['title'] + s['body'] for s in content.story_steps(results)]
        + [c['title'] + c['body'] for c in content.how_to_use_chapters(results)]
        + [r['title'] + r['why'] for r in content.REFERENCES]
    )
    assert not re.search(r'[\U0001F000-\U0001FAFF☀-➿]', blob)
