from drafter import *

set_website_style("skeleton")


@route
def index() -> Page:
    return Page([
        Header("The skeleton theme"),
        "Ordinary text, a link, and a form, in this theme.\n",
        Link("A link", "index"),
        "\nA field:",
        TextBox("field", "typed text"),
        "\n",
        Button("A button", "index")
    ])


start_server()
