"""Tests for the styled controls: the call-to-action button and the checkbox.

Both are Streamlit's own widgets with a stylesheet over them, which is the whole
point - a hand-built div would have to reimplement focus, keyboard handling and
the accessible name, and would get one of them wrong. So what there is to test is
the stylesheet: that it restyles the real control instead of replacing it, that it
stays inside the area it is meant for, and that it does not quietly remove
anything a keyboard or a screen reader needs.

These read the CSS as text. That is a contract test, not a rendering test: it
cannot prove the button looks right, only that the rules the design depends on are
present and that the forbidden ones are absent.
"""
import re

import pytest

import dashboard_ui as ui


@pytest.fixture(scope='module')
def css():
    return ui._css()


def _rules_for(css: str, selector: str) -> list[str]:
    """Every declaration block whose selector list contains ``selector``."""
    blocks = []
    for match in re.finditer(r'([^{}]+)\{([^{}]*)\}', css):
        if selector in match.group(1):
            blocks.append(match.group(2))
    return blocks


# --- the call to action -------------------------------------------------------

def test_the_cta_treatment_is_confined_to_the_main_area(css):
    """The sidebar is navigation, and its buttons have their own quieter style.

    An unscoped .stButton rule would put the slab behind every nav item: the
    sidebar rules never mention the pseudo-elements, so specificity alone would
    not protect them. So every button rule has to name the area it belongs to,
    and the pseudo-elements have to belong to the main area only.
    """
    for match in re.finditer(r'([^{}]*\.stButton\s*>\s*button[^{}]*)\{', css):
        selector = match.group(1).strip()
        assert ('[data-testid="stMain"]' in selector
                or '[data-testid="stSidebar"]' in selector), selector
        if '::before' in selector or '::after' in selector:
            assert '[data-testid="stMain"]' in selector, selector


def test_the_cta_grows_from_pseudo_elements_not_the_button(css):
    """The label must not move, so the movement belongs to ::before and ::after."""
    assert '[data-testid="stMain"] .stButton > button::before' in css
    assert '[data-testid="stMain"] .stButton > button::after' in css
    hover = _rules_for(css, '.stButton > button:hover::before')
    assert hover and any('transform' in b and 'width' in b for b in hover)
    # The face itself keeps no background of its own, or there would be two.
    base = _rules_for(css, '[data-testid="stMain"] .stButton > button')[0]
    assert 'background: transparent' in base


def test_the_cta_label_sits_above_the_moving_layers(css):
    """Without this the growing wash crosses the text and it flickers."""
    block = _rules_for(css, '.stButton > button > div')
    assert block and 'z-index: 2' in block[0]


def test_the_cta_wash_is_faint_at_rest_and_accented_on_hover(css):
    """At rest it is glass; the colour arrives on hover, where it means something."""
    rest = _rules_for(css, '[data-testid="stMain"] .stButton > button::after')[0]
    assert 'rgba(255, 255, 255, 0.055)' in rest
    hover = _rules_for(css, '.stButton > button:hover::after')[0]
    assert 'rgba(59, 201, 222' in hover


def test_the_cta_stands_still_for_a_reader_who_asked_for_less_motion(css):
    reduced = css.split('@media (prefers-reduced-motion: reduce)')
    assert any('.stButton > button::before' in part for part in reduced[1:])


# --- the checkbox -------------------------------------------------------------

def test_the_checkbox_input_is_never_hidden(css):
    """The reference component set display:none on its input. That must not happen.

    Streamlit clips the real input to a pixel, which keeps it focusable and in the
    accessibility tree. display:none or visibility:hidden would take it out of the
    tab order, and the control would be mouse-only.
    """
    for block in _rules_for(css, '[data-testid="stCheckbox"]'):
        assert 'display: none' not in block
        assert 'visibility: hidden' not in block
    # Nothing in the stylesheet targets the input at all; it is left alone.
    assert not re.search(r'stCheckbox[^{}]*input[^{}:]*\{', css)


def test_the_checkbox_paint_follows_the_input_state(css):
    """Read from :checked, not from a class Streamlit might rename or reuse.

    A class-driven rule can end up out of step with the value the app received,
    which would mean the box on screen disagreeing with the analysis that ran.
    """
    assert '[data-testid="stCheckbox"] label:has(input:checked)' in css
    assert 'data-selected' not in css


def test_the_checked_box_is_visibly_different(css):
    """Not by colour alone: the tick appears as well, for anyone who cannot see it."""
    checked = _rules_for(css, 'label:has(input:checked) > div:first-of-type')
    assert checked and any('background' in b for b in checked)
    assert any('opacity: 1' in b for b in checked)


def test_the_focus_ring_is_drawn_on_the_box(css):
    """The input holds the focus but is a pixel wide, so its own ring is invisible."""
    block = _rules_for(css, 'label:has(input:focus-visible) > div:first-of-type')
    assert block and 'outline' in block[0]
    assert 'var(--cyan)' in block[0]


def test_the_box_is_round_and_sized_for_a_line_of_text(css):
    """The reference's shape, at a size that belongs beside a label.

    Its 50px was for a standalone control; here the checkbox sits in a settings
    panel next to a sentence.
    """
    block = _rules_for(css, '[data-testid="stCheckbox"] label > div:first-of-type')[0]
    assert 'border-radius: 50%' in block
    size = re.search(r'width:\s*(\d+)px', block)
    assert size and 12 <= int(size.group(1)) <= 28


def test_the_checkbox_uses_the_project_palette(css):
    """Adapted, not pasted: the reference was #191A1E and white on a 50px disc."""
    blocks = ' '.join(_rules_for(css, '[data-testid="stCheckbox"]'))
    assert 'var(--' in blocks
    assert '#191A1E'.lower() not in blocks.lower()


def test_the_checkbox_stands_still_for_a_reader_who_asked_for_less_motion(css):
    reduced = css.split('@media (prefers-reduced-motion: reduce)')
    assert any('stCheckbox' in part for part in reduced[1:])
