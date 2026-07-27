from drafter import *


@route
def index() -> Page:
    return Page([
        Header("Three swatches"),
        Picture.new(80, 50, "salmon"),
        Picture.new(80, 50, "lightseagreen"),
        Picture.new(80, 50, "navajowhite")
    ])


start_server()
