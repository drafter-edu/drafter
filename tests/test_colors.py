"""Tests for the `Color` data type, the color spellings Drafter accepts,
and the route-parameter conversions a `ColorPicker` relies on."""

import sys
from dataclasses import dataclass
from unittest.mock import MagicMock

import pytest

# drafter.bridge requires a browser 'js' module; stub it for unit tests.
if not hasattr(sys.modules.get("js"), "document"):
    sys.modules["js"] = MagicMock()

from drafter import Color, Span
from drafter.bridge.snapshot import (
    deserialize_state_snapshot,
    serialize_state_snapshot,
)
from drafter.data.colors import CSS_COLOR_NAMES, to_color
from drafter.data.converter import ConversionContext
from drafter.data.errors import StudentFacingError
from drafter.payloads.renderer import render
from drafter.router.parameters.conversion import CONVERTER_REGISTRY

ORANGE = Color(255, 136, 0)


def convert(value, expected_type):
    """Convert a submitted form value the way a route parameter would be."""
    return CONVERTER_REGISTRY.convert(
        ConversionContext(
            param_name="paint", expected_type=expected_type, raw_value=value
        )
    )


class TestColor:
    def test_alpha_defaults_to_solid(self):
        assert ORANGE.alpha == 255

    def test_equal_when_all_amounts_match(self):
        assert Color(255, 0, 0) == Color.from_name("red")
        assert Color(255, 0, 0) != Color(255, 0, 0, 128)

    def test_hex_code_omits_alpha_for_a_solid_color(self):
        assert ORANGE.to_hex() == "#ff8800"
        assert str(ORANGE) == "#ff8800"

    def test_hex_code_includes_alpha_when_not_solid(self):
        assert Color(255, 136, 0, 128).to_hex() == "#ff880080"

    def test_hex_code_alpha_can_be_forced_either_way(self):
        assert ORANGE.to_hex(alpha=True) == "#ff8800ff"
        assert Color(255, 136, 0, 128).to_hex(alpha=False) == "#ff8800"

    def test_list_follows_the_same_alpha_rule(self):
        assert ORANGE.to_list() == [255, 136, 0]
        assert Color(255, 136, 0, 128).to_list() == [255, 136, 0, 128]
        assert ORANGE.to_list(alpha=True) == [255, 136, 0, 255]

    def test_whole_number_floats_are_accepted(self):
        assert Color(255.0, 136.0, 0.0) == ORANGE
        assert isinstance(Color(255.0, 0, 0).red, int)

    @pytest.mark.parametrize(
        "amounts, phrase",
        [
            ((256, 0, 0), "red must be from 0 to 255"),
            ((0, -1, 0), "green must be from 0 to 255"),
            ((0, 0, 0, 300), "alpha must be from 0 to 255"),
            ((0.5, 0, 0), "red must be a whole number"),
            (("255", 0, 0), "red must be a whole number"),
            ((True, 0, 0), "red must be a whole number"),
        ],
    )
    def test_amounts_outside_the_scale_explain_themselves(self, amounts, phrase):
        with pytest.raises(StudentFacingError) as raised:
            Color(*amounts)

        assert phrase in str(raised.value)
        assert raised.value.friendly_steps

    def test_used_as_a_style_it_becomes_its_hex_code(self):
        html = render(Span("Hi", style_color=Color(255, 136, 0, 128))).flatten()

        assert "color: #ff880080" in html


class TestFromHex:
    @pytest.mark.parametrize(
        "code, expected",
        [
            ("#ff8800", Color(255, 136, 0)),
            ("#FF8800", Color(255, 136, 0)),
            ("#f80", Color(255, 136, 0)),
            ("#f808", Color(255, 136, 0, 136)),
            ("#ff880080", Color(255, 136, 0, 128)),
            ("  #f80  ", Color(255, 136, 0)),
        ],
    )
    def test_reads_every_hex_form(self, code, expected):
        assert Color.from_hex(code) == expected

    @pytest.mark.parametrize(
        "code", ["ff8800", "#ff880", "#ff88000", "#gg8800", "#", "", None]
    )
    def test_rejects_anything_else(self, code):
        with pytest.raises(StudentFacingError, match="Could not read"):
            Color.from_hex(code)


