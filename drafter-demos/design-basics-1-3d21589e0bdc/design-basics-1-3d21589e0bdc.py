from drafter import *


@route
def index() -> Page:
    box = Div("Ada is a corgi.")
    box = change_background_color(box, "lavender")
    box = change_padding(box, "20px")
    box = change_border(box, "4px solid slateblue")
    box = change_margin(box, "30px")
    return Page([
        "The line above the box.",
        box,
        "The line below the box."
    ])


start_server()
