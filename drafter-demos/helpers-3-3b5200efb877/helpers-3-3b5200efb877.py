from drafter import *


@route
def index() -> Page:
    return Page([
        Text("Big red button protocol.\n", style_font_size="20px"),
        Button("Do not press", "index",
               style_background_color="crimson",
               style_color="white",
               style_padding="10px")
    ])


start_server()
