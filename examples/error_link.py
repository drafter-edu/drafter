from drafter import Link, Page, route, start_server


@route
def index():
    return Page(
        [Link("Look at my cool background!", "file:///C:/Users/Student/background.png")]
    )


start_server()
