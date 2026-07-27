from drafter import *


@route
def index() -> Page:
    return Page([
        "The front porch.\n",
        Button("Go inside", "kitchen")
    ])


@route
def kitchen() -> Page:
    return Page([
        "The kitchen smells like toast.\n",
        Link("Back to the porch", "index")
    ])


start_server()
