from drafter import *


@route
def index() -> Page:
    return Page([
        Header("Today's Visitor"),
        Image("https://placehold.co/200x120.png", 200, 120),
        "\nA placeholder guest, 200 by 120."
    ])


start_server()
