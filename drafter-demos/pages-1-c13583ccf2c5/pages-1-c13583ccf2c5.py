from drafter import *


@route
def index() -> Page:
    return Page([
        "Welcome to the arcade.\n",
        Button("Play a game", "game"),
        Link("Read the rules", "rules")
    ])


@route
def game() -> Page:
    return Page([
        "The game happens here.\n",
        Button("Back to the front", "index")
    ])


@route
def rules() -> Page:
    return Page([
        "Rule 1: have fun.\n",
        Link("Back to the front", "index")
    ])


start_server()
