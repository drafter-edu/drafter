from drafter import *


@route
def index() -> Page:
    return Page([
        Header("Mission Control"),
        Row("Callsign:", TextBox("callsign", "Rubber Duck 1")),
        Row(
            Button("Launch", "index"),
            Button("Abort", "index"),
            Button("Snacks", "index")
        ),
        Row(
            Div("LEFT PANEL", style_padding="10px",
                style_background_color="lavender"),
            Div("RIGHT PANEL", style_padding="10px",
                style_background_color="honeydew")
        )
    ])


start_server()
