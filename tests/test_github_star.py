"""Tests for the star button and the count behind it.

The rule the button has to keep is that the number on it is either GitHub's or
absent. So these check both halves: that the count is only ever reported when the
API really said it, and that the button leaves the pill off when it was not.

The network is never called here. ``star_count`` is exercised against stubbed
responses, because a test that depended on GitHub answering would fail for
reasons that have nothing to do with this repository.
"""
import io
import json
import urllib.error

import pytest

import dashboard_github as gh
import dashboard_ui as ui
from dashboard_content import REPO_URL


# --- the URL the count is asked for ------------------------------------------

def test_the_repo_path_comes_from_the_url_the_app_links_to():
    """Parsed, not hard-coded, so the link and the count cannot disagree."""
    assert gh.repo_path(REPO_URL) == (
        'shaxntanu/Energy-Consumption-Pattern-Analysis-using-PCA-and-K-Means'
    )


@pytest.mark.parametrize('url', [
    'https://gitlab.com/owner/name',        # another host entirely
    'https://github.com/owner',             # no repository
    'https://github.com/',                  # nothing at all
    'ftp://github.com/owner/name',          # not a web URL
    'not a url',
    '',
])
def test_anything_that_is_not_a_github_repo_is_refused(url):
    """This builds an API request, so it must not be talkable into other hosts."""
    assert gh.repo_path(url) is None


def test_a_git_suffix_and_extra_path_are_tolerated():
    assert gh.repo_path('https://github.com/owner/name.git') == 'owner/name'
    assert gh.repo_path('https://github.com/owner/name/tree/main') == 'owner/name'


# --- the count itself ---------------------------------------------------------

def _response(payload, status=200):
    """A stand-in for what urlopen returns: a context manager with .read()."""
    class _Resp:
        def __init__(self):
            self.status = status
            self._body = io.BytesIO(json.dumps(payload).encode())

        def __enter__(self):
            return self

        def __exit__(self, *exc):
            return False

        def read(self):
            return self._body.read()

    return _Resp()


@pytest.fixture(autouse=True)
def uncached():
    """st.cache_data would otherwise carry one stub's answer into the next test."""
    gh.star_count.clear()
    yield
    gh.star_count.clear()


def test_a_real_count_is_reported(monkeypatch):
    monkeypatch.setattr(gh.urllib.request, 'urlopen',
                        lambda *a, **k: _response({'stargazers_count': 42}))
    assert gh.star_count(REPO_URL) == 42


def test_a_private_repository_reports_nothing(monkeypatch):
    """An unauthenticated request for a private repository is a 404."""
    def _raise(*args, **kwargs):
        raise urllib.error.HTTPError(REPO_URL, 404, 'Not Found', {}, None)

    monkeypatch.setattr(gh.urllib.request, 'urlopen', _raise)
    assert gh.star_count(REPO_URL) is None


def test_no_network_reports_nothing(monkeypatch):
    def _raise(*args, **kwargs):
        raise urllib.error.URLError('getaddrinfo failed')

    monkeypatch.setattr(gh.urllib.request, 'urlopen', _raise)
    assert gh.star_count(REPO_URL) is None


def test_a_timeout_reports_nothing(monkeypatch):
    def _raise(*args, **kwargs):
        raise TimeoutError('timed out')

    monkeypatch.setattr(gh.urllib.request, 'urlopen', _raise)
    assert gh.star_count(REPO_URL) is None


@pytest.mark.parametrize('payload', [
    {},                                  # no such field
    {'stargazers_count': None},
    {'stargazers_count': 'many'},
    {'stargazers_count': True},          # a bool is an int and would print as True
    {'stargazers_count': -1},
    ['not', 'an', 'object'],
])
def test_a_body_that_is_not_a_count_reports_nothing(monkeypatch, payload):
    """Better no number than a number this code had to guess at."""
    monkeypatch.setattr(gh.urllib.request, 'urlopen',
                        lambda *a, **k: _response(payload))
    assert gh.star_count(REPO_URL) is None


def test_a_non_200_reports_nothing(monkeypatch):
    monkeypatch.setattr(gh.urllib.request, 'urlopen',
                        lambda *a, **k: _response({'stargazers_count': 9}, status=204))
    assert gh.star_count(REPO_URL) is None


