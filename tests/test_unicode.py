from tests.helpers import *

@dataclass
class State:
    message: str

def test_emojis(browser, splinter_headless):
    drafter_server = TestServer(State("🍪"))

    @route(server=drafter_server.server)
    def index(state: State) -> Page:
        return Page(state, [
            state.message,
            Button("\"🍪", "add_cookie")
        ])

    @route(server=drafter_server.server)
    def add_cookie(state: State) -> Page:
        state.message += "🍪"
        return index(state)

    with drafter_server:
        browser.visit('http://localhost:8080')
        assert browser.is_text_present('🍪')

        browser.find_by_name(SUBMIT_BUTTON_KEY).click()

        assert browser.is_text_present('🍪🍪')

        browser.find_by_name(SUBMIT_BUTTON_KEY).click()

        assert browser.is_text_present('🍪🍪🍪')