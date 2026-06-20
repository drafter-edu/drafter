from drafter import *


@dataclass
class State:
    message: str

@route
def index(state: State) -> Page:
    return Page(state, [
        Button("🍪", "add_cookie"),
        "\n",
        state.message,
    ])

@route
def add_cookie(state: State) -> Page:
    state.message += "🍪"
    return Redirect("index", state)

start_server(State("🍪"))