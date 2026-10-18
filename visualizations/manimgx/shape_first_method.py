"""Short ManimGX explainer for the project's shape-first clustering method.

The two load curves are deliberately illustrative: they share one daily shape
and differ only by scale. All pipeline counts refer to the committed reference
run documented in README.md.
"""
from __future__ import annotations

import math

import manimgx as m


BG = "#0F1519"
INK = "#E8EFED"
MUTED = "#A7B6B2"
LINE = "#2B393C"
PAPER = "#151E22"
TEAL = "#55B7AA"
TEAL_LIGHT = "#1B302F"
ORANGE = "#E4A16D"
ORANGE_LIGHT = "#34251D"
BLUE = "#91A8C4"
m.config.background_color = BG


def _daily_shape(hour: float) -> float:
    """A small, deterministic example profile with morning and evening peaks."""
    morning = 0.60 * math.exp(-((hour - 8.0) / 2.8) ** 2)
    evening = 1.00 * math.exp(-((hour - 19.0) / 3.2) ** 2)
    return 0.22 + morning + evening


def _curve_points(scale: float, *, x0: float, y0: float, width: float,
                  height: float) -> list[list[float]]:
    values = [_daily_shape(float(hour)) for hour in range(24)]
    peak = max(values)
    return [
        [x0 + hour / 23 * width, y0 + value / peak * height * scale, 0]
        for hour, value in enumerate(values)
    ]


def _curve(scale: float, color: str, *, x0: float = -6.0, y0: float = -0.8,
           width: float = 7.4, height: float = 2.75, opacity: float = 1.0) -> m.VGroup:
    points = _curve_points(scale, x0=x0, y0=y0, width=width, height=height)
    segments = [
        m.Line(start, end, color=color, stroke_width=5).set_opacity(opacity)
        for start, end in zip(points, points[1:])
    ]
    return m.VGroup(*segments)


def _chart_axes() -> m.VGroup:
    parts = [
        m.Line([-6.0, -0.8, 0], [1.45, -0.8, 0], color=LINE, stroke_width=2),
        m.Line([-6.0, -0.8, 0], [-6.0, 2.2, 0], color=LINE, stroke_width=2),
    ]
    for hour in (0, 6, 12, 18, 23):
        x = -6.0 + hour / 23 * 7.4
        parts.append(m.Line([x, -0.8, 0], [x, -0.91, 0], color=MUTED, stroke_width=1.5))
        parts.append(m.Text(str(hour), font_size=18, color=MUTED).move_to([x, -1.2, 0]))
    parts.append(m.Text("Hour of day", font_size=18, color=MUTED).move_to([-2.3, -1.65, 0]))
    return m.VGroup(*parts)


def _info_card(title: str, detail: str, color: str, tint: str,
               center: list[float]) -> tuple[m.Rectangle, m.Rectangle, m.Text, m.Text]:
    panel = m.Rectangle(
        width=3.8,
        height=1.15,
        color=LINE,
        fill_color=tint,
        fill_opacity=1,
        stroke_width=1.5,
    ).move_to(center)
    accent = m.Rectangle(
        width=0.09,
        height=1.15,
        color=color,
        fill_color=color,
        fill_opacity=1,
        stroke_width=0,
    ).move_to([center[0] - 1.85, center[1], 0])
    label = m.Text(title, font_size=19, color=INK).move_to([center[0], center[1] + 0.18, 0])
    value = m.Text(detail, font_size=16, color=color).move_to([center[0], center[1] - 0.2, 0])
    return panel, accent, label, value


