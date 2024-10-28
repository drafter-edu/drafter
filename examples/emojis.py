from drafter import *


@dataclass
class State:
    message: str

@route
def index(state: State) -> Page:
    return Page(state, [
        state.message,
        Button("\"🍪", "add_cookie")
    ])

@route
def add_cookie(state: State) -> Page:
    state.message += "🍪"
    return index(state)

start_server(State("🍪"))