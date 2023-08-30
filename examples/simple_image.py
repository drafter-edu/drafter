from bakery import assert_equal
from websites import route, start_server, Page, Image, Link

@route("index")
def index():
    return Page(["Hey look at this kitten!", Link(Image("http://placekitten.com/200/300"), "https://example.com")])


assert_equal(index(), Page(["Hey look at this kitten!", Link(Image("http://placekitten.com/200/300"), "https://example.com")]))

start_server(reloader=True)