from bakery import assert_equal
from dataclasses import dataclass
from drafter import route, start_server, Page, TextBox, SubmitButton


@dataclass
class State:
    first_number: int
    second_number: int
    result: str


@route
def index(state: State) -> Page:
    return Page(state, [
        "What is the first number?",
        TextBox("first", state.first_number, "number", style_background_color='pink'),
        "What is the second number?",
        TextBox("second", state.second_number, "number"),
        SubmitButton("Add", add_page),
        "The result is",
        state.result
    ])


@route
def add_page(state: State, first: str, second: str) -> Page:
    if not first.isdigit() or not second.isdigit():
        return index(state)
    state.first_number = int(first)
    state.second_number = int(second)
    state.result = str(int(first) + int(second))
    return index(state)


assert_equal(index(State(0, 0, "")), Page(State(0, 0, ""), [
    "What is the first number?",
    TextBox("first", "number"),
    "What is the second number?",
    TextBox("second", "number"),
    SubmitButton("Add", "add_page"),
    "The result is",
    ""
]))

assert_equal(add_page(State(0, 0, ""), "5", "3"), Page(State(5, 3, "8"), [
    "What is the first number?",
    TextBox("first", "number", 5),
    "What is the second number?",
    TextBox("second", "number", 3),
    SubmitButton("Add", "add_page"),
    "The result is",
    "8",
]))

start_server(State(0, 0, ""), reloader=True)