from tests.helpers import *
from tests.test_retry_wrapper import retry_on_network_error


@retry_on_network_error(max_retries=3, delay=2.0)
def test_simple_default_page(browser, splinter_headless):
    drafter_server = TestServer()
    with drafter_server:
        browser.visit('http://localhost:8080')
        assert browser.is_text_present('Hello world')
        assert browser.is_text_present('Welcome to Drafter.')
        assert not browser.is_text_present('This text will not be there')

@retry_on_network_error(max_retries=3, delay=2.0)
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


@retry_on_network_error(max_retries=3, delay=2.0)
def test_two_box_form(browser, splinter_headless):
    drafter_server = TestServer()

    @route(server=drafter_server.server)
    def index(state: str) -> Page:
        return Page([
            "Enter your name:",
            TextBox("name"),
            "Enter your age:",
            TextBox("age"),
            Button("Submit", process_form)
        ])

    @route(server=drafter_server.server)
    def process_form(state: str, name: str, age: int) -> Page:
        return Page([
            "Hello, " + name + "!",
            "You are " + str(age) + " years old."
        ])

    with drafter_server:
        browser.visit('http://localhost:8080')
        assert browser.is_text_present('Enter your name:')

        browser.fill("name", "Ada Lovelace")
        browser.fill("age", "36")
        browser.find_by_name(SUBMIT_BUTTON_KEY).click()

        assert browser.is_text_present('Hello, Ada Lovelace!')
        assert browser.is_text_present('You are 36 years old.')