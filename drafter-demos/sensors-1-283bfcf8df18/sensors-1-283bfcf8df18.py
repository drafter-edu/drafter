from drafter import *
from dataclasses import dataclass


@dataclass
class State:
    pass


@route
def index(state: State) -> Page:
    return Page(state, [
        Header("Passport Photos"),
        Camera("shot"),
        "\n",
        Button("Develop the roll", "develop")
    ])


@route
def develop(state: State, shot: Photo) -> Page:
    if shot.picture is None:
        return Page(state, [
            "No photo to develop (" + shot.status + ").\n",
            Button("Back to the studio", "index")
        ])
    return Page(state, [
        Header("The roll"),
        shot.picture.resize(120, 90),
        shot.picture.grayscale().resize(120, 90),
        shot.picture.flip_horizontal().resize(120, 90),
        "\n",
        Button("New pose", "index")
    ])


start_server(State())
