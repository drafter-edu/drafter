from drafter import *
from dataclasses import dataclass


@dataclass
class State:
    name: str
    available: bool
    favorite: str
    poem: str


@route
def index(state: State) -> Page:
    return Page(state, [
        Header("Saved so far"),
        "Name: " + state.name + "\n",
        "Available: " + str(state.available) + "\n",
        "Favorite animal: " + state.favorite + "\n",
        "Poem: " + state.poem + "\n",
        HorizontalRule(),
        Header("Change the data", 2),
        "What is your name?",
        TextBox("new_name", state.name),
        "\n",
        CheckBox("new_availability", state.available),
        " I am available for adventures\n",
        "Dogs, cats, or capybaras?",
        SelectBox("new_animal", ["dogs", "cats", "capybaras"],
                  state.favorite),
        "\nWrite me a poem, please.",
        TextArea("new_poem", state.poem),
        "\n",
        Button("Submit", "save")
    ])


@route
def save(state: State, new_name: str, new_availability: bool,
         new_animal: str, new_poem: str) -> Page:
    state.name = new_name
    state.available = new_availability
    state.favorite = new_animal
    state.poem = new_poem
    return index(state)


assert_state(
    save(State("", False, "dogs", ""), "Ada", True, "capybaras", "wow"),
    State("Ada", True, "capybaras", "wow"))
assert_has(index(State("", False, "dogs", "")), Button("Submit", "save"))

start_server(State("Dr. Bart", False, "dogs", ""))
