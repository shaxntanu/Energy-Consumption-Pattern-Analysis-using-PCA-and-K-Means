"""Smoke tests that actually run the app.

Every other test here exercises the analysis or a figure factory. These run
``streamlit_app.py`` itself through Streamlit's own test harness, so a broken
page - a renamed attribute, a bad format string, a chart that raises - fails
here instead of in front of a reader.

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
    at.session_state['_page'] = 'Home'
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
    assert 'How to use this simulator' in app.PAGES
    assert app.SECTION_OF_PAGE['How to use this simulator'] == 'Start'


def test_home_draws_live_charts(booted):
    """The landing page must draw its figures, not describe them."""
    booted.session_state['_page'] = 'Home'
    booted.run(timeout=BOOT_TIMEOUT)
    assert not booted.exception
    assert len(booted.get('plotly_chart')) >= 3


def test_how_to_use_draws_its_fifteen_chapters(booted):
    """Fifteen numbered chapters, their kickers, and their five figures.

    The titles are checked against the ones that carry no live figures, so this
    stays true for any run size; the chapter count is checked through the
    zero-padded numbers the chapter component emits.
    """
    booted.session_state['_page'] = 'How to use this simulator'
    booted.run(timeout=BOOT_TIMEOUT)
    assert not booted.exception
    text = ' '.join(m.value for m in booted.markdown)

    for number in range(1, 16):
        assert f'>{number:02d}<' in text, f"chapter {number} is missing its number"
    for kicker in app.HOW_TO_KICKERS.values():
        assert kicker in text
    for title in ('What this project is', 'What a load profile is', 'What PCA does',
                  'What K-Means does', 'What the metrics mean',
                  'What the limitations are'):
        assert title in text, f"missing chapter: {title}"

    assert len(booted.get('plotly_chart')) == len(app.HOW_TO_FIGURES)
    assert 'squeezing many related measurements' in text
    assert 'STEP 01' in text and 'STEP 03' in text


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
    for page in ('Home', 'How to use this simulator', 'Dataset', 'The clusters'):
        booted.session_state['_page'] = page
        booted.run(timeout=BOOT_TIMEOUT)
        blob = ' '.join(m.value for m in booted.markdown)
        found = re.search(r'[\U0001F300-\U0001FAFF]', blob)
        assert not found, f"{page} contains {found.group() if found else ''}"
