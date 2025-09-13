import pytest
import os

@pytest.fixture(scope='session')
def splinter_headless():
    return True

@pytest.fixture(scope='session')
def splinter_webdriver():
    return 'chrome'

@pytest.fixture(scope='session')
def splinter_webdriver_options():
    """Configure Chrome options for CI environments"""
    chrome_options = [
        '--headless',
        '--no-sandbox',
        '--disable-dev-shm-usage',
        '--disable-gpu',
        '--disable-extensions',
        '--disable-web-security',
        '--window-size=1920,1080',
        '--disable-background-timer-throttling',
        '--disable-renderer-backgrounding',
        '--disable-backgrounding-occluded-windows',
        '--disable-features=TranslateUI',
        '--disable-ipc-flooding-protection',
        '--disable-background-networking',
        '--disable-sync',
        '--disable-default-apps',
        '--no-first-run',
        '--no-default-browser-check'
    ]
    
    return chrome_options

@pytest.fixture(scope='session')
def splinter_wait_time():
    """Default wait time for splinter browser operations"""
    return 5

@pytest.fixture(scope='session')
def splinter_browser_load_timeout():
    """Timeout for browser page loads"""
    return 30
