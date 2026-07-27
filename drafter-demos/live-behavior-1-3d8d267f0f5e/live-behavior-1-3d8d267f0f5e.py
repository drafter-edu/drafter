from drafter import *


@route
def index() -> Page:
    return Page([
        Header("Tweet Composer"),
        "Say it in 50 characters:",
        TextBox("message", "", on_input="count"),
        "\n",
        Output("meter", ["50 characters left"])
    ])


@route
def count(message: str) -> Fragment:
    remaining = 50 - len(message)
    if remaining >= 0:
        report = str(remaining) + " characters left"
    else:
        report = str(-remaining) + " over! Trim it."
    return Fragment([report], target="#meter")


start_server()
