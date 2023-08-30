from bakery import assert_equal
from websites import route, start_server, Page, Link

@route("index")
def index():
    return Page(None, [
        "Hello, World!",
        Link("Second page", "second")
    ])


assert_equal(index(), Page(None, ["Hello, World!", Link("Second page", "second")]))

start_server(reloader=True)