class TestFromName:
    def test_knows_all_148_browser_color_names(self):
        assert len(CSS_COLOR_NAMES) == 148
        for name, code in CSS_COLOR_NAMES.items():
            assert Color.from_name(name).to_hex() == code

    def test_both_spellings_of_gray(self):
        assert Color.from_name("gray") == Color.from_name("grey")
        assert Color.from_name("darkslategray") == Color.from_name("darkslategrey")

    @pytest.mark.parametrize("name", ["Tomato", "TOMATO", " tomato "])
    def test_capitals_and_outer_spaces_do_not_matter(self, name):
        assert Color.from_name(name) == Color(255, 99, 71)

    @pytest.mark.parametrize("name", ["Steel Blue", "steel-blue", "steel_blue"])
    def test_separators_inside_a_name_do_not_matter(self, name):
        assert Color.from_name(name) == Color(70, 130, 180)

    def test_transparent_is_invisible_black(self):
        assert Color.from_name("transparent") == Color(0, 0, 0, 0)

    def test_misspelled_name_suggests_the_closest_ones(self):
        with pytest.raises(StudentFacingError) as raised:
            Color.from_name("tomatoe")

        assert "Did you mean 'tomato'?" in raised.value.friendly_steps[0]

    def test_unknown_name_without_a_near_match_lists_the_options(self):
        with pytest.raises(StudentFacingError) as raised:
            Color.from_name("xyzzy")

        assert "hex code" in raised.value.friendly_steps[0]


class TestToColor:
    @pytest.mark.parametrize(
        "value, expected",
        [
            (ORANGE, ORANGE),
            ("#f80", ORANGE),
            ("darkorange", Color(255, 140, 0)),
            ([255, 136, 0], ORANGE),
            ((255, 136, 0), ORANGE),
            ([255, 136, 0, 64], Color(255, 136, 0, 64)),
            ({"red": 255, "green": 136, "blue": 0}, ORANGE),
            ({"red": 1, "green": 2, "blue": 3, "alpha": 4}, Color(1, 2, 3, 4)),
        ],
    )
    def test_accepts_every_spelling(self, value, expected):
        assert to_color(value) == expected

    def test_a_color_is_returned_unchanged(self):
        assert to_color(ORANGE) is ORANGE

    @pytest.mark.parametrize("value", [[255, 136], [1, 2, 3, 4, 5], []])
    def test_list_of_the_wrong_length(self, value):
        with pytest.raises(StudentFacingError, match="needs 3 or 4 numbers"):
            to_color(value)

    @pytest.mark.parametrize("value", [None, 255, 1.5, {"red": 1}])
    def test_other_values_are_rejected(self, value):
        with pytest.raises(StudentFacingError, match="Could not read"):
            to_color(value)


class TestRouteParameterConversion:
    """What a route receives for the hex code a ColorPicker submits."""

    def test_str_keeps_the_hex_code(self):
        result = convert("#ff8800", str)

        assert result.ok and result.value == "#ff8800"

    def test_color_annotation(self):
        result = convert("#ff8800", Color)

        assert result.ok and result.value == ORANGE

    def test_color_annotation_with_alpha(self):
        result = convert("#ff880080", Color)

        assert result.ok and result.value == Color(255, 136, 0, 128)

    def test_list_of_ints(self):
        result = convert("#ff8800", list[int])

        assert result.ok and result.value == [255, 136, 0]

    def test_list_of_ints_with_alpha(self):
        result = convert("#ff880080", list[int])

        assert result.ok and result.value == [255, 136, 0, 128]

    def test_tuple_annotations(self):
        assert convert("#ff8800", tuple[int, int, int]).value == (255, 136, 0)
        assert convert("#ff8800", tuple[int, ...]).value == (255, 136, 0)
        assert convert("#ff880080", tuple[int, int, int, int]).value == (
            255,
            136,
            0,
            128,
        )

    def test_tuple_of_the_wrong_length_says_how_many_amounts_arrived(self):
        result = convert("#ff880080", tuple[int, int, int])

        assert not result.ok
        assert "4 amounts" in result.hint

    def test_color_accepts_a_name_or_list_from_a_button_argument(self):
        assert convert("tomato", Color).value == Color(255, 99, 71)
        assert convert([255, 136, 0], Color).value == ORANGE

    def test_unreadable_color_is_a_conversion_error_with_advice(self):
        result = convert("tomatoe", Color)

        assert not result.ok
        assert "Did you mean 'tomato'?" in result.hint

    def test_ordinary_lists_are_untouched(self):
        assert convert("5", list[int]).value == [5]
        assert convert(["1", "2"], list[int]).value == [1, 2]
        assert convert("#ff8800", list[str]).value == ["#ff8800"]
        assert convert("#ff8800", list).value == ["#ff8800"]


class TestColorInState:
    def test_survives_a_save_and_load(self):
        @dataclass
        class Paint:
            wall: Color
            trim: Color

        state = Paint(ORANGE, Color(0, 0, 0, 128))
        saved = serialize_state_snapshot(state, "index", {}, "save", "quick")

        restored = deserialize_state_snapshot(saved.state_json, state)

        assert restored == state
        assert isinstance(restored.wall, Color)
