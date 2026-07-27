from drafter import *


@route
def index() -> Page:
    return Page([
        "Welcome to the trailhead.\n",
        Link("Hike to the waterfall", "waterfall")
    ])


@route
def waterfall() -> Page:
    return Page([
        "The waterfall roars.\n",
        Link("Continue to the summit", "summit")
    ])


@route
def summit() -> Page:
    return Page([
        "The summit! You can see your house from here.\n",
        Link("Head back down", "index")
    ])


assert_has(index(), Link("Hike to the waterfall", "waterfall"))
assert_has(waterfall(), Link("Continue to the summit", "summit"))
assert_has(summit(), Link("Head back down", "index"))

start_server()
