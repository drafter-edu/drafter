from tests.helpers import *
from drafter import *
from dataclasses import dataclass

@dataclass
class State:
    name: str
    available: bool
    favorite: str
    poem: str

def test_complex_form(browser, splinter_headless):
    drafter_server = TestServer(State("Dr. Bart", False, "dogs", ""))

    @route(server=drafter_server.server)
    def index(state: State) -> Page:
        return Page(state, [
            Header("Existing Data"),
            "Current name: " + state.name,
            "Availabilty: " + str(state.available),
            "Favorite animal: " + state.favorite,
            "Poem: " + state.poem,
            HorizontalRule(),
            Header("Change the Data", 2),
            "What is your name?",
            TextBox("new_name", state.name),
            "Are you available?",
            CheckBox("new_availability", state.available),
            "Dogs, cats, or capybaras?",
            SelectBox("new_animal", ["dogs", "cats", "capybaras"], state.favorite),
            "Write me a poem, please.",
            TextArea("new_poem", state.poem),
            LineBreak(),
            Button("Submit", change_name)
        ])

    @route(server=drafter_server.server)
    def change_name(state: State, new_name: str, new_availability: bool, new_animal: str, new_poem: str) -> Page:
        state.name = new_name
        state.available = new_availability
        state.favorite = new_animal
        state.poem = new_poem
        return index(state)

    with drafter_server:
        browser.visit('http://localhost:8080')
        assert browser.is_text_present('Current name: Dr. Bart')
        assert browser.is_text_present('Availabilty: False')
        assert browser.is_text_present('Favorite animal: dogs')
        assert browser.is_text_present('Poem:')
        assert not browser.is_text_present('This text will not be there')

        browser.fill("new_name", "Ada Lovelace")
        browser.find_by_name('new_availability')[1].check()
        #print(browser.find_by_name("new_animal"))
        #browser.find_by_name("new_animal").select("capybaras")
        browser.find_by_name("new_animal").first.find_by_tag("option")[2].click()
        browser.fill("new_poem", "Roses are red, violets are blue.")
        browser.find_by_name(SUBMIT_BUTTON_KEY).click()

        assert browser.is_text_present('Current name: Ada Lovelace')
        assert browser.is_text_present('Availabilty: True')
        assert browser.is_text_present('Favorite animal: capybaras')
        assert browser.is_text_present('Poem: Roses are red, violets are blue.')
