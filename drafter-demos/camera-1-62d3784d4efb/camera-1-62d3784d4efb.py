from drafter import *
from dataclasses import dataclass


@dataclass
class State:
    pass


@route
def index(state: State) -> Page:
    return Page(state, [
        Header("Pet Portrait Studio"),
        "Hold your pet up to the camera!\n",
        Camera("shot"),
        "\n",
        Button("Save portrait", "portrait")
    ])


@route
def portrait(state: State, shot: Photo) -> Page:
    if shot.picture is None:
        return Page(state, [
            "No photo yet (" + shot.status + "). Go back and "
            "take one!\n",
            Button("Back", "index")
        ])
    return Page(state, [
        Header("A masterpiece"),
        Image(shot.picture),
        "\n",
        Button("Take another", "index")
    ])


start_server(State())
