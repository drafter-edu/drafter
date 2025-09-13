"""
Tests for duplicate form field name detection
"""
import warnings
from drafter.components import *
from drafter.page import Page
from drafter.configuration import ServerConfiguration


def test_duplicate_textbox_names():
    """Test that duplicate TextBox names trigger a warning"""
    config = ServerConfiguration()
    
    with warnings.catch_warnings(record=True) as w:
        warnings.simplefilter("always")
        page = Page(None, [
            TextBox("email", "user1@example.com"),
            TextBox("email", "user2@example.com")  # Duplicate name
        ])
        page.render_content('{}', config)
        
        assert len(w) == 1
        assert "Multiple form components use the same name 'email'" in str(w[0].message)
        assert "unpredictable behavior" in str(w[0].message)


def test_duplicate_mixed_component_names():
    """Test that different component types with same name trigger a warning"""
    config = ServerConfiguration()
    
    with warnings.catch_warnings(record=True) as w:
        warnings.simplefilter("always")
        page = Page(None, [
            SelectBox("preference", ["A", "B", "C"]),
            TextBox("preference", "default")  # Same name as SelectBox
        ])
        page.render_content('{}', config)
        
        assert len(w) == 1
        assert "Multiple form components use the same name 'preference'" in str(w[0].message)


def test_multiple_duplicate_names():
    """Test that multiple duplicate names are all listed in the warning"""
    config = ServerConfiguration()
    
    with warnings.catch_warnings(record=True) as w:
        warnings.simplefilter("always")
        page = Page(None, [
            TextBox("name1", "a"),
            TextBox("name1", "b"),  # Duplicate name1
            SelectBox("name2", ["X", "Y"]),
            CheckBox("name2", True),  # Duplicate name2
        ])
        page.render_content('{}', config)
        
        assert len(w) == 1
        assert "'name1'" in str(w[0].message)
        assert "'name2'" in str(w[0].message)
        assert "Multiple form components use the same names" in str(w[0].message)


def test_no_warning_for_unique_names():
    """Test that unique names don't trigger warnings"""
    config = ServerConfiguration()
    
    with warnings.catch_warnings(record=True) as w:
        warnings.simplefilter("always")
        page = Page(None, [
            TextBox("name1", "a"),
            SelectBox("name2", ["X", "Y"]),
            CheckBox("name3", True),
            TextArea("name4", "d")
        ])
        page.render_content('{}', config)
        
        assert len(w) == 0


def test_button_names_dont_conflict():
    """Test that Button names don't conflict with form field names"""
    config = ServerConfiguration()
    
    # This reproduces the original issue scenario
    with warnings.catch_warnings(record=True) as w:
        warnings.simplefilter("always")
        page = Page(None, [
            SelectBox('choice', ['Encode', 'Decode', 'Gallery']),
            Button("choice", "choice_changer")  # Same text but Button uses --submit-button
        ])
        page.render_content('{}', config)
        
        assert len(w) == 0  # Should not warn because Button doesn't use 'choice' as form name


def test_mixed_content_with_duplicates():
    """Test that duplicate detection works with mixed string/component content"""
    config = ServerConfiguration()
    
    with warnings.catch_warnings(record=True) as w:
        warnings.simplefilter("always")
        page = Page(None, [
            "Enter your information:",
            TextBox("info", "default1"),
            "Select an option:",
            SelectBox("info", ["A", "B"]),  # Duplicate name
            Button("Submit", "handler")
        ])
        page.render_content('{}', config)
        
        assert len(w) == 1
        assert "Multiple form components use the same name 'info'" in str(w[0].message)


def test_all_form_component_types():
    """Test that all form component types are checked for duplicates"""
    config = ServerConfiguration()
    
    with warnings.catch_warnings(record=True) as w:
        warnings.simplefilter("always")
        page = Page(None, [
            TextBox("test", "value1"),
            SelectBox("test", ["A", "B"]),
            CheckBox("test", True),
            TextArea("test", "value2"),
            FileUpload("test")  # Include FileUpload in the test
        ])
        page.render_content('{}', config)
        
        assert len(w) == 1
        assert "Multiple form components use the same name 'test'" in str(w[0].message)


def test_file_upload_duplicates():
    """Test that FileUpload components are included in duplicate detection"""
    config = ServerConfiguration()
    
    with warnings.catch_warnings(record=True) as w:
        warnings.simplefilter("always")
        page = Page(None, [
            TextBox("document", "default"),
            FileUpload("document")  # Same name as TextBox
        ])
        page.render_content('{}', config)
        
        assert len(w) == 1
        assert "Multiple form components use the same name 'document'" in str(w[0].message)