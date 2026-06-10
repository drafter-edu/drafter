from drafter import *


def error_call():
    return 5 / 0
    

@route
def index(state: int) -> Page:
    return Page(state, [
        "Hello",
        error_call()
    ])
    
start_server(0)