from drafter import *
from dataclasses import dataclass


@dataclass
class State:
    toppings: list[str]


@route
def index(state: State) -> Page:
    return Page(state, [
        Header("Pizza Order"),
        "Toppings on the order: " + str(len(state.toppings)) + "\n",
        BulletedList(state.toppings),
        "Choose your toppings:\n",
        SelectBox("chosen",
                  ["cheese", "olives", "basil", "peppers"],
                  multiple=True),
        "\n",
        Button("Order", "order")
    ])


@route
def order(state: State, chosen: list[str]) -> Page:
    state.toppings = chosen
    return index(state)


start_server(State([]))
