from drafter import route, start_server, Page, Image, Link, set_image_path
from bakery import assert_equal

from drafter import Image, Link, Page, route, start_server


@route("index")
def index():
    return Page(
        [
            "Hey look at this image!",
            Link(Image("https://picsum.photos/200/300"), "https://example.com"),
            Image("images/soon-128.png"),
        ]
    )


assert_equal(
    index(),
    Page(
        [
            "Hey look at this image!",
            Link(Image("https://picsum.photos/200/300"), "https://example.com"),
            Image("images/soon-128.png"),
        ]
    ),
)

start_server(reloader=True)
