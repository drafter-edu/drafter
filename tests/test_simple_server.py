import pytest
from drafter import *
from threading import Thread
from contextlib import contextmanager
import sys
from bottle import WSGIRefServer, ServerAdapter, Bottle

@pytest.fixture(scope='session')
def splinter_headless():
    return True

class MyWSGIRefServer(ServerAdapter):
    server = None

    def run(self, handler):
        from wsgiref.simple_server import make_server, WSGIRequestHandler
        if self.quiet:
            class QuietHandler(WSGIRequestHandler):
                def log_request(*args, **kw): pass
            self.options['handler_class'] = QuietHandler
        self.server = make_server(self.host, self.port, handler, **self.options)
        self.server.serve_forever()

    def stop(self):
        self.server.server_close()

class TestServer:
    def __init__(self, initial_state=None, setup_kwargs=None,
                 run_kwargs=None, custom_name="TEST_SERVER"):
        if setup_kwargs is None:
            setup_kwargs = {}
        if '_custom_name' not in setup_kwargs:
            setup_kwargs['_custom_name'] = custom_name
        if run_kwargs is None:
            run_kwargs = {}
        run_kwargs.setdefault('host', 'localhost')
        run_kwargs.setdefault('port', 8080)
        self.initial_state = initial_state
        self.setup_kwargs = setup_kwargs
        self.run_kwargs = run_kwargs
        self.custom_name = custom_name
        self.server = Server(**setup_kwargs)

    def __enter__(self):
        if not self.server.routes:
            route("index", self.server)(default_index)

        self.wsgi = MyWSGIRefServer(
            host=self.run_kwargs.get('host'),
            port=int(self.run_kwargs.get('port')))
        self.server.setup(self.initial_state)
        self.thread = Thread(target=self.run_server, daemon=True)
        self.thread.start()
        return self.thread

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.wsgi.stop()
        self.thread.join()

    def run_server(self):
        self.server.run(server=self.wsgi, **self.run_kwargs)



def test_simple_default_page(browser, splinter_headless):
    drafter_server = TestServer()
    with drafter_server:
        print("BNETA")
        browser.visit('http://localhost:8080')
        assert browser.is_text_present('Hello world')
        assert browser.is_text_present('Welcome to Drafter.')
        assert not browser.is_text_present('This text will not be there')

def test_simple_form(browser, splinter_headless):
    drafter_server = TestServer()

    @route(server=drafter_server.server)
    def index(state: str) -> Page:
        return Page([
            "Enter your name:",
            TextBox("name"),
            Button("Submit", process_form)
        ])

    @route(server=drafter_server.server)
    def process_form(state: str, name: str) -> Page:
        return Page([
            "Hello, " + name + "!"
        ])

    with drafter_server:
        browser.visit('http://localhost:8080')
        assert browser.is_text_present('Enter your name:')

        browser.fill("name", "Ada Lovelace")
        browser.find_by_name(SUBMIT_BUTTON_KEY).click()

        assert browser.is_text_present('Hello, Ada Lovelace!')