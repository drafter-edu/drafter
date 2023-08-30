from bakery import assert_equal
from dataclasses import dataclass
from websites import route, start_server, Page, Textbox, SubmitButton, Text

@route("index")
def index_page() -> Page:
    return Page(None, [
        "What is the first number?",
        Textbox("first", "number"),
        "What is the second number?",
        Textbox("second", "number"),
        SubmitButton("Add", "add_page")
    ])


@route("add_page")
def add_page(first: str, second: str) -> Page:
    result = str(int(first) + int(second))
    return Page(None, [
        "The result is", result
    ])


assert_equal(index_page(), Page(None, [
    "What is the first number?",
    Textbox("first", "number"),
    "What is the second number?",
    Textbox("second", "number"),
    SubmitButton("Add", "add")
]))

assert_equal(add_page("5", "3"), Page(None, [
    "The result is",
    "8",
]))

start_server(reloader=True)