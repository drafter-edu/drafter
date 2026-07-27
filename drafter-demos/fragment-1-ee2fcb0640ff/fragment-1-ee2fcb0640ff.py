from drafter import *


@route
def index() -> Page:
    return Page([
        Header("Shouting Machine"),
        "Type something to shout:",
        TextBox("words", "", on_input="shout"),
        "\n",
        Output("display", ["..."])
    ])


@route
def shout(words: str) -> Fragment:
    return Fragment([words.upper() + "!"], target="#display")


start_server()
