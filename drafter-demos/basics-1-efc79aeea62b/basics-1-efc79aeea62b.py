from drafter import *


@route
def index() -> Page:
    return Page(["Hello, world!"])


start_server()
