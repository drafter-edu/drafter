from drafter import *


@route
def index() -> Page:
    return Page([
        bold("Bold.\n"),
        italic("Italic.\n"),
        bold(italic(underline("All three at once.\n"))),
        change_color("Crimson.\n", "crimson"),
        change_background_color(
            change_padding("Padded on lavender.\n", "12px"), "lavender"),
        large_font(change_text_font("Fancy and large.\n", "Georgia"))
    ])


start_server()
