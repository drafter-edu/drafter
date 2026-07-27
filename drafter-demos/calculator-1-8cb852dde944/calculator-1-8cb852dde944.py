from drafter import *
from dataclasses import dataclass


@dataclass
class State:
    first_number: str
    second_number: str
    result: str


@route
def index(state: State) -> Page:
    return Page(state, [
        Header("Adding Machine"),
        "What is the first number?",
        TextBox("first", state.first_number),
        "\nWhat is the second number?",
        TextBox("second", state.second_number),
        "\n",
        Button("Add", "add"),
        "\nThe result is: " + state.result
    ])


@route
def add(state: State, first: str, second: str) -> Page:
    state.first_number = first
    state.second_number = second
    if first.isdigit() and second.isdigit():
        state.result = str(int(first) + int(second))
    else:
        state.result = "not a number!"
    return index(state)


assert_state(add(State("", "", ""), "3", "4"), State("3", "4", "7"))
assert_state(add(State("", "", ""), "cat", "4"),
             State("cat", "4", "not a number!"))
assert_has(index(State("", "", "")), Button("Add", "add"))

start_server(State("", "", ""))