class ShapeFirstMethod(m.Scene):
    def construct(self) -> None:
        title = m.Text(
            "Cluster by daily rhythm, not daily total",
            font_size=38,
            color=INK,
        ).to_edge(m.UP, buff=0.45)
        kicker = m.Text(
            "ENERGY CONSUMPTION PATTERN ANALYSIS",
            font_size=16,
            color=TEAL,
        ).next_to(title, m.DOWN, buff=0.18)
        self.play(m.FadeIn(title), m.FadeIn(kicker), run_time=0.8)

        stage_one = m.Text(
            "Same routine. Different amount of energy.",
            font_size=23,
            color=INK,
        ).move_to([-1.8, 2.15, 0])
        axes = _chart_axes()
        low_curve = _curve(0.48, TEAL)
        high_curve = _curve(0.96, ORANGE)
        legend_a = _info_card("Household A", "lower daily total", TEAL, TEAL_LIGHT,
                              [4.25, 0.75, 0])
        legend_b = _info_card("Household B", "about twice the total", ORANGE, ORANGE_LIGHT,
                              [4.25, -0.75, 0])
        self.play(
            m.Write(stage_one),
            m.Create(axes),
            m.Create(low_curve),
            m.Create(high_curve),
            m.FadeIn(legend_a[0]),
            m.FadeIn(legend_a[1]),
            m.FadeIn(legend_b[0]),
            m.FadeIn(legend_b[1]),
            run_time=1.4,
        )
        self.play(
            m.Write(legend_a[2]),
            m.Write(legend_a[3]),
            m.Write(legend_b[2]),
            m.Write(legend_b[3]),
            run_time=0.45,
        )
        self.wait(1.2)

        stage_two = m.Text(
            "Divide each hour by that household's daily total",
            font_size=22,
            color=INK,
        ).move_to([-1.7, 2.15, 0])
        normalized_a = _curve(0.82, TEAL)
        normalized_b = _curve(0.82, ORANGE, opacity=0.7)
        formula = m.Text(
            "hourly use  ÷  daily total",
            font_size=20,
            color=TEAL,
        ).move_to([4.25, 0.45, 0])
        result = m.Text(
            "The two shapes overlap",
            font_size=19,
            color=INK,
        ).move_to([4.25, -0.15, 0])
        keep = m.Text(
            "timing stays; scale drops out",
            font_size=15,
            color=MUTED,
        ).move_to([4.25, -0.62, 0])
        self.play(
            m.Transform(stage_one, stage_two),
            m.Transform(low_curve, normalized_a),
            m.Transform(high_curve, normalized_b),
            *(m.FadeOut(item) for item in (*legend_a, *legend_b)),
            m.FadeIn(formula),
            m.FadeIn(result),
            m.FadeIn(keep),
            run_time=1.2,
        )
        self.wait(1.4)

        stage_three = m.Text(
            "Turn each day into a behavioral fingerprint",
            font_size=22,
            color=INK,
        ).move_to([0, 2.15, 0])
        card_centers = ([-4.45, 0.05, 0], [0, 0.05, 0], [4.45, 0.05, 0])
        card_specs = (
            ("51 features", "24 hourly shares + 27 summaries", TEAL),
            ("PCA · 10 components", "retain at least 95% variance", BLUE),
            ("K-Means · K = 4", "groups with similar daily shape", ORANGE),
        )
        card_backgrounds = []
        card_copy = []
        for center, (heading, detail, accent) in zip(card_centers, card_specs):
            panel = m.Rectangle(
                width=3.7,
                height=1.8,
                color=LINE,
                fill_color=PAPER,
                fill_opacity=1,
                stroke_width=1.5,
            ).move_to(center)
            band = m.Rectangle(
                width=3.7,
                height=0.08,
                color=accent,
                fill_color=accent,
                fill_opacity=1,
                stroke_width=0,
            ).move_to([center[0], center[1] + 0.86, 0])
            heading_text = m.Text(heading, font_size=20, color=INK).move_to(
                [center[0], center[1] + 0.2, 0]
            )
            detail_text = m.Text(detail, font_size=14, color=MUTED).move_to(
                [center[0], center[1] - 0.25, 0]
            )
            card_backgrounds.append(m.VGroup(panel, band))
            card_copy.append(m.VGroup(heading_text, detail_text))

        arrow_a = m.Arrow([-2.45, 0.05, 0], [-2.05, 0.05, 0], buff=0, color=MUTED)
        arrow_b = m.Arrow([2.05, 0.05, 0], [2.45, 0.05, 0], buff=0, color=MUTED)
        selection_note = m.Text(
            "K is selected using cluster quality and restart stability checks.",
            font_size=17,
            color=MUTED,
        ).move_to([0, -1.35, 0])
        source_note = m.Text(
            "Reference run · 200 synthetic consumers · curves are illustrative",
            font_size=14,
            color=MUTED,
        ).to_edge(m.DOWN, buff=0.45)

        self.play(
            m.FadeOut(axes),
            m.FadeOut(low_curve),
            m.FadeOut(high_curve),
            m.FadeOut(formula),
            m.FadeOut(result),
            m.FadeOut(keep),
            m.Transform(stage_one, stage_three),
            *(m.FadeIn(card) for card in card_backgrounds),
            m.Create(arrow_a),
            m.Create(arrow_b),
            m.FadeIn(selection_note),
            m.FadeIn(source_note),
            run_time=1.4,
        )
        self.play(*(m.Write(copy) for copy in card_copy), run_time=0.6)
        self.wait(2.0)
