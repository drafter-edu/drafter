from drafter import *


@route
def index() -> Page:
    face = Picture.new(8, 8, "gold")
    face.set_pixel(2, 2, "black")
    face.set_pixel(5, 2, "black")
    face.set_pixel(1, 5, "black")
    face.set_pixel(2, 6, "black")
    face.set_pixel(3, 6, "black")
    face.set_pixel(4, 6, "black")
    face.set_pixel(5, 6, "black")
    face.set_pixel(6, 5, "black")
    return Page([
        Header("Pixel Painter"),
        face.resize(160, 160)
    ])


start_server()
