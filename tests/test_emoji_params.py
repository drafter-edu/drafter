"""Unit tests for emoji support in form parameters."""
from bottle import FormsDict
from drafter.history import get_params
from unittest.mock import Mock
import pytest

def test_get_params_with_emoji():
    """Test that get_params correctly handles emoji characters."""
    # Create a mock request with FormsDict containing emojis
    mock_request = Mock()
    
    # Create a FormsDict with emoji content
    params = FormsDict()
    params['star_rating'] = '⭐'
    params['message'] = '🎉 Hello World! 🌍'
    params['name'] = 'test'
    
    mock_request.params = params
    mock_request.files = {}
    
    # Replace the global request object temporarily
    import drafter.history
    original_request = drafter.history.request
    drafter.history.request = mock_request
    
    try:
        # Call get_params and verify it handles emojis correctly
        result = get_params()
        
        # Verify the results contain the emojis
        assert result['star_rating'] == '⭐', f"Expected '⭐', got {result['star_rating']!r}"
        assert result['message'] == '🎉 Hello World! 🌍', f"Expected '🎉 Hello World! 🌍', got {result['message']!r}"
        assert result['name'] == 'test', f"Expected 'test', got {result['name']!r}"
    finally:
        # Restore the original request
        drafter.history.request = original_request

def test_get_params_with_ascii():
    """Test that get_params still works with ASCII characters."""
    mock_request = Mock()
    
    # Create a FormsDict with ASCII content
    params = FormsDict()
    params['name'] = 'John Doe'
    params['age'] = '25'
    
    mock_request.params = params
    mock_request.files = {}
    
    # Replace the global request object temporarily
    import drafter.history
    original_request = drafter.history.request
    drafter.history.request = mock_request
    
    try:
        # Call get_params
        result = get_params()
        
        # Verify the results
        assert result['name'] == 'John Doe'
        assert result['age'] == '25'
    finally:
        # Restore the original request
        drafter.history.request = original_request

def test_get_params_with_mixed_unicode():
    """Test that get_params works with various Unicode characters."""
    mock_request = Mock()
    
    # Create a FormsDict with various Unicode content
    params = FormsDict()
    params['chinese'] = '你好'
    params['arabic'] = 'مرحبا'
    params['emoji'] = '😀🎉🚀'
    params['ascii'] = 'hello'
    
    mock_request.params = params
    mock_request.files = {}
    
    # Replace the global request object temporarily
    import drafter.history
    original_request = drafter.history.request
    drafter.history.request = mock_request
    
    try:
        # Call get_params
        result = get_params()
        
        # Verify all Unicode is preserved
        assert result['chinese'] == '你好'
        assert result['arabic'] == 'مرحبا'
        assert result['emoji'] == '😀🎉🚀'
        assert result['ascii'] == 'hello'
    finally:
        # Restore the original request
        drafter.history.request = original_request
