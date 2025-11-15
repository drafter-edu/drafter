from drafter import *


@route
def index(state: str) -> Page:
    return Page(
        state, ["Enter your name:", TextBox("name"), Button("Submit", process_form)]
    )


@route
def process_form(state: str, name: str) -> Page:
    return Page(state, ["Hello, " + name[0] + "!"])


start_server("")
