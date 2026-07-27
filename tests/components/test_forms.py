"""Tests for form components with focused SelectBox behavior checks."""

import pytest

from drafter import SelectBox
from drafter.payloads.renderer import render


class TestSelectBoxAllowMissing:
    def test_missing_default_raises_when_allow_missing_false(self):
        with pytest.raises(
            ValueError, match="default_value 'purple' is not in options"
        ):
            SelectBox("color", ["red", "green", "blue"], "purple")

    def test_missing_default_allowed_when_flag_true(self):
        component = SelectBox(
            "color", ["red", "green", "blue"], "purple", allow_missing=True
        )
        assert component.default_value == "purple"

    def test_missing_default_allowed_renders_without_selected_option(self):
        component = SelectBox(
            "color", ["red", "green", "blue"], "purple", allow_missing=True
        )
        html = render(component).flatten()
        assert "selected" not in html

    def test_present_default_still_selected_when_allow_missing_true(self):
        component = SelectBox(
            "color", ["red", "green", "blue"], "green", allow_missing=True
        )
        html = render(component).flatten()
        assert 'selected value="green"' in html
