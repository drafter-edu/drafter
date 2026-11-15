"""Tests for form components: focused SelectBox behavior checks, and the
Slider and ColorPicker inputs (drafter-edu/drafter#28)."""

import pytest

from drafter import (
    CheckBox,
    Color,
    ColorPicker,
    DateInput,
    DateTimeInput,
    FileUpload,
    RadioButtonGroup,
    RelatedCheckBox,
    SelectBox,
    Slider,
    TextArea,
    TextBox,
    TimeInput,
)
from drafter.data.converter import ConversionContext
from drafter.data.errors import StudentFacingError
from drafter.payloads.renderer import render
from drafter.router.parameters.conversion import CONVERTER_REGISTRY


class TestSelectBoxAllowMissing:
    def test_missing_default_raises_when_allow_missing_false(self):
        with pytest.raises(
            ValueError, match="default_value 'purple' is not in options"
        ) as raised:
            SelectBox("color", ["red", "green", "blue"], "purple")

        # Its own title, not the shared "Unusable Value" of a ValueError.
        assert raised.value.friendly_title == "SelectBox Default Is Not an Option"

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
        assert picker.alpha is False
        assert "value=" not in render(picker).flatten()

    @pytest.mark.parametrize(
        "written",
        [
            "#FF8800",
            "#f80",
            "#ff8800",
            [255, 136, 0],
            (255, 136, 0),
            Color(255, 136, 0),
        ],
    )
    def test_every_spelling_becomes_the_same_hex_code(self, written):
        assert ColorPicker("ink", written).default_value == "#ff8800"

    def test_color_names_are_accepted(self):
        assert ColorPicker("ink", "tomato").default_value == "#ff6347"
        assert ColorPicker("ink", "Steel Blue").default_value == "#4682b4"

    def test_pickers_with_the_same_color_are_equal(self):
        assert ColorPicker("ink", "red") == ColorPicker("ink", "#ff0000")
        assert ColorPicker("ink", "red") != ColorPicker("ink", "blue")

    def test_alpha_in_the_starting_color_is_dropped_without_alpha(self):
        assert ColorPicker("ink", "#ff880080").default_value == "#ff8800"
        assert ColorPicker("ink", [255, 136, 0, 128]).default_value == "#ff8800"
        assert ColorPicker("ink", Color(255, 136, 0, 128)).default_value == "#ff8800"

    def test_submitted_color_arrives_as_text(self):
        result = convert("#ff8800", str)

        assert result.ok and result.value == "#ff8800"

    @pytest.mark.parametrize(
        "bad_color", ["tomatoe", "ff8800", "#ff88000", "#gg8800", "", None, 255, [1, 2]]
    )
    def test_unreadable_colors_are_rejected(self, bad_color):
        with pytest.raises(StudentFacingError) as raised:
            ColorPicker("ink", bad_color)

        assert raised.value.friendly_message
        assert raised.value.friendly_steps

    def test_name_must_be_a_valid_parameter_name(self):
        with pytest.raises(ValueError, match="2nd"):
            ColorPicker("2nd")


class TestColorPickerAlpha:
    def render(self, *args, **kwargs) -> str:
        return render(ColorPicker(*args, alpha=True, **kwargs)).flatten()

    def test_default_is_solid_black_with_alpha_digits(self):
        assert ColorPicker("ink", alpha=True).default_value == "#000000ff"

    def test_starting_color_keeps_its_alpha(self):
        assert ColorPicker("ink", "#ff880080", alpha=True).default_value == (
            "#ff880080"
        )
        assert ColorPicker("ink", [255, 136, 0, 64], alpha=True).default_value == (
            "#ff880040"
        )
        assert ColorPicker("ink", Color(255, 136, 0, 0), alpha=True).default_value == (
            "#ff880000"
        )

    def test_solid_starting_color_gets_full_alpha(self):
        assert ColorPicker("ink", "tomato", alpha=True).default_value == "#ff6347ff"

    def test_only_the_hidden_field_is_submitted(self):
        html = self.render("ink", "#ff880080")

        assert html.count('name="ink"') == 1
        assert '<input name="ink" type="hidden" value="#ff880080"/>' in html

    def test_swatch_shows_the_solid_part_and_slider_the_alpha(self):
        html = self.render("ink", "#ff880080")

        assert 'type="color" value="#ff8800"' in html
        assert 'type="range" value="128"' in html
        assert 'max="255" min="0"' in html

    def test_both_controls_are_labelled_and_the_swatch_owns_the_id(self):
        html = self.render("ink")

        assert 'aria-label="ink" id="ink"' in html
        assert 'aria-label="ink opacity"' in html
        assert html.count('id="ink"') == 1

    def test_styles_and_handlers_go_on_the_wrapper(self):
        html = self.render("ink", on_change="recolor", style_margin="4px")

        wrapper = html.split(">", 1)[0]
        assert wrapper.startswith("<span")
        assert "margin: 4px" in wrapper
        assert "recolor" in wrapper

    def test_repr_round_trips(self):
        picker = ColorPicker("ink", "#ff880080", alpha=True)

        assert repr(picker) == "ColorPicker('ink', '#ff880080', True)"
        assert eval(repr(picker)) == picker
        assert picker != ColorPicker("ink", "#ff8800")

    def test_disabled_goes_on_every_input_and_not_the_wrapper(self):
        html = self.render("ink", disabled=True)

        wrapper = html.split(">", 1)[0]
        assert "disabled" not in wrapper
        assert 'disabled id="ink"' in html
        # The swatch, the opacity slider, and the hidden input that is
        # submitted: a disabled field must not send its value.
        assert html.count(" disabled ") == 3
        assert '<input disabled name="ink" type="hidden"' in html

    def test_not_disabled_by_default(self):
        assert "disabled" not in self.render("ink")


