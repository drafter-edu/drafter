from drafter import *


@route
def index() -> Page:
    return Page([
        Header("Box Model"),
        Div(
            "margin 20px, border 4px, padding 24px",
            style_margin="20px",
            style_border="4px solid darkorange",
            style_padding="24px",
            style_background_color="cornsilk"
        ),
        Div(
            "no margin, thin border, no padding",
            style_border="1px solid gray"
        )
    ])


start_server()
