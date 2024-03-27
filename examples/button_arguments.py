from drafter import *

@dataclass
class State:
    pass


@route
def index(state: State) -> Page:
    return Page(state, [
        "Welcome to my site!",
        TextBox("pears", 7),
        TextBox("plums", "3"),
        Argument("apples", 5),
        Button("Buy", "buy_page", Argument("oranges", 7))
    ])

@route
def buy_page(state: State, apples: int, oranges: int, pears: int, plums: str) -> Page:
    return Page(state, [
        f"You bought {apples} apples, {oranges} oranges, {plums} plums, and {pears} pears",
    ])

start_server(State())