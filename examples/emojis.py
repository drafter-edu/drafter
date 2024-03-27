from drafter import *


@dataclass
class State:
    pass

@route
def index(state: State) -> Page:
    return Page(state, [
        Button("🍪", "index")
    ])

start_server(State())