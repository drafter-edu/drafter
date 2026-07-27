from drafter import *


@route
def index() -> Page:
    return Page([
        "Hello from Drafter!"
    ])


start_server()
