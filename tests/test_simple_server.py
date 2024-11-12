import pytest
from drafter import *
from threading import Thread
from contextlib import contextmanager

@pytest.fixture(scope='session')
def splinter_headless():
    return True

@contextmanager
def start_threaded_server(initial_state=None, setup_kwargs=None,
                          run_kwargs=None):
    if setup_kwargs is None:
        setup_kwargs = {}
    if run_kwargs is None:
        run_kwargs = {}
    run_kwargs.setdefault('host', 'localhost')
    run_kwargs.setdefault('port', 8080)
    drafter_server = Server(**setup_kwargs)
    drafter_server.setup(initial_state)
    thread = Thread(target=drafter_server.run, daemon=True,
                    args=[initial_state], kwargs=run_kwargs)
    thread.start()
    yield thread
    thread.join()
    print("Server will shutdown?")

def test_simple_default_page(browser, splinter_headless):
    with start_threaded_server():
        browser.visit('http://localhost:8080')
        assert browser.is_text_present('Hello world')
        assert browser.is_text_present('Welcome to Drafter.')
        assert not browser.is_text_present('This text will not be there')

def test_simple_form(browser, splinter_headless):
    @route
    def index(state: str) -> Page:
        return Page([
            "Enter your name:",
            TextBox("name"),
            Button("Submit", process_form)
        ])

    @route
    def process_form(state: str, name: str) -> Page:
        return Page([
            "Hello, " + name + "!"
        ])

    with start_threaded_server(""):
        browser.visit('http://localhost:8080')
        assert browser.is_text_present('Enter your name:')

        browser.fill("name", "Ada Lovelace")
        browser.find_by_name(SUBMIT_BUTTON_KEY).click()

        assert browser.is_text_present('Hello, Ada Lovelace!')