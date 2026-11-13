from drafter import *

add_website_css("""
button {
    background-color: lavender;
    border: 2px solid slateblue;
    padding: 8px 16px;
}
""")


@route
def index() -> Page:
    return Page([
        Header("Lavender World"),
        Button("Every button", "index"),
        Button("Gets the rule", "index")
    ])


start_server()
