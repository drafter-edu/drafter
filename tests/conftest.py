import pytest

@pytest.fixture(scope='session')
def splinter_headless():
    return True
