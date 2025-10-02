"""
Unit tests for button namespacing.
Tests that multiple buttons with the same text but different arguments
can be properly distinguished.
"""
import pytest
from drafter import Button, Argument
from drafter.history import extract_button_label, remap_hidden_form_parameters
from drafter.constants import LABEL_SEPARATOR
import json
import re


def test_button_unique_namespacing():
    """Test that buttons with same text get unique namespaces"""
    # Create multiple buttons with the same text
    button1 = Button("Click", "route1", [Argument("x", 0), Argument("y", 0)])
    button2 = Button("Click", "route2", [Argument("x", 1), Argument("y", 1)])
    button3 = Button("Click", "route3", [Argument("x", 2), Argument("y", 2)])
    
    # Convert to HTML
    html1 = str(button1)
    html2 = str(button2)
    html3 = str(button3)
    
    # Extract parameter names from hidden inputs
    id_pattern = r'name=\'([^\']+)\''
    names1 = set(re.findall(id_pattern, html1))
    names2 = set(re.findall(id_pattern, html2))
    names3 = set(re.findall(id_pattern, html3))
    
    # Remove the submit button name (which is the same for all)
    names1 = {n for n in names1 if n != '--submit-button'}
    names2 = {n for n in names2 if n != '--submit-button'}
    names3 = {n for n in names3 if n != '--submit-button'}
    
    # All parameter names should be different (no collisions)
    all_names = names1 | names2 | names3
    assert len(all_names) == 6, f"Expected 6 unique parameter names, got {len(all_names)}"
    
    # Check that parameters don't overlap
    assert len(names1 & names2) == 0, "Button 1 and 2 have overlapping parameter names"
    assert len(names1 & names3) == 0, "Button 1 and 3 have overlapping parameter names"
    assert len(names2 & names3) == 0, "Button 2 and 3 have overlapping parameter names"


def test_button_unique_values():
    """Test that buttons with same text have unique values (including IDs)"""
    button1 = Button("Click", "route1")
    button2 = Button("Click", "route2")
    button3 = Button("Click", "route3")
    
    html1 = str(button1)
    html2 = str(button2)
    html3 = str(button3)
    
    # Extract button values
    value_pattern = r"<button[^>]+value='([^']+)'"
    value1 = re.search(value_pattern, html1).group(1)
    value2 = re.search(value_pattern, html2).group(1)
    value3 = re.search(value_pattern, html3).group(1)
    
    # Values should be unique
    assert value1 != value2, "Button 1 and 2 have the same value"
    assert value1 != value3, "Button 1 and 3 have the same value"
    assert value2 != value3, "Button 2 and 3 have the same value"
    
    # Each value should contain the button text
    assert 'Click' in value1
    assert 'Click' in value2
    assert 'Click' in value3


def test_parameter_extraction_with_multiple_buttons():
    """Test that parameters are correctly extracted when multiple buttons with same text exist"""
    
    # Simulate three buttons all with text "Click" but different IDs
    button_id_1 = 12345
    button_id_2 = 67890
    button_id_3 = 11111
    
    # Simulate form submission where ALL buttons' hidden inputs are present
    form_data = {
        f'"Click#{button_id_1}"{LABEL_SEPARATOR}x': '0',
        f'"Click#{button_id_1}"{LABEL_SEPARATOR}y': '0',
        f'"Click#{button_id_2}"{LABEL_SEPARATOR}x': '1',
        f'"Click#{button_id_2}"{LABEL_SEPARATOR}y': '1',
        f'"Click#{button_id_3}"{LABEL_SEPARATOR}x': '2',
        f'"Click#{button_id_3}"{LABEL_SEPARATOR}y': '2',
    }
    
    # Test clicking button 1
    button_pressed = f"Click#{button_id_1}"
    params = remap_hidden_form_parameters(form_data, button_pressed)
    assert params['x'] == 0
    assert params['y'] == 0
    
    # Test clicking button 2
    button_pressed = f"Click#{button_id_2}"
    params = remap_hidden_form_parameters(form_data, button_pressed)
    assert params['x'] == 1
    assert params['y'] == 1
    
    # Test clicking button 3
    button_pressed = f"Click#{button_id_3}"
    params = remap_hidden_form_parameters(form_data, button_pressed)
    assert params['x'] == 2
    assert params['y'] == 2


def test_backward_compatibility_buttons_without_ids():
    """Test that buttons without IDs (old format) still work"""
    # Simulate old-style button (without ID in namespace)
    form_data = {
        f'"OldButton"{LABEL_SEPARATOR}param': json.dumps('value1'),
    }
    
    button_pressed = "OldButton"
    params = remap_hidden_form_parameters(form_data, button_pressed)
    assert params['param'] == 'value1'


def test_extract_button_label_with_id():
    """Test that extract_button_label correctly handles button IDs"""
    # Old format (backward compatibility - without ID)
    button_namespace, param = extract_button_label(f'"Click"{LABEL_SEPARATOR}x')
    assert button_namespace == "Click"
    assert param == "x"
    
    # New format with ID - returns full namespace
    namespace = "Click#12345"
    full_key = f'"{namespace}"{LABEL_SEPARATOR}x'
    button_namespace, param = extract_button_label(full_key)
    assert button_namespace == "Click#12345"
    assert param == "x"