def test_the_request_identifies_itself_and_gives_up_quickly(monkeypatch):
    """GitHub rejects a missing User-Agent, and a slow reply must not hold the page."""
    seen = {}

    def _capture(request, timeout=None):
        seen['url'] = request.full_url
        seen['headers'] = {k.lower(): v for k, v in request.header_items()}
        seen['timeout'] = timeout
        return _response({'stargazers_count': 1})

    monkeypatch.setattr(gh.urllib.request, 'urlopen', _capture)
    gh.star_count(REPO_URL)
    assert seen['url'].startswith('https://api.github.com/repos/')
    assert 'user-agent' in seen['headers']
    assert seen['timeout'] is not None and seen['timeout'] <= 5
    # No credential is read or sent; an authorization header would mean one is.
    assert 'authorization' not in seen['headers']


# --- how the number is written down ------------------------------------------

@pytest.mark.parametrize('count, text', [
    (0, '0'), (1, '1'), (7, '7'), (999, '999'),
    (1000, '1k'), (1099, '1k'), (1250, '1.2k'),
    (9999, '9.9k'), (10000, '10k'), (12345, '12k'),
])
def test_the_count_is_never_rounded_up(count, text):
    """Truncated, so the button cannot claim a star that was not given."""
    assert gh.format_count(count) == text


# --- the button ---------------------------------------------------------------

def _button_html(monkeypatch, **kwargs):
    """Render star_button and return the HTML it handed to Streamlit."""
    captured = []
    monkeypatch.setattr(ui.st, 'markdown',
                        lambda html, **kw: captured.append(html))
    ui.star_button(REPO_URL, **kwargs)
    assert len(captured) == 1
    return captured[0]


def test_the_button_links_to_the_real_repository(monkeypatch):
    html = _button_html(monkeypatch, count=3)
    assert f'href="{REPO_URL}"' in html
    assert 'target="_blank"' in html and 'rel="noopener"' in html


def test_the_button_shows_a_count_it_was_given(monkeypatch):
    html = _button_html(monkeypatch, count=1250)
    assert 'gh-count' in html
    assert '1.2k' in html


def test_the_button_shows_no_count_when_there_is_none(monkeypatch):
    """The whole pill goes, rather than a zero or a dash standing in for a fact."""
    import re
    html = _button_html(monkeypatch, count=None)
    assert 'gh-count' not in html
    # Everything outside the tags is what a reader sees; the SVG path data is
    # full of digits and has to be left out of a check about visible text.
    visible = re.sub(r'<[^>]+>', '', html).strip()
    assert visible == 'Star on GitHub'


def test_the_button_is_a_link_with_readable_text(monkeypatch):
    """It has to stay keyboard-reachable and announced, so it stays an anchor."""
    html = _button_html(monkeypatch, count=5)
    assert html.startswith('<a ') and html.endswith('</a>')
    assert 'Star on GitHub' in html
    # The icons carry no meaning the text does not already give.
    assert html.count('aria-hidden="true"') == 2
    # A bare digit would be read out with nothing to attach it to.
    assert '<span class="sr-only"> stars</span>' in html


def test_the_button_carries_no_emoji(monkeypatch):
    import re
    html = _button_html(monkeypatch, count=5)
    assert not re.search(r'[\U0001F300-\U0001FAFF]', html)


def test_the_style_the_button_needs_is_in_the_stylesheet():
    css = ui._css()
    assert '.gh-star' in css and '.gh-count' in css
    # Black, as every repository page's star button is.
    assert 'background: #000' in css
    # The label is chrome and unselectable; the count is a fact and is not.
    assert 'user-select: none' in css.split('.gh-star .gh-face')[1].split('}')[0]
    # The hover shine and the amber star, and neither one forced on a reader who
    # asked for less motion.
    assert '.gh-star:hover::after' in css
    assert 'var(--amber)' in css
    assert '.gh-star, .gh-star::after' in css
    # Clipped rather than hidden, so it stays in the accessibility tree.
    assert '.sr-only' in css and 'clip: rect(0, 0, 0, 0)' in css
