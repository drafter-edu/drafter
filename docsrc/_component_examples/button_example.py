from drafter import *

@route
def index(state: int) -> Page:
    return Page(state, [
        f"Counter: {state}",
        Button("Increment", increment),
        Button("Decrement", decrement),
        Button("Reset", reset)
    ])

@route
def increment(state: int) -> Page:
    return index(state + 1)

@route
def decrement(state: int) -> Page:
    return index(state - 1)

@route
def reset(state: int) -> Page:
    return index(0)

start_server(0)