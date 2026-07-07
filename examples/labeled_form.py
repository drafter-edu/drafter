from drafter import *


@dataclass
class State:
    pass


"""
Same deal with the CustomTextBox; instead of writing it in HTML, use the appropriate
Drafter components to generate the corresponding HTML elements.
"""


def CustomTextBox(name: str, label: str, default_value: str) -> PageContent:
    return Div(
        Label(label, name),
        TextBox(name, default_value, size="28"),
    )


@route
def index(state: State) -> Page:
    return Page(
        state,
        [
            CustomTextBox("username", "Username", ""),
            CustomTextBox("email", "Email", ""),
        ],
    )


start_server(State())
