from bakery import assert_equal
from websites import route, start_server, Page, Link

@route
def index():
    return Page([Link("Look at this cool website!", "https://example.com/")])

start_server()