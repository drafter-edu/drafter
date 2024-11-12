import pytest
from drafter import *
from webtest import TestApp


def test_default_index_page():
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

def test_simple_input_form():
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

"""
@pytest.fixture(scope='session')
def splinter_headless():
    return True

def test_browser(browser, splinter_headless):
    MAIN_SERVER.setup(None)
    app = TestApp(MAIN_SERVER.app)

    assert app.get('/').status == '200 OK'  # fetch a page successfully
"""
"""url = "localhost:8080"
    browser.visit(url)
    browser.fill('q', 'splinter - python acceptance testing for web applications')
    # Find and click the 'search' button
    button = browser.find_by_name('btnK')
    # Interact with elements
    button.click()
    assert browser.is_text_present('splinter.cobrateam.info'), "splinter.cobrateam.info wasn't found... We need to"
    ' improve our SEO techniques'"""