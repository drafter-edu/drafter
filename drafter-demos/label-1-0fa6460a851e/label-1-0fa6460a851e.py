from drafter import *
from dataclasses import dataclass


@dataclass
class State:
    signed_up: bool


@route
def index(state: State) -> Page:
    agree_box = CheckBox("agrees")
    name_box = TextBox("volunteer")
    return Page(state, [
        Header("Volunteer Sign-up"),
        Label("Your name:", name_box),
        name_box,
        "\n",
        agree_box,
        Label(" I agree to water the plants", agree_box),
        "\n",
        Button("Sign up", "sign")
    ])


@route
def sign(state: State, volunteer: str, agrees: bool) -> Page:
    state.signed_up = agrees
    return index(state)


start_server(State(False))
