from bakery import assert_equal
from dataclasses import dataclass
from drafter import route, start_server, Page, TextBox, Button, Text

@route("index")
def index() -> Page:
    return Page(None, [
        "What is the first number?",
        TextBox("first"),
        "What is the second number?",
        TextBox("second"),
        Button("Add", "add_page")
    ])


@route("add_page")
def add_page(first: str, second: str) -> Page:
    result = str(int(first) + int(second))
    return Page(None, [
        "The result is", result
    ])


assert_equal(index(), Page(None, [
    "What is the first number?",
    TextBox("first", "number"),
    "What is the second number?",
    TextBox("second", "number"),
    Button("Add", "add")
]))

assert_equal(add_page("5", "3"), Page(None, [
    "The result is",
    "8",
]))

start_server(reloader=True)