from drafter import *

set_website_style("terminal")


@route
def index() -> Page:
    return Page([
        Header("Coin Collector"),
        "Coins so far: 3\n",
        Button("Count again", "index"),
        Link("Start over", "index")
    ])


start_server()
