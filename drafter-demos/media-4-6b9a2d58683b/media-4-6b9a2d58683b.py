from drafter import *


@route
def index() -> Page:
    rings = ""
    colors = ["tomato", "gold", "mediumseagreen", "steelblue"]
    for position in range(len(colors)):
        rings = rings + (
            '<circle cx="' + str(30 + position * 25)
            + '" cy="50" r="20" fill="' + colors[position]
            + '" opacity="0.7" />'
        )
    return Page([
        Header("Ring Toss"),
        SVG(rings, width=300, height=150, viewBox="0 0 130 100")
    ])


start_server()
