from drafter import *

add_website_css("h1", "color: darkslateblue; letter-spacing: 2px;")
add_website_css("button", "border-radius: 999px; padding: 8px 16px;")


@route
def index() -> Page:
    return Page([
        Header("Rounded World"),
        Button("Every button", "index"),
        Button("Gets the treatment", "index")
    ])


start_server()
