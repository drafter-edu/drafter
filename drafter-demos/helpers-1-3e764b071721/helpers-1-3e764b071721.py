from drafter import *


@route
def index() -> Page:
    return Page([
        bold("This line is bold.\n"),
        italic("This one is italic.\n"),
        change_color("This one is crimson.\n", "crimson"),
        bold(change_color("This one is both.\n", "crimson"))
    ])


start_server()
