from bakery import assert_equal
from dataclasses import dataclass
from drafter import route, start_server, Page, TextBox, Button, add_website_css


@dataclass
class State:
    first_number: int
    second_number: int
    result: str

STYLE = """
<style>
    button.quit-button {
        color: red;
        float: right;
    }
</style>
"""

add_website_css("""
body {
    background-color: lightblue;
}
""")

@route
def index(state: State) -> Page:
    return Page(state, [
        STYLE,
        "What is the first number?",
        TextBox("first", str(state.first_number), "number", style_background_color='pink'),
        "What is the second number?",
        TextBox("second", str(state.second_number), "number"),
        Button("Add", add_page, classes="quit-button"),
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
    TextBox("first", "0", "number"),
    "What is the second number?",
    TextBox("second", "0", "number"),
    Button("Add", "add_page"),
    "The result is",
    ""
]))

assert_equal(add_page(State(0, 0, ""), "5", "3"), Page(State(5, 3, "8"), [
    "What is the first number?",
    TextBox("first", "5", "number" ),
    "What is the second number?",
    TextBox("second", "3", "number", ),
    Button("Add", "add_page"),
    "The result is",
    "8",
]))

start_server(State(0, 0, ""), reloader=True)