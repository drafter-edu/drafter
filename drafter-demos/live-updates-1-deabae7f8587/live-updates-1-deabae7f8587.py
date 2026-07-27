from drafter import *


@route
def index() -> Page:
    return Page([
        Header("Haiku Drafting Desk"),
        "Write, and watch the count:",
        TextBox("draft", "", on_input="count"),
        "\n",
        Output("counter", ["0 characters so far"])
    ])


@route
def count(draft: str) -> Fragment:
    return Fragment([
        str(len(draft)) + " characters so far"
    ], target="#counter")


start_server()
