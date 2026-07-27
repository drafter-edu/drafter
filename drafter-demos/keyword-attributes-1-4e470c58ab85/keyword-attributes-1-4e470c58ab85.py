from drafter import *


@route
def index() -> Page:
    return Page([
        Header("Every family at once", style_color="darkslateblue"),
        Button("Styled", "index", style_font_size="20px"),
        "\n",
        TextBox("word", "", placeholder="an HTML attribute at work"),
        "\n",
        Button("Wired", "index", on_mouseenter="react"),
        "\n",
        Output("noticeboard", ["Hover the Wired button."])
    ])


@route
def react() -> Fragment:
    return Fragment(["I felt that."], target="#noticeboard")


start_server()
