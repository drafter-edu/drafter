"""
Test the __repr__ method for Row components to ensure clean code generation.
"""
from drafter.components import Row, Div


def test_row_repr_basic():
    """Test that Row displays cleanly without showing default style settings"""
    r = Row('test', 'content')
    assert repr(r) == "Row('test', 'content')"


def test_row_repr_with_extra_settings():
    """Test that Row displays extra settings when they are added"""
    r = Row('test', 'content', style_color='red')
    assert repr(r) == "Row('test', 'content', {'style_color': 'red'})"


def test_row_repr_with_multiple_extra_settings():
    """Test that Row displays multiple extra settings"""
    r = Row('test', 'content', style_color='red', style_border='1px solid black')
    # Note: dict order is preserved in Python 3.7+
    assert repr(r) == "Row('test', 'content', {'style_color': 'red', 'style_border': '1px solid black'})"


def test_div_with_row_like_settings():
    """Test that Div with Row-like settings still shows all settings"""
    d = Div('test', 'content', style_display='flex', style_flex_direction='row', style_align_items='center')
    assert repr(d) == "Div('test', 'content', {'style_display': 'flex', 'style_flex_direction': 'row', 'style_align_items': 'center'})"


def test_plain_div():
    """Test that plain Div shows no settings"""
    d = Div('test', 'content')
    assert repr(d) == "Div('test', 'content')"


def test_row_with_modified_default_settings():
    """Test that Row displays settings when default values are changed"""
    r = Row('test', 'content')
    r.extra_settings['style_display'] = 'block'
    # This should show the modified setting
    assert repr(r) == "Row('test', 'content', {'style_display': 'block'})"
