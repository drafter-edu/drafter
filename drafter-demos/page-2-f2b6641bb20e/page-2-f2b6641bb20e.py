from drafter import *


@route
def index() -> Page:
    return Page([
        "This site remembers nothing.\n",
        Link("See for yourself", "again")
    ])


@route
def again() -> Page:
    return Page([
        "Still nothing remembered.\n",
        Link("Back", "index")
    ])


start_server()
