from drafter import *


@route
def index() -> Page:
    return Page([
        "The potion is ",
        Span("extremely",
             style_color="crimson",
             style_text_transform="uppercase"),
        " unstable, but the label is ",
        Span("reassuring", id="mood"),
        ".\n",
        Button("Shake it", "shake")
    ])


@route
def shake() -> Fragment:
    return Fragment(["no longer reassuring"], target="#mood")


start_server()
