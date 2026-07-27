from drafter import *


@route
def index() -> Page:
    return Page([
        "This is a simple Drafter page.\n",
        "Each string in the list becomes text on the page.\n",
        "Items appear in the order you list them."
    ])


start_server()
