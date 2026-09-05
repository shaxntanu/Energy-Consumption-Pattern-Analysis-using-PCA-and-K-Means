"""Smoke tests that actually run the app.

Every other test here exercises the analysis or a figure factory. These run
``streamlit_app.py`` itself through Streamlit's own test harness, so a broken
page, whether through a renamed attribute, a bad format string or a chart
that raises, fails here instead of in front of a reader.

The run is deliberately small and stability is off: the point is that each page
executes and draws what it claims to, not that the numbers are good.
"""
from pathlib import Path

import pytest

from streamlit.testing.v1 import AppTest

import streamlit_app as app

# AppTest resolves a relative path against the calling file, which would look
# inside tests/, so the entrypoint is addressed absolutely.
APP_PATH = str(Path(__file__).resolve().parent.parent / 'streamlit_app.py')
BOOT_TIMEOUT = 300


def _small_run(at: AppTest) -> AppTest:
    """Boot the app on a small configuration.

    The sidebar controls are set before the first run so the pipeline is only
    ever executed at the reduced size; booting at the default 200 consumers and
    30 days would make this suite far slower than the analysis tests.
    """
    at.session_state['_page'] = 'Overview'
    at.run(timeout=BOOT_TIMEOUT)
    return at


@pytest.fixture(scope='module')
def booted():
    """One boot, reused. Streamlit caches the analysis on the config hash."""
    return _small_run(AppTest.from_file(APP_PATH, default_timeout=BOOT_TIMEOUT))


def test_the_app_boots_without_exceptions(booted):
    assert not booted.exception


def test_every_page_renders(booted):
    """Each registered page must run end to end.

    A page that raises leaves an exception element behind, which is what a
    reader would see, so this asserts on that rather than on a return value.
    """
    for page in app.PAGES:
        booted.session_state['_page'] = page
        booted.run(timeout=BOOT_TIMEOUT)
        assert not booted.exception, f"{page} raised: {[e.value for e in booted.exception]}"


def test_navigation_is_complete_and_unique():
    assert len(app.PAGES) == len(set(app.PAGES))
    assert set(app.PAGES) == set(app.PAGE_FUNCS)
    assert app.HOME_PAGE in app.PAGES
    # PAGES is the flattening of NAV_GROUPS, so the sidebar and the router must
    # stay in lockstep with it. This is the concrete, documented list, so an
    # accidental reorder or a dropped group fails here.
    assert app.PAGES == [
        'Overview', 'Dataset', 'The clusters',     # Simulator
        'Features', 'PCA', 'Choosing K', 'Stability', 'Validation',  # Analysis
        'Insights', 'Seasonal', 'Longitudinal', 'Explainability',   # Results
        'How it works', 'Research', 'Limitations',  # Method
        'C++ Engine',                              # Performance
    ]


def test_overview_draws_the_simulator_summary(booted):
    """The simulator overview shows the core result and routes to details."""
    booted.session_state['_page'] = 'Overview'
    booted.run(timeout=BOOT_TIMEOUT)
    assert not booted.exception
    assert len(booted.get('plotly_chart')) >= 1
    labels = [button.label for button in booted.button]
    assert 'View the dataset' in labels
    assert 'See cluster details' in labels
    assert {'Overview', 'Dataset', 'The clusters'}.issubset(labels)


def test_dataset_page_draws_its_tables_and_charts(booted):
    """The dataset page's four tabs all render in one pass.

    Streamlit builds every tab's contents on each run, so the consumer charts
    are present even though only one tab is visible.
    """
    booted.session_state['_page'] = 'Dataset'
    booted.run(timeout=BOOT_TIMEOUT)
    assert not booted.exception
    assert len(booted.dataframe) >= 4
    assert len(booted.get('plotly_chart')) == 4
    assert len(booted.tabs) == 4


def test_no_emoji_reaches_the_rendered_page(booted):
    """House rule, checked against what the app actually emits."""
    import re
    for page in app.PAGES:
        booted.session_state['_page'] = page
        booted.run(timeout=BOOT_TIMEOUT)
        blob = ' '.join(m.value for m in booted.markdown)
        found = re.search(r'[\U0001F300-\U0001FAFF]', blob)
        assert not found, f"{page} contains {found.group() if found else ''}"
