from drafter import *

@dataclass
class State:
    cookies: int

@route
def index(state: State) -> Page:
    return Page(state, [
        f"{state.cookies} 🍪s",
        Button("🍪", buy)
    ])

@route
def buy(state: State) -> Page:
    state.cookies += 1
    return index(state)

start_server(State(0))
