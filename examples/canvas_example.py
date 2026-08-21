from dataclasses import dataclass

from drafter import *


@dataclass
class State:
    pass


@route
def index(state: State) -> Page:
    return Page(
        state,
        [
            Header("Doodle"),
            Canvas("doodle", width=300, height=120),
            "\n",
            Button("Draw a sunset", "draw"),
        ],
    )


@route
def draw(state: State) -> Page:
    import js

    canvas = js.document.getElementById("doodle")
    if canvas is not None:
        brush = canvas.getContext("2d")
        brush.fillStyle = "coral"
        brush.fillRect(0, 0, 300, 120)
        brush.fillStyle = "gold"
        brush.beginPath()
        brush.arc(150, 120, 40, 3.14, 0)
        brush.fill()
    return Update(state)


start_server(State())
