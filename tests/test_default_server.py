import pytest
from drafter import *
from webtest import TestApp

@pytest.fixture
def browser():
    MAIN_SERVER.setup(None)
    app = TestApp(MAIN_SERVER.app)
    with Browser(app=app) as b:  # 'app' is your Flask app instance
        yield b


@pytest.fixture(scope='session')
def splinter_headless():
    return True

def test_browser(browser, splinter_headless):
    browser.visit('http://localhost:8080')
    assert browser.is_text_present('Hello world')


def test_default_index_page(browser, splinter_headless):
    MAIN_SERVER.setup(None)
    app = TestApp(MAIN_SERVER.app)

    default_index_page = app.get("/")
    assert default_index_page.status == '200 OK'
    assert default_index_page.content_type == 'text/html'
    default_index_page.mustcontain("<html>")
    assert 'Hello world' in default_index_page
    assert 'Welcome to Drafter.' in default_index_page
    # Avoid false positives
    assert 'This text will not be there' not in default_index_page

def test_simple_input_form(browser, splinter_headless):
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
    MAIN_SERVER.setup("")
    app = TestApp(MAIN_SERVER.app)

    index_page = app.get("/")
    assert index_page.status == '200 OK'
    assert 'Enter your name:' in index_page

    form = index_page.form
    form['name'] = 'Ada Lovelace'
    print(form[SUBMIT_BUTTON_KEY].formaction)
    form[SUBMIT_BUTTON_KEY].action = "process_form"

    result_page = form.submit("XYZ") #SUBMIT_BUTTON_KEY)

    assert result_page.status == '200 OK'
    assert 'Hello, Ada Lovelace!' in result_page

