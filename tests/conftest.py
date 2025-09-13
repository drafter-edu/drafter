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
        '--window-size=1920,1080'
    ]
    
    return chrome_options

@pytest.fixture(scope='session')
def splinter_driver_kwargs():
    """Additional driver configuration"""
    return {}
