from drafter import route, start_server, Page, Image, Link, set_image_path
from bakery import assert_equal

@route("index")
def index():
    return Page(["Hey look at this image!",
                 Link(Image("https://picsum.photos/200/300"),
                      "https://example.com"),
                Image("victory.png")
             ])


set_image_path("./examples/images")


assert_equal(index(), Page(["Hey look at this image!",
                            Link(Image("https://picsum.photos/200/300"),
                                 "https://example.com"),
                            Image("victory.png")]))

start_server(reloader=True,
             cdn_skulpt="http://localhost:63342/skulpt/dist/skulpt.js",
             cdn_skulpt_std="http://localhost:63342/skulpt/dist/skulpt-stdlib.js",
             cdn_skulpt_drafter="http://localhost:8000/skulpt-drafter.js"
             )