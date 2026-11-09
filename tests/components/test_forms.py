"""Tests for form components: focused SelectBox behavior checks, and the
Slider and ColorPicker inputs (drafter-edu/drafter#28)."""

import pytest

from drafter import ColorPicker, SelectBox, Slider
from drafter.data.converter import ConversionContext
from drafter.data.errors import StudentFacingError
from drafter.payloads.renderer import render
from drafter.router.parameters.conversion import CONVERTER_REGISTRY


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


def convert(value, expected_type):
    """Convert a submitted form value the way a route parameter would be."""
    return CONVERTER_REGISTRY.convert(
        ConversionContext(
            param_name="field", expected_type=expected_type, raw_value=value
        )
    )


class TestSlider:
    def test_keeps_its_arguments(self):
        slider = Slider("volume", 0, 100, 25, step=5)

        assert (slider.name, slider.min, slider.max) == ("volume", 0, 100)
        assert (slider.default_value, slider.step) == (25, 5)

    def test_start_defaults_to_the_browsers_choice(self):
        html = render(Slider("volume", 0, 100)).flatten()

        assert "value=" not in html
        assert "step=" not in html

    def test_default_may_sit_on_either_end(self):
        assert Slider("volume", 0, 100, 0).default_value == 0
        assert Slider("volume", 0, 100, 100).default_value == 100

    def test_id_is_the_field_name_so_labels_can_point_at_it(self):
        assert Slider("volume", 0, 100).get_id() == "volume"

    def test_submitted_value_converts_to_an_int_parameter(self):
        result = convert("40", int)

        assert result.ok and result.value == 40

    def test_submitted_fraction_converts_to_a_float_parameter(self):
        result = convert("2.5", float)

        assert result.ok and result.value == 2.5

    @pytest.mark.parametrize(
        "build, phrase",
        [
            (lambda: Slider("v", 10, 0), "min (10) must be less than max (0)"),
            (lambda: Slider("v", 5, 5), "min (5) must be less than max (5)"),
            (lambda: Slider("v", 0, 10, 50), "default_value (50) must be between"),
            (lambda: Slider("v", 0, 10, -1), "default_value (-1) must be between"),
            (lambda: Slider("v", 0, 10, step=0), "step must be greater than zero"),
            (lambda: Slider("v", 0, 10, step=-2), "step must be greater than zero"),
            (lambda: Slider("v", "0", 10), "min must be a number"),
            (lambda: Slider("v", 0, "10"), "max must be a number"),
            (lambda: Slider("v", 0, 10, "5"), "default_value must be a number"),
            (lambda: Slider("v", 0, 10, step="1"), "step must be a number"),
            (lambda: Slider("v", False, True), "min must be a number"),
        ],
    )
    def test_bad_arguments_explain_themselves(self, build, phrase):
        with pytest.raises(StudentFacingError) as raised:
            build()

        assert phrase in str(raised.value)
        assert raised.value.friendly_message
        assert raised.value.friendly_steps

    def test_name_must_be_a_valid_parameter_name(self):
        with pytest.raises(ValueError, match="my volume"):
            Slider("my volume", 0, 100)


class TestColorPicker:
    def test_defaults_to_black_without_writing_a_value(self):
        picker = ColorPicker("ink")

        assert picker.default_value == "#000000"
        assert "value=" not in render(picker).flatten()

    def test_hex_codes_are_normalized_to_lowercase(self):
        assert ColorPicker("ink", "#FF8800").default_value == "#ff8800"

    def test_submitted_color_arrives_as_text(self):
        result = convert("#ff8800", str)

        assert result.ok and result.value == "#ff8800"

    @pytest.mark.parametrize(
        "bad_color", ["red", "ff8800", "#f80", "#ff88000", "#gg8800", "", None, 255]
    )
    def test_anything_but_six_digit_hex_is_rejected(self, bad_color):
        with pytest.raises(StudentFacingError) as raised:
            ColorPicker("ink", bad_color)

        assert "hex color like '#ff8800'" in str(raised.value)
        assert raised.value.friendly_steps

    def test_name_must_be_a_valid_parameter_name(self):
        with pytest.raises(ValueError, match="2nd"):
            ColorPicker("2nd")
