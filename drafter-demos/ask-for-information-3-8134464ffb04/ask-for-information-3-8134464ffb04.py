from drafter import *
from dataclasses import dataclass


@dataclass
class State:
    total: int


@route
def index(state: State) -> Page:
    return Page(state, [
        "Tickets cost 5 gold each.\n",
        "How many tickets?",
        TextBox("tickets", 2),
        "\n",
        Button("Get the price", "price")
    ])


@route
def price(state: State, tickets: int) -> Page:
    state.total = tickets * 5
    return Page(state, [
        str(tickets) + " tickets cost " + str(state.total) + " gold.\n",
        Button("Change the order", "index")
    ])


assert_state(price(State(0), 3), State(15))

start_server(State(0))
