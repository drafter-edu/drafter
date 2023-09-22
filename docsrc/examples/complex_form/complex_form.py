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

@route
def change_name(state: State, new_name: str, new_availability: bool, new_animal: str, new_poem: str) -> Page:
    state.name = new_name
    state.available = new_availability
    state.favorite = new_animal
    state.poem = new_poem
    return index(state)


start_server(State("Dr. Bart", False, "dogs", ""))
