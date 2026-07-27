from drafter import *
from dataclasses import dataclass


@dataclass
class State:
    portrait: Picture


@route
def index(state: State) -> Page:
    return Page(state, [
        Header("Portrait Studio"),
        state.portrait,
        "\nChoose a new portrait:",
        FileUpload("new_portrait", accept="image/*"),
        "\n",
        Button("Use it", "update")
    ])


@route
def update(state: State, new_portrait: Picture | None) -> Page:
    if new_portrait is not None:
        state.portrait = new_portrait
    return index(state)


start_server(State(Picture.new(160, 120, "lightsteelblue")))
