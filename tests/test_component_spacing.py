"""
Test cases for component HTML spacing issues.

Tests to verify that components produce HTML without extra spaces
that could cause string comparison issues in unit tests.
"""

import pytest
from drafter import Row, Div, Span, Text


def test_row_component_no_double_spaces():
    """Test that Row component doesn't produce double spaces in HTML output."""
    row = Row("Task:", "test task")
    result = str(row)
    
    # Should not have double spaces
    assert "  " not in result, f"Found double space in: {result!r}"
    
    # Should have proper format with style attribute
    assert result.startswith("<div style="), f"Unexpected format: {result!r}"


def test_div_component_no_trailing_space():
    """Test that Div component without settings has no trailing space."""
    div = Div("content")
    result = str(div)
    
    # Should be clean without trailing space
    assert result == "<div>content</div>", f"Expected '<div>content</div>', got {result!r}"


def test_row_comparison_consistency():
    """Test that two identical Row components produce identical strings."""
    row1 = Row("Task:", "test")
    row2 = Row("Task:", "test")
    
    str1 = str(row1)
    str2 = str(row2)
    
    # Should be identical for comparison in unit tests
    assert str1 == str2, f"Row strings differ:\n  {str1!r}\n  {str2!r}"


def test_div_with_attributes_no_double_spaces():
    """Test that Div with attributes has proper spacing (no double spaces)."""
    div = Div("content", id="test", style_color="red")
    result = str(div)
    
    # Should not have double spaces
    assert "  " not in result, f"Found double space in: {result!r}"
    
    # Should have single space between attributes
    assert "<div " in result, "Should start with '<div '"


def test_span_component_spacing():
    """Test that Span component has proper spacing."""
    span1 = Span("text")
    span2 = Span("text", id="myspan")
    
    result1 = str(span1)
    result2 = str(span2)
    
    # Neither should have double spaces
    assert "  " not in result1, f"Found double space in: {result1!r}"
    assert "  " not in result2, f"Found double space in: {result2!r}"
    
    # Span without attributes should have no space before closing >
    assert result1 == "<span>text</span>", f"Unexpected format: {result1!r}"


def test_nested_row_components():
    """Test nested Row components in a realistic scenario like a task list."""
    task_entry = Div(
        Row("Task:", "Clean room"),
        Row("Date:", "12/25/2024"),
        Row("Description:", Text("A simple task")),
        Row("Tag:", "home")
    )
    
    result = str(task_entry)
    
    # Should not have double spaces anywhere in the output
    assert "  " not in result, f"Found double space in task entry"
    
    # Each Row should be properly formatted with style attribute
    assert result.count("style='display: flex") == 4, "Should have 4 Row components with styles"
