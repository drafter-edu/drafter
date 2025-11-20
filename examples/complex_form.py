from drafter import *


@dataclass
class State:
    name: str
    available: bool
    favorite: str
    poem: str


@route
def index(state: State) -> Page:
    return Page(
        state,
        [
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
            Button("Submit", change_name),
        ],
    )


@route
def change_name(
    state: State, new_name: str, new_availability: bool, new_animal: str, new_poem: str
) -> Page:
    state.name = new_name
    state.available = new_availability
    state.favorite = new_animal
    state.poem = new_poem
    return index(state)


assert_equal(
    index(State(name="Dr. Bart", available=False, favorite="dogs", poem="")),
    Page(
        State(name="Dr. Bart", available=False, favorite="dogs", poem=""),
        [
            Header("Existing Data"),
            "Current name: Dr. Bart",
            "Availabilty: False",
            "Favorite animal: dogs",
            "Poem: ",
            HorizontalRule(),
            Header("Change the Data", 2),
            "What is your name?",
            TextBox("new_name", "Dr. Bart"),
            "Are you available?",
            CheckBox("new_availability"),
            "Dogs, cats, or capybaras?",
            SelectBox("new_animal", ["dogs", "cats", "capybaras"], "dogs"),
            "Write me a poem, please.",
            TextArea("new_poem"),
            LineBreak(),
            Button("Submit", "change_name"),
        ],
    ),
)

start_server(State("Dr. Bart", False, "dogs", ""))
