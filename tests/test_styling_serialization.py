"""
Tests for styling function serialization to ensure they use underscores in style names
for proper test generation.
"""

import pytest
from drafter.components import Text
from drafter.styling import (
    bold, italic, underline, strikethrough, monospace, small_font, large_font,
    change_color, change_background_color, change_text_size, change_text_font,
    change_text_align, change_text_decoration, change_text_transform,
    change_height, change_width, change_border, change_margin, change_padding,
    float_left, float_right
)


def test_styling_functions_use_underscores_in_extra_settings():
    """Test that styling functions store style keys with underscores, not dashes."""
    text = Text("Test")
    
    # Test styling functions that should convert dashes to underscores
    test_cases = [
        (bold, [], "style_font_weight"),
        (italic, [], "style_font_style"),
        (underline, [], "style_text_decoration"),
        (strikethrough, [], "style_text_decoration"),
        (monospace, [], "style_font_family"),
        (small_font, [], "style_font_size"),
        (large_font, [], "style_font_size"),
        (change_color, ["red"], "style_color"),
        (change_background_color, ["blue"], "style_background_color"),
        (change_text_size, ["16px"], "style_font_size"),
        (change_text_font, ["Arial"], "style_font_family"),
        (change_text_align, ["center"], "style_text_align"),
        (change_text_decoration, ["none"], "style_text_decoration"),
        (change_text_transform, ["uppercase"], "style_text_transform"),
        (change_height, ["100px"], "style_height"),
        (change_width, ["200px"], "style_width"),
        (change_border, ["1px solid black"], "style_border"),
        (change_margin, ["10px"], "style_margin"),
        (change_padding, ["5px"], "style_padding"),
        (float_left, [], "style_float"),
        (float_right, [], "style_float"),
    ]
    
    for func, args, expected_key in test_cases:
        # Apply styling function
        styled_text = func(Text("Test"), *args)
        
        # Verify the expected key exists
        assert expected_key in styled_text.extra_settings, f"{func.__name__} should create {expected_key}"
        
        # Verify no style keys contain dashes
        for key in styled_text.extra_settings.keys():
            if key.startswith("style_"):
                assert "-" not in key, f"Style key {key} from {func.__name__} contains dash instead of underscore"


def test_styling_functions_generate_correct_html():
    """Test that styling functions still generate correct HTML with CSS dashes."""
    text = Text("Test")
    
    # Test a few key styling functions to ensure HTML output is correct
    bold_text = bold(text)
    assert "font-weight: bold" in str(bold_text)
    
    bg_colored_text = change_background_color(Text("Test"), "red")
    assert "background-color: red" in str(bg_colored_text)
    
    styled_text = italic(underline(Text("Test")))
    html = str(styled_text)
    assert "font-style: italic" in html
    assert "text-decoration: underline" in html


def test_chained_styling_functions():
    """Test that chaining multiple styling functions works correctly."""
    text = Text("Test")
    styled_text = change_background_color(bold(italic(text)), "blue")
    
    # Should have all three styles with underscores
    expected_keys = {"style_font_style", "style_font_weight", "style_background_color"}
    actual_keys = set(styled_text.extra_settings.keys())
    
    assert expected_keys.issubset(actual_keys), f"Missing keys: {expected_keys - actual_keys}"
    
    # Verify no dashes in any keys
    for key in styled_text.extra_settings.keys():
        if key.startswith("style_"):
            assert "-" not in key, f"Style key {key} contains dash"
    
    # HTML should still use CSS property names with dashes
    html = str(styled_text)
    assert "font-style: italic" in html
    assert "font-weight: bold" in html
    assert "background-color: blue" in html