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


# --- the cluster identity card ------------------------------------------------

def test_only_the_identity_card_is_three_dimensional(css):
    """The tilt is the point of one card, and would be noise on the rest.

    Reference cards, step cards and metric cards carry text to be read; rotating
    them would cost legibility and buy nothing.
    """
    for match in re.finditer(r'([^{}]*)\{([^{}]*)\}', css):
        selector, block = match.group(1), match.group(2)
        if 'rotate3d' in block or 'preserve-3d' in block or 'perspective:' in block:
            assert 'arch' in selector, selector


def test_the_card_is_flat_until_it_is_hovered(css):
    """A card that is already tilted is harder to read for no reason."""
    rest = _rules_for(css, '.arch-card')[0]
    assert 'rotate3d' not in rest
    hover = _rules_for(css, '.arch-3d:hover .arch-card')[0]
    assert 'rotate3d' in hover


def test_the_tilt_is_gentler_than_the_reference(css):
    """Thirty degrees distorts the bullet list enough to need re-reading."""
    hover = _rules_for(css, '.arch-3d:hover .arch-card')[0]
    angle = re.search(r'rotate3d\([^)]*?(\d+)deg\)', hover)
    assert angle and int(angle.group(1)) <= 20


def test_the_card_is_coloured_by_the_cluster_not_by_a_brand(css):
    """The reference's lime is replaced by a tint of the cluster's own colour."""
    body = _rules_for(css, '.arch-card .arch-body')[0]
    assert 'var(--swatch' in body
    assert '8ed500' not in css.lower()
    # A tint, because the qualitative palette at full strength leaves the text on
    # top of it no contrast.
    assert 'color-mix' in body
    # And a plain colour first, for a browser that cannot mix.
    assert body.index('background: var(--panel-hi)') < body.index('color-mix')


def test_the_card_stands_still_for_a_reader_who_asked_for_less_motion(css):
    reduced = css.split('@media (prefers-reduced-motion: reduce)')
    assert any('.arch-3d:hover .arch-card' in part and 'transform: none' in part
               for part in reduced[1:])


def test_the_corner_box_is_left_out_when_there_is_no_figure_for_it(monkeypatch):
    """An empty box would read as a missing value rather than an absent one."""
    captured = []
    monkeypatch.setattr(ui.st, 'markdown', lambda html, **kw: captured.append(html))
    ui.archetype_card('Evening-Peaking', '#B085F5', '49 consumers', ['a', 'b'])
    assert 'arch-badge' not in captured[0]
    captured.clear()
    ui.archetype_card('Evening-Peaking', '#B085F5', '49 consumers', ['a', 'b'],
                      badge='24.5%')
    assert '<div class="arch-badge">24.5%</div>' in captured[0]


def test_the_card_carries_the_cluster_colour_as_a_variable(monkeypatch):
    """One value in the markup drives the border, the dot and the corner box."""
    captured = []
    monkeypatch.setattr(ui.st, 'markdown', lambda html, **kw: captured.append(html))
    ui.archetype_card('Flat All-Day', '#3BC9DE', '57 consumers', ['near-flat'])
    assert '--swatch:#3BC9DE' in captured[0]
    assert captured[0].count('#3BC9DE') == 1


# --- what a reader can select -------------------------------------------------

def _unselectable(css: str) -> str:
    """The selector lists of every rule that switches selection off."""
    parts = []
    for match in re.finditer(r'([^{}]+)\{([^{}]*)\}', css):
        if 'user-select: none' in match.group(2):
            parts.append(match.group(1))
    return ' '.join(parts)


def test_selection_is_never_switched_off_wholesale(css):
    """The one failure mode that would matter: nobody can quote the work.

    A blanket rule is easy to write and hard to notice, so it is named here
    explicitly rather than left to the per-selector checks below.
    """
    for selector in re.findall(r'([^{}]+)\{[^{}]*user-select: none[^{}]*\}', css):
        for part in selector.split(','):
            part = part.strip()
            assert part not in ('*', 'body', 'html', '.stApp', '.block-container')
            assert not part.endswith('*')


def test_the_chrome_a_double_click_lands_on_is_unselectable(css):
    """Eyebrows, structural labels, sequence numbers and control names."""
    off = _unselectable(css)
    for selector in ('.kicker', '.nav-group', '.insight .k', '.pipe .step .n',
                     '.masthead .brand', '[data-testid="stTab"]'):
        assert selector in off, selector
    # Both button areas, since either one is a label on a control.
    assert '[data-testid="stMain"] .stButton > button' in off
    assert '[data-testid="stSidebar"] .stButton > button' in off


def test_the_work_itself_stays_selectable(css):
    """Anything a reader might quote must not appear in a selection-off rule.

    The bibliographic values are the sharpest case: a citation nobody can copy is
    worse than no citation card at all.
    """
    off = _unselectable(css)
    for selector in ('.hero h1', '.hero .lede', '.note', '.tag',
                     '.ref-card .ref-title', '.ref-card .ref-authors',
                     '.ref-card .ref-grid .rv', '.ref-card .ref-why',
                     '.arch-card li', '.insight .v', '[data-testid="stMetricValue"]'):
        assert selector not in off, selector


def test_the_reference_cards_lose_only_their_label_column(css):
    """The keys are structure; the values beside them are the citation."""
    off = _unselectable(css)
    assert '.ref-card .ref-grid .rk' in off
    assert '.rv' not in off
