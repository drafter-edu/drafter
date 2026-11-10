"""Tests for `MatPlotLibPlot` figure capture and cleanup.

Regression coverage for drafter-edu/drafter#149: a chart built by a unit
test (which calls the route but never renders the page) used to stay in
pyplot's current figure and show up in the first page that did render.
"""

import re

import pytest

matplotlib = pytest.importorskip("matplotlib")
matplotlib.use("Agg")

import matplotlib.pyplot as plt  # noqa: E402  (must follow the backend choice)

from drafter import MatPlotLibPlot  # noqa: E402
from drafter.components import plotting  # noqa: E402
from drafter.payloads.renderer import render  # noqa: E402


@pytest.fixture(autouse=True)
def clean_pyplot():
    """Start and end every test with no open figures."""
    plt.close("all")
    yield
    plt.close("all")


def line_chart(**settings) -> MatPlotLibPlot:
    """Plot one line the way a route would, then build the component."""
    plt.plot([1, 2, 3])
    return MatPlotLibPlot(**settings)


def html_of(component: MatPlotLibPlot) -> str:
    """The chart's image data, without the per-component id attribute."""
    rendered = render(component).flatten()
    if "<svg" in rendered:
        return rendered
    match = re.search(r'src="([^"]+)"', rendered)
    assert match, rendered
    return match.group(1)


def test_unrendered_charts_do_not_leak_into_the_next_chart():
    baseline = html_of(line_chart())

    # Unit tests call the route and compare the page without rendering it.
    line_chart()
    line_chart()

    assert html_of(line_chart()) == baseline


def test_creating_the_component_starts_the_next_chart_fresh():
    line_chart()

    assert plt.get_fignums() == []


def test_browser_rendering_does_not_accumulate(monkeypatch):
    monkeypatch.setattr(plotting, "is_pyodide", lambda: True)

    first = html_of(line_chart())
    second = html_of(line_chart())

    assert first == second
    assert plt.get_fignums() == []


def test_rendering_twice_gives_the_same_chart():
    chart = line_chart()

    assert html_of(chart) == html_of(chart)


def test_close_automatically_false_lets_two_components_share_a_figure():
    empty = html_of(MatPlotLibPlot())

    plt.plot([1, 2, 3])
    first = MatPlotLibPlot(close_automatically=False)
    second = MatPlotLibPlot()

    assert html_of(first) == html_of(second)
    assert html_of(first) != empty


def test_close_automatically_false_keeps_the_figure_open():
    line_chart(close_automatically=False)

    assert len(plt.get_fignums()) == 1


def test_to_picture_uses_the_figure_the_component_captured():
    chart = line_chart()
    before = chart.to_picture().to_bytes()

    # Later plotting belongs to a different chart.
    plt.plot([3, 2, 1])
    plt.plot([5, 5, 5])

    assert chart.to_picture().to_bytes() == before


def test_svg_format_renders_inline_svg():
    chart = line_chart(extra_matplotlib_settings={"format": "svg"})

    assert "<svg" in html_of(chart)


def test_png_chart_is_an_image_source_not_a_style():
    rendered = render(line_chart()).flatten()

    assert ' src="data:image/png;base64,' in rendered
    assert "src:" not in rendered
