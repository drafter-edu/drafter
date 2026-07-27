from drafter import *


@route
def index() -> Page:
    return Page([
        bold("Bold.\n"),
        change_color(italic("Crimson italics.\n"), "crimson"),
        change_background_color(
            change_padding("Boxed in.\n", "8px"), "lavender"),
        Button("Reload", "index")
    ])


start_server()
