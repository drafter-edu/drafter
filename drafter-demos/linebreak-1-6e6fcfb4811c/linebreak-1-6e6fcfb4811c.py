from drafter import *


@route
def index() -> Page:
    return Page([
        "These two fields sit on separate lines because of the break:",
        LineBreak(),
        TextBox("first_word"),
        LineBreak(),
        TextBox("second_word"),
        LineBreak(),
        Button("Combine", "index")
    ])


start_server()
