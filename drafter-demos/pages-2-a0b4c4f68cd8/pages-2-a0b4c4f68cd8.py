from drafter import *


def header(title: str) -> list:
    return [
        Header(title),
        Link("Home", "index"),
        " | ",
        Link("About", "about"),
        "\n"
    ]


@route
def index() -> Page:
    return Page(header("My Arcade") + [
        "Pick a destination above."
    ])


@route
def about() -> Page:
    return Page(header("About") + [
        "Built with Drafter."
    ])


start_server()
