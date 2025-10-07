from tests.helpers import *


def test_selectbox_with_placeholder(browser, splinter_headless):
    """Test that SelectBox displays a placeholder when default_value is not in options"""
    drafter_server = TestServer()

    @route(server=drafter_server.server)
    def index(state: str) -> Page:
        return Page(state, [
            "Choose an option:",
            SelectBox("choice", ["A", "B", "C"], "pick one"),
            Button("Submit", process_form)
        ])

    @route(server=drafter_server.server)
    def process_form(state: str, choice: str) -> Page:
        return Page(state, [
            f"You chose: {choice}"
        ])

    with drafter_server:
        browser.visit('http://localhost:8080')
        assert browser.is_text_present('Choose an option:')
        
        # Check that the placeholder text appears in the select box
        select_element = browser.find_by_name("choice").first
        # The first option should be the placeholder
        options = select_element.find_by_tag("option")
        assert len(options) == 4  # placeholder + 3 options
        assert "pick one" in options[0].text
        
        # Select a real option and submit
        options[1].click()  # Select "A"
        browser.find_by_name(SUBMIT_BUTTON_KEY).click()
        
        assert browser.is_text_present('You chose: A')


def test_selectbox_with_default_in_options(browser, splinter_headless):
    """Test that SelectBox works correctly when default_value is in options"""
    drafter_server = TestServer()

    @route(server=drafter_server.server)
    def index(state: str) -> Page:
        return Page(state, [
            "Choose an option:",
            SelectBox("choice", ["A", "B", "C"], "B"),
            Button("Submit", process_form)
        ])

    @route(server=drafter_server.server)
    def process_form(state: str, choice: str) -> Page:
        return Page(state, [
            f"You chose: {choice}"
        ])

    with drafter_server:
        browser.visit('http://localhost:8080')
        assert browser.is_text_present('Choose an option:')
        
        # Check that the default value is selected
        select_element = browser.find_by_name("choice").first
        options = select_element.find_by_tag("option")
        assert len(options) == 3  # Just the 3 options, no placeholder
        
        # Submit without changing selection (should submit "B")
        browser.find_by_name(SUBMIT_BUTTON_KEY).click()
        
        assert browser.is_text_present('You chose: B')


def test_selectbox_without_default(browser, splinter_headless):
    """Test that SelectBox works correctly without a default_value"""
    drafter_server = TestServer()

    @route(server=drafter_server.server)
    def index(state: str) -> Page:
        return Page(state, [
            "Choose an option:",
            SelectBox("choice", ["A", "B", "C"]),
            Button("Submit", process_form)
        ])

    @route(server=drafter_server.server)
    def process_form(state: str, choice: str) -> Page:
        return Page(state, [
            f"You chose: {choice}"
        ])

    with drafter_server:
        browser.visit('http://localhost:8080')
        assert browser.is_text_present('Choose an option:')
        
        # Check that no placeholder is shown
        select_element = browser.find_by_name("choice").first
        options = select_element.find_by_tag("option")
        assert len(options) == 3  # Just the 3 options, no placeholder
        
        # Submit with first option (default browser behavior)
        browser.find_by_name(SUBMIT_BUTTON_KEY).click()
        
        assert browser.is_text_present('You chose: A')
