from drafter import *


@route
def index() -> Page:
    notice = Div(
        bold("Field trip on Friday!\n"),
        "Bring a raincoat and a snack."
    )
    notice = change_border(notice, "2px solid steelblue")
    notice = change_padding(notice, "12px")
    return Page([
        notice,
        large_font(Button("Sounds fun!", "index"))
    ])


start_server()
