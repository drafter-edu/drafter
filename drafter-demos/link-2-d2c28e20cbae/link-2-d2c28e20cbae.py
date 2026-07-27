from drafter import *


@route
def index() -> Page:
    return Page([
        "Drafter's code lives on ",
        Link("GitHub", "https://github.com/drafter-edu/drafter"),
        ".\n"
    ])


start_server()
