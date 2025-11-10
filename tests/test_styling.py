"""
Tests for the styling system and theme registration
"""
import pytest
from pathlib import Path
from drafter.styling.themes import get_theme_system, Theme


def test_theme_registration():
    """Test that all expected themes are registered"""
    theme_system = get_theme_system()
    expected_themes = ['default', 'none', 'mvp', 'sakura', 'tacit', 'skeleton', '7', '98', 'XP']
    
    for theme_name in expected_themes:
        assert theme_name in theme_system.themes, f"Theme '{theme_name}' not registered"


def test_theme_has_css_paths():
    """Test that themes have CSS paths configured"""
    theme_system = get_theme_system()
    
    # Default theme should have CSS
    default_theme = theme_system.get_theme('default')
    assert len(default_theme.css_paths) > 0, "Default theme should have CSS paths"
    
    # None theme should have no CSS
    none_theme = theme_system.get_theme('none')
    assert len(none_theme.css_paths) == 0, "None theme should have no CSS paths"
    
    # Other themes should have CSS
    for theme_name in ['mvp', 'sakura', 'tacit', 'skeleton']:
        theme = theme_system.get_theme(theme_name)
        assert len(theme.css_paths) > 0, f"Theme '{theme_name}' should have CSS paths"


def test_theme_css_files_exist():
    """Test that theme CSS files exist in the assets directory"""
    # Get the assets directory relative to this test file
    test_dir = Path(__file__).parent
    repo_root = test_dir.parent
    assets_dir = repo_root / "src" / "drafter" / "assets" / "js" / "css"
    
    theme_system = get_theme_system()
    
    # Check that the base CSS files exist
    base_files = ['default.css', 'drafter_base.css', 'drafter_debug.css', 'drafter_deploy.css']
    for file in base_files:
        file_path = assets_dir / file
        assert file_path.exists(), f"Base CSS file {file} does not exist at {file_path}"
    
    # Check that theme CSS files exist
    theme_files = ['themes/mvp.css', 'themes/sakura.css', 'themes/tacit.css', 
                   'themes/skeleton.css', 'themes/7.css', 'themes/98.css', 'themes/XP.css']
    for file in theme_files:
        file_path = assets_dir / file
        assert file_path.exists(), f"Theme CSS file {file} does not exist at {file_path}"


def test_css_uses_class_selectors():
    """Test that CSS files use class selectors instead of high-specificity ID selectors"""
    test_dir = Path(__file__).parent
    repo_root = test_dir.parent
    assets_dir = repo_root / "src" / "drafter" / "assets" / "js" / "css"
    
    css_files = [
        assets_dir / 'default.css',
        assets_dir / 'drafter_base.css',
        assets_dir / 'drafter_debug.css',
        assets_dir / 'drafter_deploy.css',
    ]
    
    for css_file in css_files:
        if css_file.exists():
            content = css_file.read_text()
            
            # Check for class selectors
            assert '.drafter-' in content, f"{css_file.name} should use .drafter-* class selectors"
            
            # Check that we don't have nested ID selectors (which would have high specificity)
            # We allow #reset-button-- and #about-button-- as they are functional IDs
            lines = [line.strip() for line in content.split('\n')]
            for line in lines:
                # Skip comments and allowed IDs
                if line.startswith('/*') or line.startswith('*'):
                    continue
                if '#reset-button--' in line or '#about-button--' in line:
                    continue
                
                # Check for problematic nested ID patterns like #drafter-root-- #drafter-body--
                if '#drafter-root--' in line or ('#drafter-frame--' in line and not '.drafter-' in line):
                    # This would indicate a nested ID selector pattern
                    if '{' not in line:  # Not a declaration, likely a selector
                        pytest.fail(f"Found nested ID selector in {css_file.name}: {line}")


def test_site_html_has_classes():
    """Test that the site HTML template includes class attributes"""
    from drafter.site.site import SITE_HTML_TEMPLATE, DRAFTER_TAG_CLASSES
    
    # Verify that classes are added to the HTML
    for class_name in ['drafter-site', 'drafter-frame', 'drafter-body', 'drafter-header', 'drafter-footer']:
        assert class_name in SITE_HTML_TEMPLATE, f"Class '{class_name}' not found in SITE_HTML_TEMPLATE"
    
    # Verify that DRAFTER_TAG_CLASSES has the expected entries
    expected_classes = ['ROOT', 'SITE', 'FRAME', 'HEADER', 'BODY', 'FOOTER', 'FORM', 'DEBUG']
    for key in expected_classes:
        assert key in DRAFTER_TAG_CLASSES, f"Key '{key}' not found in DRAFTER_TAG_CLASSES"


def test_invalid_theme_error():
    """Test that requesting an invalid theme raises an error with suggestions"""
    theme_system = get_theme_system()
    
    with pytest.raises(ValueError) as exc_info:
        # Try to get a theme that doesn't exist
        from drafter.site.site import Site
        site = Site(theme="invalid_theme")
        site.render()
    
    error_message = str(exc_info.value)
    assert "invalid_theme" in error_message.lower(), "Error message should mention the invalid theme name"
