from drafter import Link, Page, route, start_server


@route
def index():
    return Page([Link("Look at this cool website!", "https://example.com/")])


start_server()
