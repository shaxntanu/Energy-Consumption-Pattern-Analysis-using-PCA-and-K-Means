"""Tests for the zoom hint.

The hint is JavaScript, so these tests check the contract that JavaScript has to
honour rather than its behaviour in a browser: that the delivered frame is fully
substituted, that it keeps the pieces the design depends on, and that it decides
"zoomed" by measuring how much of each axis is on screen rather than by reading
the autorange flag - which several figures here switch off in their own layout.
"""
import re

import pytest

import dashboard_charts as ch
import dashboard_zoom as zoom
from energy_analysis import AnalysisConfig, EnergyAnalysis


@pytest.fixture(scope='module')
def payload():
    return zoom.payload()


def test_no_placeholder_survives_substitution(payload):
    """A leftover slot would be a syntax error in the browser and silent here."""
    assert not re.search(r'__[A-Z]+__', payload)
    assert 'undefined' not in payload
    assert payload.startswith('<script>') and payload.endswith('</script>')


def test_the_goo_filter_is_intact(payload):
    """The blob and the label merge through this filter; its values are the effect."""
    assert 'feGaussianBlur' in payload and 'stdDeviation=' in payload
    assert '0 0 0 18 -7' in payload
    assert 'feComposite' in payload and 'operator=\\"atop\\"' in payload
    assert 'filter: url(\\"#zoomhint-goo\\")' in payload


def test_it_says_what_the_gesture_is(payload):
    assert zoom.ZOOMED_LABEL in payload
    assert zoom.RESET_LABEL in payload
    assert 'DOUBLE-CLICK' in zoom.RESET_LABEL


def test_it_cannot_obstruct_the_chart(payload):
    """Pointer-transparent, out of the plotting area, and self-dismissing."""
    assert 'pointer-events: none' in payload
    assert 'position: absolute' in payload
    assert str(zoom.HOLD_MS) in payload
    assert 'setTimeout' in payload


def test_it_respects_reduced_motion_and_small_screens(payload):
    assert 'prefers-reduced-motion' in payload
    assert 'max-width: 640px' in payload


def test_it_is_hidden_from_assistive_technology(payload):
    """It restates a mouse gesture, so announcing it would only interrupt."""
    assert 'aria-hidden' in payload


def test_it_uses_the_project_palette_not_the_source_component(payload):
    """The borrowed component was magenta on black; this one has to belong here."""
    from dashboard_ui import CYAN, GREEN
    assert CYAN.lower() in payload.lower()
    assert GREEN.lower() in payload.lower()
    assert '#ff00ff' not in payload.lower()
    assert 'Syncopate' not in payload
    assert 'ENTER THE VOID' not in payload


def test_it_installs_only_one_set_of_listeners(payload):
    """Each rerun replaces the frame, so the old listeners must be handed back."""
    assert '__zoomhintTeardown' in payload
    assert 'removeEventListener' in payload
    # Every listener added must be handed back, or reruns accumulate them.
    added = re.findall(r'addEventListener\("(\w+)", (\w+), (\w+)\)', payload)
    removed = re.findall(r'removeEventListener\("(\w+)", (\w+), (\w+)\)', payload)
    assert added and sorted(added) == sorted(removed)


def test_zoom_is_decided_by_span_not_autorange(payload):
    """Reading autorange would be wrong here, and the code must not do it.

    Figures in this project pin an explicit hour range, which turns autorange off
    at build time; a hint keyed on that flag would appear on an untouched chart.
    The check is for a property *read* rather than the bare word, because the
    reason for avoiding it is written in a comment.
    """
    assert not re.search(r'\.autorange|\[["\']autorange', payload)
    assert '_fullLayout' in payload
    assert 'function spans(' in payload


def test_a_reset_is_told_apart_from_a_zoom(payload):
    """The two gestures move the same axes in opposite directions.

    A comparison that only asked "did the range change" would fire the hint on
    the double-click that resets the chart, which is the one moment the reader
    has already found the way out. Widening has to hide, not show.
    """
    assert 'function verdict(' in payload
    # Narrower shows, wider hides; the sign of the comparison is the whole rule.
    assert 'narrower' in payload and 'wider' in payload
    assert re.search(r'moved > 0.*show', payload, re.S)
    assert re.search(r'moved < 0.*hide', payload, re.S)
    # A pan changes neither span, so it must leave the marker alone.
    assert 'return 0;' in payload


@pytest.fixture(scope='module')
def results(tmp_path_factory):
    config = AnalysisConfig(
        n_consumers=40, n_days=14, feature_set='behavioral', test_stability=False,
        output_dir=str(tmp_path_factory.mktemp('out')),
        model_dir=str(tmp_path_factory.mktemp('models')),
        experiment_name='zoom_test', k_range=(2, 5),
    )
    return EnergyAnalysis(config).run()


def test_some_figures_really_do_pin_their_range(results):
    """The premise of the range comparison, checked against the real figures.

    If no figure pinned a range, keying the hint on autorange would have been
    fine and this module would be over-engineered. At least one does.
    """
    pinned = 0
    for factory in (ch.load_shape_chart, ch.eda_hourly_chart, ch.pca_variance_chart):
        fig = factory(results)
        if fig.layout.xaxis.range is not None:
            pinned += 1
    assert pinned >= 1


def test_a_gesture_that_ends_off_the_chart_still_counts(payload):
    """Plotly applies a box zoom even if the mouse is released elsewhere.

    Release over the sidebar or outside the window and the zoom lands but the
    mouseup does not, so the figure has to be carried from the start of the
    gesture instead of looked up again at the end.
    """
    assert re.search(r'plotUnder\(event\.target\) \|\| active', payload)


def test_the_reset_gesture_is_left_to_plotly(results):
    """Plotly's own double-click reset must stay enabled.

    The hint advertises that gesture, so a figure that disabled it would make the
    hint a false instruction.
    """
    fig = ch.load_shape_chart(results)
    assert fig.layout.xaxis.fixedrange in (None, False)
    assert fig.layout.yaxis.fixedrange in (None, False)
    assert fig.layout.dragmode != False  # noqa: E712 - a literal False would disable it
