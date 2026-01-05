"""
Eventually, we should switch to a more robust way of comparing the
two HTML snippets rather than string comparison.
"""

import pytest
import os
import pathlib
from lxml import html as lxml_html
from drafter import *
from drafter.payloads.renderer import render
from tests.components.snippets.simple import tests as simple_tests


SNIPPETS = {}
SNIPPETS["simple"] = simple_tests.get_tests()


def normalize_html(html: str):
    """Normalize HTML string for comparison."""

    parsed = lxml_html.fromstring(html)
    return lxml_html.tostring(parsed, pretty_print=True, encoding="unicode").strip()


def idfn(val):
    if isinstance(val, tuple):
        return f"{val[0]}/{val[1]}"
    return None


@pytest.mark.parametrize(
    "category, name, content, expected",
    [
        (cat, name, *data)
        for cat, items in SNIPPETS.items()
        for name, data in items.items()
    ],
    ids=idfn,
)
def test_rendering(category, name, content, expected):
    rendered = render(content).flatten()
    assert normalize_html(rendered) == normalize_html(expected)
