from drafter import *

set_website_style("sakura")


@route
def index() -> Page:
    return Page([
        Header("Corgi Fan Club"),
        "Members so far: 12\n",
        "Ada approves of this club.\n",
        Button("Reload", "index")
    ])


start_server()
