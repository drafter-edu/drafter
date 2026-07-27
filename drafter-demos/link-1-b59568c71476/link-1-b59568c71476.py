from drafter import *


@route
def index() -> Page:
    return Page([
        "Welcome to the museum.\n",
        Link("Visit the gift shop", "shop")
    ])


@route
def shop() -> Page:
    return Page([
        "Everything is free today.\n",
        Link("Back to the entrance", "index")
    ])


start_server()
