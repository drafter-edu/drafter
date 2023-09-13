from drafter import *


@route
def index(state: str) -> Page:
    return Page(state, [
        state
    ])


start_server("Hello World")
