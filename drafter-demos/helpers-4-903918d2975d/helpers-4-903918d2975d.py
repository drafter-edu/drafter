from drafter import *


@route
def index() -> Page:
    return Page([
        bold(change_color("Lives: 3\n", "crimson")),
        Text("Lives: 3\n", style_color="crimson", style_font_weight="bold")
    ])


start_server()
