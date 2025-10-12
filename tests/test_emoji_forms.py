"""Test emoji support in SelectBox and other form components."""
from tests.helpers import *

@dataclass
class State:
    stars: str
    message: str

def test_emoji_in_selectbox(browser, splinter_headless):
    """Test that emojis work in SelectBox options and values."""
    drafter_server = TestServer(State("⭐", ""))

    @route(server=drafter_server.server)
    def index(state: State) -> Page:
        return Page(state, [
            "Select star rating:",
            SelectBox("star_rating", ["⭐", "⭐⭐", "⭐⭐⭐"], state.stars),
            Button("Save", save_rating)
        ])

    @route(server=drafter_server.server)
    def save_rating(state: State, star_rating: str) -> Page:
        state.stars = star_rating
        state.message = f"You selected: {star_rating}"
        return Page(state, [
            state.message,
            Button("Back", index)
        ])

    with drafter_server:
        browser.visit('http://localhost:8080')
        
        # Verify the page loads with emoji options
        assert browser.is_text_present('Select star rating:')
        
        # Select a different emoji option
        browser.find_by_name('star_rating').select('⭐⭐⭐')
        
        # Click the save button
        browser.find_by_name(SUBMIT_BUTTON_KEY).click()
        
        # Verify the emoji was properly saved and displayed
        assert browser.is_text_present('You selected: ⭐⭐⭐')
        
        # Go back and verify the state persisted
        browser.find_by_name(SUBMIT_BUTTON_KEY).click()
        assert browser.is_text_present('Select star rating:')

def test_emoji_in_textbox(browser, splinter_headless):
    """Test that emojis work in TextBox values."""
    drafter_server = TestServer(State("⭐", "🎉"))

    @route(server=drafter_server.server)
    def index(state: State) -> Page:
        return Page(state, [
            "Enter emoji message:",
            TextBox("emoji_message", state.message),
            Button("Save", save_message)
        ])

    @route(server=drafter_server.server)
    def save_message(state: State, emoji_message: str) -> Page:
        state.message = emoji_message
        return Page(state, [
            f"Message: {state.message}",
            Button("Back", index)
        ])

    with drafter_server:
        browser.visit('http://localhost:8080')
        
        # Verify the page loads with emoji in textbox
        assert browser.is_text_present('Enter emoji message:')
        
        # Change the emoji message
        browser.fill('emoji_message', '🚀 Hello World! 🌍')
        
        # Click the save button
        browser.find_by_name(SUBMIT_BUTTON_KEY).click()
        
        # Verify the emoji was properly saved and displayed
        assert browser.is_text_present('Message: 🚀 Hello World! 🌍')
