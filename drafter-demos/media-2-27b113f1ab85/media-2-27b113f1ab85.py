from drafter import *


@route
def index() -> Page:
    original = Picture.new(90, 60, "mediumseagreen")
    original.set_pixel(10, 10, "white")
    return Page([
        Header("The Transformation Gallery"),
        original,
        original.rotate(45),
        original.grayscale(),
        original.resize(45, 30)
    ])


start_server()
