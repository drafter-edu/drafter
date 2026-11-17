from drafter import *
from dataclasses import dataclass


@dataclass
class State:
    pass


@route
def index(state: State) -> Page:
    return Page(state, [
        Header("Dinner Bell"),
        Div("Domino the black cat is napping.", id="bell"),
        Button("Remind me in three seconds", "set_reminder")
    ])


@route
def set_reminder(state: State) -> Update:
    import js
    from pyodide.ffi import create_once_callable

    def ring():
        js.document.getElementById("bell").textContent = "Time to feed Domino!"

    js.setTimeout(create_once_callable(ring), 3000)
    return Update(state)


start_server(State())
