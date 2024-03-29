from bakery import assert_equal
from drafter import route, start_server, Page, Image, Link

@route("index")
def index():
    return Page(["Hey look at this image!",
                 Link(Image("https://picsum.photos/200/300"), "https://example.com"),
                Image("victory.png")
             ])


assert_equal(index(), Page(["Hey look at this image!", Link(Image("https://picsum.photos/200/300"), "https://example.com"), Image("victory.png")]))

start_server(reloader=True)