from drafter import *


@route
def index() -> Page:
    original = Picture.new(90, 60, "mediumpurple")
    return Page([
        Header("One swatch, transformed"),
        original,
        original.scale(0.5),
        original.rotate(45),
        original.grayscale()
    ])


start_server()
