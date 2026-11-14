from drafter import *
from dataclasses import dataclass


@dataclass
class State:
    wishes: list[str]


@route
def index(state: State) -> Page:
    if state.wishes:
        display = BulletedList(state.wishes)
    else:
        display = "Your wishlist is empty. Add something!"
    return Page(state, [
        "Wishlist:\n",
        display,
        "\n",
        TextBox("wish"),
        "\n",
        Button("Add to wishlist", "add_wish")
    ])


@route
def add_wish(state: State, wish: str) -> Page:
    state.wishes.append(wish)
    return index(state)


assert_has(index(State([])), "empty")

start_server(State([]))
