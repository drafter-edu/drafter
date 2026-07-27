from drafter import *


@route
def index() -> Page:
    return Page([
        Header("Dashboard", style_color="darkslateblue"),
        Button("Big friendly button", "index",
               style_font_size="24px",
               style_padding="12px",
               style_border_radius="12px"),
        "\n",
        Button("Suspicious button", "index",
               style_background_color="crimson",
               style_color="white")
    ])


start_server()
