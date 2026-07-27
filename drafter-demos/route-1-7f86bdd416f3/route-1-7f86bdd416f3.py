from drafter import *


@route
def index() -> Page:
    return Page([
        "The front page.\n",
        Button("Visit the other page", "second")
    ])


@route
def second() -> Page:
    return Page([
        "The route named second built this page.\n",
        Button("Home", "index")
    ])


start_server()
