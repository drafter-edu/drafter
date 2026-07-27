from drafter import *


@route
def index() -> Page:
    return Page([
        Header("Layout"),
        Row(
            Div("left", style_padding="8px",
                style_background_color="mistyrose"),
            Div("middle", style_padding="8px",
                style_background_color="honeydew"),
            Div("right", style_padding="8px",
                style_background_color="aliceblue")
        ),
        "\nA label and its box, on one line:",
        Row("Name:", TextBox("name"))
    ])


start_server()
