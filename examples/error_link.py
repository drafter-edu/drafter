from bakery import assert_equal
from drafter import route, start_server, Page, Link

@route
def index():
    return Page([Link("Look at my cool background!", "file:///C:/Users/Student/background.png")])

start_server()