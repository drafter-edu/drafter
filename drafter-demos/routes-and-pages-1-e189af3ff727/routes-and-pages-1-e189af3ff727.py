from drafter import *


@route
def index() -> Page:
    return Page([
        "This is the first page.\n",
        Button("To the second page", "second"),
        Button("To the third page", "third")
    ])


@route
def second() -> Page:
    return Page([
        "This is the second page.\n",
        Button("To the third page", "third"),
        Button("Back to the start", "index")
    ])


@route
def third() -> Page:
    return Page([
        "This is the third page.\n",
        Button("Back to the start", "index")
    ])


start_server()
