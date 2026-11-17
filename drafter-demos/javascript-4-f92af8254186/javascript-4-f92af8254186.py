from drafter import *
from dataclasses import dataclass


@dataclass
class State:
    code: str


@route
def index(state: State) -> Page:
    return Page(state, [
        Header("Your Invitation"),
        "Share this code with a friend: " + state.code + "\n",
        Button("Copy the code", "copy_code"),
        Span("", id="status")
    ])


@route
def copy_code(state: State) -> Update:
    import js

    def show_copied(result):
        js.document.getElementById("status").textContent = " Copied!"

    def show_refused(error):
        js.document.getElementById("status").textContent = " Could not copy."

    js.navigator.clipboard.writeText(state.code).then(show_copied, show_refused)
    return Update(state)


start_server(State("CORGI-2026"))
