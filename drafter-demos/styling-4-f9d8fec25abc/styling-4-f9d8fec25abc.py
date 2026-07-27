from drafter import *

add_website_css(".card", """
    border: 2px solid darkslateblue;
    border-radius: 8px;
    padding: 12px;
    margin: 8px;
    background-color: ghostwhite;
""")


@route
def index() -> Page:
    return Page([
        Header("Cards"),
        Div("The first card.", classes="card"),
        Div("The second card, same rule.", classes="card"),
        Div(bold("A card with helpers inside."), classes="card")
    ])


start_server()
