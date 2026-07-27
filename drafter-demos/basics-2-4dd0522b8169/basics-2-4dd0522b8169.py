from drafter import *


@route
def index() -> Page:
    return Page([
        "First. ",
        "Still the first line. ",
        "Now a break.\n",
        "Second line."
    ])


start_server()
