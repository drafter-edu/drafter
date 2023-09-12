from drafter import *


@dataclass
class State:
    name: str
    available: bool
    favorite: str
    poem: str

@route
def index(state: State) -> Page:
    return Page(state, [
        "Current name: " + state.name,
        "Availabilty: " + str(state.available),
        "What is your name?",
        TextBox("name", state.name),
        "Are you available?",
        CheckBox("available", state.available),
        "Dogs, cats, or capybaras?",
        SelectBox("favorite", ["dogs", "cats", "capybaras"], state.favorite),
        "Write me a poem, please.",
        TextArea("poem", state.poem),
        Button("Submit", change_name)
    ])

@route
def change_name(state: State, name: str, available: bool, favorite: str, poem: str) -> Page:
    state.name = name
    state.available = available
    state.favorite = favorite
    state.poem = poem
    return index(state)


start_server(State("Dr. Bart", False, "dogs", ""))
