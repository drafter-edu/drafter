import pytest
from threading import Thread
from drafter import *

"""
@pytest.fixture
def bottle_server(scope='session'):
    MAIN_SERVER.setup("")
    thread = Thread(target=MAIN_SERVER.app.run,
                    daemon=True,
                    kwargs=dict(host='localhost', port=8080))
    thread.start()

    yield MAIN_SERVER.app
"""
