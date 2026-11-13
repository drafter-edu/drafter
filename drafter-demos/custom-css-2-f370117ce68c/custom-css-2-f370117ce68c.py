from drafter import *

add_website_css("""
.notice {
    border: 2px solid slateblue;
    padding: 12px;
    margin: 8px 0;
}
""")


@route
def index() -> Page:
    return Page([
        Div("The bake sale moved to Saturday.", classes="notice"),
        Div("Captain the cat has opinions.", classes="notice"),
        "Plain text stays plain."
    ])


start_server()
