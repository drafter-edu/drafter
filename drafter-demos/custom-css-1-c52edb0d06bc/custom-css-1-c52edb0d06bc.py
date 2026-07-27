from drafter import *

add_website_css(".notice", """
    border: 2px solid darkslateblue;
    border-radius: 8px;
    padding: 12px;
    margin: 8px 0;
    background-color: ghostwhite;
""")


@route
def index() -> Page:
    return Page([
        Header("Announcements"),
        Div("The bake sale moved to Saturday.", classes="notice"),
        Div("Captain the cat has opinions about this.", classes="notice"),
        "Plain text stays plain."
    ])


start_server()
