from drafter import *

set_website_style("water")


@route
def index() -> Page:
    return Page([
        Header("The water theme"),
        "Ordinary text, a link, and a form, in this theme.\n",
        Link("A link", "index"),
        "\nA field:",
        TextBox("field", "typed text"),
        "\n",
        Button("A button", "index")
    ])


start_server()
