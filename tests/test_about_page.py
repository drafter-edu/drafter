"""
Tests for the about page functionality
"""
from drafter import Server, Page, Header, BulletedList
from drafter.deploy import set_site_information
from drafter.server import SiteInformation


def test_about_page_no_information():
    """Test that the about page shows a message when no site information is set"""
    server = Server(_custom_name="TEST_ABOUT")
    server._state = None  # Set state without calling setup
    
    result = server.about()
    assert "No site information has been set" in result
    assert "set_site_information()" in result


def test_about_page_with_string_information():
    """Test that the about page renders string information correctly"""
    server = Server(_custom_name="TEST_ABOUT")
    server.set_information(
        author="John Doe",
        description="A test website",
        sources="https://example.com",
        planning="Planning document",
        links="https://github.com"
    )
    server._state = None  # Set state without calling setup
    
    result = server.about()
    
    # Check that all fields are present
    assert "Author" in result
    assert "John Doe" in result
    assert "Description" in result
    assert "A test website" in result
    assert "Sources" in result
    assert "https://example.com" in result
    assert "Planning" in result
    assert "Planning document" in result
    assert "Links" in result
    assert "https://github.com" in result


def test_about_page_with_list_information():
    """Test that the about page renders list information correctly"""
    server = Server(_custom_name="TEST_ABOUT")
    server.set_information(
        author="John Doe",
        description="A test website",
        sources=["https://example.com", "https://test.com"],
        planning="Planning document",
        links=["https://github.com", "https://gitlab.com"]
    )
    server._state = None  # Set state without calling setup
    
    result = server.about()
    
    # Check that lists are rendered as HTML lists
    assert "<ul>" in result
    assert "<li>" in result
    assert "https://example.com" in result
    assert "https://test.com" in result
    assert "https://github.com" in result
    assert "https://gitlab.com" in result


def test_about_page_with_page_content():
    """Test that the about page renders PageContent correctly"""
    server = Server(_custom_name="TEST_ABOUT")
    
    # Use PageContent components for some fields
    server.set_information(
        author=Header("Dr. Jane Smith", level=3),
        description="A test website",
        sources=BulletedList(["Source 1", "Source 2"]),
        planning="Planning document",
        links=["https://github.com"]
    )
    server._state = None  # Set state without calling setup
    
    result = server.about()
    
    # Check that PageContent is rendered
    assert "Author" in result
    assert "Dr. Jane Smith" in result
    assert "<h3>" in result  # Header component
    assert "Sources" in result
    assert "Source 1" in result
    assert "Source 2" in result
    assert "<ul>" in result  # BulletedList component


def test_about_page_urls_become_links():
    """Test that URLs are converted to clickable links"""
    server = Server(_custom_name="TEST_ABOUT")
    server.set_information(
        author="John Doe",
        description="A test website",
        sources="https://example.com",
        planning="https://planning.example.com",
        links=["https://github.com", "https://gitlab.com"]
    )
    server._state = None  # Set state without calling setup
    
    result = server.about()
    
    # Check that URLs are converted to <a> tags
    assert '<a href="https://example.com">https://example.com</a>' in result
    assert '<a href="https://planning.example.com">https://planning.example.com</a>' in result
    assert '<a href="https://github.com">https://github.com</a>' in result
    assert '<a href="https://gitlab.com">https://gitlab.com</a>' in result


def test_about_page_partial_information():
    """Test that the about page handles partial information correctly"""
    server = Server(_custom_name="TEST_ABOUT")
    server.set_information(
        author="John Doe",
        description="",
        sources=None,
        planning="",
        links=""
    )
    server._state = None  # Set state without calling setup
    
    result = server.about()
    
    # Only author should be present
    assert "Author" in result
    assert "John Doe" in result
    # Other fields should not show headers if empty
    # (we check that the method doesn't crash with empty/None values)
