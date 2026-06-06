from bakery import assert_equal
from drafter import route, start_server, Page, Button, add_route


def index():
    return Page(None, ["Hello, World!", Button("Second page", "/second")])


def second():
    return Page(None, ["Welcome to the second page.", Button("Third page", "/third")])


def third():
    return Page(None, ["Welcome to the third page.", Button("Return to start", "/")])


add_route("/", index)
add_route("/second", second)
add_route("/third", third)

start_server()
