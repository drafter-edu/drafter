from drafter import *
from dataclasses import dataclass

add_website_js_file(
    "https://cdn.jsdelivr.net/npm/canvas-confetti@1.9.3/dist/confetti.browser.min.js"
)


@dataclass
class State:
    pass


@route
def index(state: State) -> Page:
    return Page(state, [
        Header("Adoption Day"),
        "Domino the black cat has a new home.\n",
        Button("Celebrate", "celebrate")
    ])


@route
def celebrate(state: State) -> Update:
    import js
    js.confetti()
    return Update(state)


start_server(State())
