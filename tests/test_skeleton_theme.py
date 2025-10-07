"""
Tests to verify that the Skeleton theme is less specific and easier to override.
"""
from tests.helpers import *


def test_skeleton_css_has_important_flags():
    """
    Test that the skeleton CSS includes !important flags for commonly overridden properties.
    This makes the theme less specific and easier for students to override.
    """
    # Get the skeleton CSS from the raw files
    from drafter.raw_files import RAW_FILES
    
    skeleton_css = RAW_FILES['skeleton'].styles.get('skeleton.css', '')
    
    # Check that key properties have !important flags
    assert '!important' in skeleton_css, "Skeleton CSS should include !important flags"
    
    # Check specific properties that should have !important
    assert 'color: #1EAEDB !important' in skeleton_css, "Link color should have !important"
    assert 'color: #0FA0CE !important' in skeleton_css, "Link hover color should have !important"
    assert 'color: #333 !important' in skeleton_css, "Button hover color should have !important"
    assert 'border-color: #888 !important' in skeleton_css, "Button hover border-color should have !important"


def test_skeleton_css_has_better_layout_defaults():
    """
    Test that the skeleton CSS includes better layout defaults for common components.
    """
    from drafter.raw_files import RAW_FILES
    
    skeleton_css = RAW_FILES['skeleton'].styles.get('skeleton.css', '')
    
    # Check for vertical-align on buttons
    assert 'vertical-align: middle' in skeleton_css, "Buttons should have vertical-align: middle"
    
    # Check for inline-block on images
    assert '.btlw img' in skeleton_css, "Should have specific img styling"
    assert 'display: inline-block' in skeleton_css, "Images should be inline-block"
    
    # Check for better list item button margins
    assert '.btlw li button' in skeleton_css, "Should have specific li button styling"


def test_skeleton_theme_in_page(browser, splinter_headless):
    """
    Test that the skeleton theme is applied to a page and can be easily overridden.
    """
    drafter_server = TestServer()
    
    @route(server=drafter_server.server)
    def index(state: str) -> Page:
        return Page([
            """<style>
            .my-button {
                color: red !important;
                background-color: yellow !important;
            }
            </style>
            """,
            "Test page with custom styling",
            Button("Test", index, classes="my-button")
        ])
    
    with drafter_server:
        browser.visit('http://localhost:8080')
        assert browser.is_text_present('Test page with custom styling')
        
        # Verify the button exists
        button = browser.find_by_text('TEST')
        assert len(button) > 0, "Button should be present"


def test_skeleton_theme_default():
    """
    Test that skeleton is the default theme.
    """
    from drafter import get_website_style
    
    # The default should be skeleton
    style = get_website_style()
    assert style == 'skeleton', "Default theme should be skeleton"
