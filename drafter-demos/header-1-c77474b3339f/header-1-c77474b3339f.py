from drafter import *


@route
def index() -> Page:
    return Page([
        Header("Pet of the Month"),
        Header("Winner: Domino", 2),
        "A black cat of considerable dignity.\n",
        Header("Runner-up: Babbage", 2),
        "A small black mutt of considerable enthusiasm.\n"
    ])


start_server()
