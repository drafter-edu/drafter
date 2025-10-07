import pytest


def pytest_addoption(parser):
    """Add command line option to update snapshots"""
    parser.addoption(
        "--update-snapshots",
        action="store_true",
        default=False,
        help="Update snapshot files with new output"
    )


@pytest.fixture(scope='session')
def splinter_headless():
    return True
