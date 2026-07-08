from drafter import *


@route
def index() -> Page:
    return Page(
        None,
        [TextBox("input_text", "Enter some text"), Button("Click Me", "next/")],
    )


@route
def next(input_text: int) -> Page:
    return Page(
        None,
        [
            f"You entered: {input_text}\n",
        ],
    )


start_server(None)
