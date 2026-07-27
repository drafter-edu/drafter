from drafter import *

set_website_title("Fortune Teller")
set_website_style("water")


@route
def index() -> Page:
    return Page([
        "The site title and theme were set before the server started.\n",
        Button("Consult the orb", "index")
    ])


start_server()