def render_tag(component) -> str:
    """The opening tag of a rendered component."""
    return render(component).flatten().split(">", 1)[0]


class TestFieldKeywordsBecomeAttributes:
    """A keyword missing from KNOWN_ATTRS is rendered as a CSS style, which
    silently drops it: `min=0` became `style="min: 0"`."""

    @pytest.mark.parametrize(
        "component, expected",
        [
            (
                TextBox("age", kind="number", min=0, max=10, step=2, required=True),
                ['min="0"', 'max="10"', 'step="2"', " required"],
            ),
            (
                TextBox("age", disabled=True, readonly=True, list="ages"),
                [" disabled", " readonly", 'list="ages"'],
            ),
            (TextArea("essay", maxlength=10, minlength=2), ['maxlength="10"']),
            (TextArea("essay", maxlength=10, minlength=2), ['minlength="2"']),
            (SelectBox("size", ["S", "M"], disabled=True), [" disabled"]),
            (ColorPicker("ink", disabled=True), [" disabled"]),
            (FileUpload("photo", disabled=True), [" disabled"]),
            (
                DateInput("day", min="2026-01-01", max="2026-12-31", required=True),
                ['min="2026-01-01"', 'max="2026-12-31"', " required"],
            ),
            (
                DateTimeInput("moment", step=60, disabled=True, readonly=True),
                ['step="60"', " disabled", " readonly"],
            ),
            (TimeInput("alarm", min="08:00", max="17:00"), ['min="08:00"']),
            (Slider("volume", 0, 10, disabled=True, list="ticks"), [" disabled"]),
            (Slider("volume", 0, 10, disabled=True, list="ticks"), ['list="ticks"']),
        ],
    )
    def test_keyword_renders_as_an_attribute(self, component, expected):
        tag = render_tag(component)

        assert "style=" not in tag
        for attribute in expected:
            assert attribute in tag

    @pytest.mark.parametrize(
        "component", [CheckBox("agree", required=True, disabled=True)]
    )
    def test_checkbox_keywords_go_on_the_checkbox(self, component):
        html = render(component).flatten()
        hidden, checkbox = html.split("/>", 1)

        assert "required" not in hidden and "disabled" not in hidden
        assert " disabled" in checkbox and " required" in checkbox
        assert "style=" not in html

    def test_related_checkbox_keywords(self):
        tag = render_tag(RelatedCheckBox("toppings", "olives", disabled=True))

        assert " disabled" in tag
        assert "style=" not in tag

    def test_false_leaves_the_attribute_off(self):
        tag = render_tag(TextBox("age", required=False, disabled=False))

        assert "required" not in tag and "disabled" not in tag

    def test_real_styles_are_still_styles(self):
        tag = render_tag(TextBox("age", style_color="red", required=True))

        assert 'style="color: red"' in tag
        assert " required" in tag


class TestAutocomplete:
    """`autocomplete` takes a word, so it must not render as a bare flag."""

    def test_text_value_is_kept(self):
        assert 'autocomplete="off"' in render_tag(TextArea("essay", autocomplete="off"))
        assert 'autocomplete="email"' in render_tag(
            TextBox("email", autocomplete="email")
        )

    def test_booleans_become_on_and_off(self):
        assert 'autocomplete="on"' in render_tag(TextBox("name", autocomplete=True))
        assert 'autocomplete="off"' in render_tag(TextBox("name", autocomplete=False))


class TestRadioButtonGroup:
    def render(self, **kwargs) -> str:
        group = RadioButtonGroup(
            "size", ["small", "medium"], default_value="medium", **kwargs
        )
        return render(group).flatten()

    def test_id_is_the_field_name_not_the_default_value(self):
        assert RadioButtonGroup("size", ["small"], default_value="small").get_id() == (
            "size"
        )
        assert RadioButtonGroup("size", ["small"]).get_id() == "size"
        assert RadioButtonGroup("size", ["small"], id="sizes").get_id() == "sizes"

    def test_wrapper_renders_the_field_name_as_its_id(self):
        assert self.render().startswith('<div aria-label="size" id="size">')

    def test_required_and_disabled_go_on_every_radio_button(self):
        html = self.render(required=True, disabled=True)
        wrapper, radios = html.split(">", 1)

        assert "required" not in wrapper and "disabled" not in wrapper
        assert "style=" not in wrapper
        assert radios.count(" disabled ") == 2
        assert radios.count(" required ") == 2

    def test_styles_stay_on_the_wrapper(self):
        html = self.render(style_margin="4px")
        wrapper, radios = html.split(">", 1)

        assert "margin: 4px" in wrapper
        assert "margin" not in radios
