from drafter import *

set_website_style("brutal")


@route
def index() -> Page:
    return Page([
        Header("Themed in one line"),
        "Every component dresses to match.\n",
        TextBox("sample", "typed text"),
        "\n",
        Button("A button", "index")
    ])


start_server()
