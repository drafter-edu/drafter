from drafter import *

# set_website_style("none")
add_website_css("""
body {
    background-color: lightblue;
    font-size: 20px;
}

.name-box {
    background-color: pink;
    float: right;
}
""")


@route
def index(state: str) -> Page:
    return Page(
        state,
        [
            """<style>
        /* Page specific style */
        .name-box {
            margin: 10px;
        }
        </style>
        """,
            bold("Welcome to the website!"),
            TextBox("Name", "Your name goes here", classes="name-box"),
            Button("Quit", index, style_color="red", style_float="right"),
        ],
        css=".name-box { border: 2px solid black; }",
    )


start_server("")
