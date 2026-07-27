from bakery import assert_equal

from drafter import Page, route, start_server


@route("index")
def index():
    return Page(None, ["Hello, World!"])


assert_equal(index(), Page(None, ["Hello, World!"]))

start_server()
