from drafter import *
from dataclasses import dataclass


@dataclass
class State:
    pass


@route
def index(state: State) -> Page:
    return Page(state, [
        Header("Photo Booth"),
        Camera("snapshot", facing="user"),
        "\n",
        Button("Develop", "develop")
    ])


@route
def develop(state: State, snapshot: Picture) -> Page:
    return Page(state, [
        Header("Your prints"),
        Image(snapshot.grayscale()),
        Image(snapshot.flip_horizontal()),
        "\n",
        Button("New photo", "index")
    ])


start_server(State())
