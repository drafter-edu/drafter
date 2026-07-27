from drafter import *


@route
def index() -> Page:
    swatch = Picture.new(120, 80, "cadetblue")
    return Page([
        Header("Gallery of One"),
        Image(swatch, alt="A calm blue rectangle"),
        "\nThe same picture, small: ",
        Image(swatch, 30, 20, alt="The same rectangle, tiny")
    ])


start_server()
